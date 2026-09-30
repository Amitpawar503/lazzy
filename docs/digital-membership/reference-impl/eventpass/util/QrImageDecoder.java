package com.airtel.userprofile.eventpass.util;

import com.airtel.userprofile.eventpass.exception.QrInvalidException;
import com.google.zxing.BarcodeFormat;
import com.google.zxing.BinaryBitmap;
import com.google.zxing.DecodeHintType;
import com.google.zxing.LuminanceSource;
import com.google.zxing.MultiFormatReader;
import com.google.zxing.ReaderException;
import com.google.zxing.Result;
import com.google.zxing.client.j2se.BufferedImageLuminanceSource;
import com.google.zxing.common.GlobalHistogramBinarizer;
import com.google.zxing.common.HybridBinarizer;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;

import javax.imageio.ImageIO;
import java.awt.image.BufferedImage;
import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.util.ArrayList;
import java.util.EnumMap;
import java.util.EnumSet;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.function.Function;

/**
 * Reads a QR image back to its payload — the validation half of the util. Verifies that a rendered
 * image (styled or plain) still decodes to the exact string that was encoded, so callers can prove
 * the round-trip in tests, and the backend can accept a screenshot/upload and recover the token or
 * deeplink it carries.
 *
 * <p>This is <em>structural</em> validation (the image is a readable QR and yields a payload). Trust
 * validation of that payload — signature, TTL, single-active — remains {@code QrTokenService.verify}.
 * A typical agent flow decodes on-device and POSTs the string to API 3; this decoder is the
 * server-side equivalent for uploads and tests.
 *
 * <p><b>Resilience.</b> A marginal image (photographed, compressed, dark-mode screenshot, styled
 * dots) can defeat a single binarizer. {@link #tryDecode(BufferedImage)} therefore runs a ladder of
 * strategies — Hybrid then Global-histogram binarizer, then the inverted luminance for light-on-dark
 * — all with {@code TRY_HARDER}, and returns the first hit. It never throws: unreadable input yields
 * an empty {@link Optional}; {@link #decode(byte[])} is the throwing wrapper for the gate path.
 *
 * <p>Uses ZXing ({@code com.google.zxing:javase} supplies {@link BufferedImageLuminanceSource}).
 */
@Component
@Slf4j
public class QrImageDecoder {

	/** Binarizer ladder, tried in order until one decodes. Cheap: later passes run only on miss. */
	private static final List<Function<LuminanceSource, BinaryBitmap>> BINARIZERS = List.of(
			src -> new BinaryBitmap(new HybridBinarizer(src)),
			src -> new BinaryBitmap(new GlobalHistogramBinarizer(src)));

	private static final Map<DecodeHintType, Object> HINTS = buildHints();

	/**
	 * Decode a QR image to its payload.
	 * @throws QrInvalidException if the bytes are not an image or contain no readable QR.
	 */
	public String decode(byte[] imageBytes) {
		return tryDecode(imageBytes)
				.orElseThrow(() -> new QrInvalidException("No readable QR found in image"));
	}

	/** Decode without throwing; empty when the image is unreadable or holds no QR. */
	public Optional<String> tryDecode(byte[] imageBytes) {
		if (imageBytes == null || imageBytes.length == 0) return Optional.empty();
		BufferedImage image;
		try {
			image = ImageIO.read(new ByteArrayInputStream(imageBytes));
		} catch (IOException e) {
			log.debug("QR decode: bytes are not a readable image", e);
			return Optional.empty();
		}
		return image == null ? Optional.empty() : tryDecode(image);
	}

	/**
	 * Decode a {@link BufferedImage}, walking the resilience ladder. Handy when rendering and reading
	 * in the same process/test.
	 */
	public Optional<String> tryDecode(BufferedImage image) {
		LuminanceSource source = new BufferedImageLuminanceSource(image);
		// Normal orientation first, then inverted (light-on-dark), each across both binarizers.
		for (LuminanceSource src : sources(source)) {
			for (Function<LuminanceSource, BinaryBitmap> binarizer : BINARIZERS) {
				Optional<String> hit = readQuietly(binarizer.apply(src));
				if (hit.isPresent()) return hit;
			}
		}
		return Optional.empty();
	}

	/**
	 * True when {@code imageBytes} decodes to exactly {@code expectedPayload}. Use in tests / health
	 * checks to assert a freshly rendered QR round-trips its data.
	 */
	public boolean matches(byte[] imageBytes, String expectedPayload) {
		return tryDecode(imageBytes).map(d -> d.equals(expectedPayload)).orElse(false);
	}

	// ---- internals ----------------------------------------------------------

	private static List<LuminanceSource> sources(LuminanceSource base) {
		List<LuminanceSource> list = new ArrayList<>(2);
		list.add(base);
		list.add(base.invert()); // dark-mode screenshots / inverted prints
		return list;
	}

	/** A single reader pass; MultiFormatReader is not thread-safe, so use a fresh one each call. */
	private static Optional<String> readQuietly(BinaryBitmap bitmap) {
		try {
			Result result = new MultiFormatReader().decode(bitmap, HINTS);
			return Optional.ofNullable(result.getText());
		} catch (ReaderException e) {
			return Optional.empty(); // NotFound / Checksum / Format → try the next strategy
		}
	}

	private static Map<DecodeHintType, Object> buildHints() {
		Map<DecodeHintType, Object> hints = new EnumMap<>(DecodeHintType.class);
		hints.put(DecodeHintType.TRY_HARDER, Boolean.TRUE);
		hints.put(DecodeHintType.POSSIBLE_FORMATS, EnumSet.of(BarcodeFormat.QR_CODE));
		hints.put(DecodeHintType.CHARACTER_SET, "UTF-8");
		return hints;
	}
}
