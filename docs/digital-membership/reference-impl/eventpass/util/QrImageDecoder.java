package com.airtel.userprofile.eventpass.util;

import com.airtel.userprofile.eventpass.exception.QrInvalidException;
import com.google.zxing.BarcodeFormat;
import com.google.zxing.BinaryBitmap;
import com.google.zxing.DecodeHintType;
import com.google.zxing.MultiFormatReader;
import com.google.zxing.NotFoundException;
import com.google.zxing.Result;
import com.google.zxing.client.j2se.BufferedImageLuminanceSource;
import com.google.zxing.common.HybridBinarizer;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;

import javax.imageio.ImageIO;
import java.awt.image.BufferedImage;
import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.util.EnumMap;
import java.util.EnumSet;
import java.util.Map;
import java.util.Optional;

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
 * <p>Uses ZXing ({@code com.google.zxing:javase} supplies {@link BufferedImageLuminanceSource}).
 */
@Component
@Slf4j
public class QrImageDecoder {

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
		if (image == null) return Optional.empty();
		return tryDecode(image);
	}

	/** Decode a {@link BufferedImage} (handy when rendering and reading in the same process/test). */
	public Optional<String> tryDecode(BufferedImage image) {
		BinaryBitmap bitmap = new BinaryBitmap(
				new HybridBinarizer(new BufferedImageLuminanceSource(image)));
		Map<DecodeHintType, Object> hints = new EnumMap<>(DecodeHintType.class);
		hints.put(DecodeHintType.TRY_HARDER, Boolean.TRUE);
		hints.put(DecodeHintType.POSSIBLE_FORMATS, EnumSet.of(BarcodeFormat.QR_CODE));
		hints.put(DecodeHintType.CHARACTER_SET, "UTF-8");
		try {
			Result result = new MultiFormatReader().decode(bitmap, hints);
			return Optional.ofNullable(result.getText());
		} catch (NotFoundException e) {
			return Optional.empty();
		}
	}

	/**
	 * True when {@code imageBytes} decodes to exactly {@code expectedPayload}. Use in tests / health
	 * checks to assert a freshly rendered QR round-trips its data.
	 */
	public boolean matches(byte[] imageBytes, String expectedPayload) {
		return tryDecode(imageBytes).map(d -> d.equals(expectedPayload)).orElse(false);
	}
}
