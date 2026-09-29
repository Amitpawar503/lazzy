package com.airtel.userprofile.eventpass.util;

import com.airtel.userprofile.eventpass.config.QrStyleProperties;
import com.airtel.userprofile.eventpass.config.QrStyleProperties.ModuleShape;
import com.google.zxing.EncodeHintType;
import com.google.zxing.WriterException;
import com.google.zxing.common.BitMatrix;
import com.google.zxing.qrcode.QRCodeWriter;
import com.google.zxing.qrcode.decoder.ErrorCorrectionLevel;
import lombok.Builder;
import lombok.Value;
import lombok.extern.slf4j.Slf4j;
import org.springframework.core.io.DefaultResourceLoader;
import org.springframework.core.io.Resource;
import org.springframework.core.io.ResourceLoader;
import org.springframework.stereotype.Component;
import org.springframework.util.StringUtils;

import javax.imageio.ImageIO;
import java.awt.AlphaComposite;
import java.awt.Color;
import java.awt.Font;
import java.awt.FontMetrics;
import java.awt.Graphics2D;
import java.awt.MultipleGradientPaint.CycleMethod;
import java.awt.RadialGradientPaint;
import java.awt.RenderingHints;
import java.awt.geom.Ellipse2D;
import java.awt.geom.Point2D;
import java.awt.geom.RoundRectangle2D;
import java.awt.image.BufferedImage;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.Base64;
import java.util.EnumMap;
import java.util.Map;

/**
 * Renders the styled circular membership QR — dotted modules under a radial gradient, rounded finder
 * "eyes", and a centre badge carrying a logo or changeable text — from any payload string
 * (signed token, deeplink, or opaque info). What a camera reads back is exactly the payload; the
 * styling never touches the encoded bits.
 *
 * <p>Stateless and thread-safe: all per-call inputs arrive through {@link Style}. Resolve a {@link
 * Style} from {@link QrStyleProperties} once (optionally layering request overrides), then call
 * {@link #renderPng} / {@link #renderDataUri} as often as needed.
 *
 * <p>Error correction defaults to level H so the covered centre still decodes. Encoding uses
 * ZXing ({@code com.google.zxing:core} + {@code javase} for decode); see the platform-wiring note in
 * the LLD for the {@code pom.xml} entries.
 */
@Component
@Slf4j
public class CircularQrGenerator {

	private static final ResourceLoader RESOURCE_LOADER = new DefaultResourceLoader();

	/**
	 * Immutable, fully-resolved render style. Build from config with {@link #from(QrStyleProperties)},
	 * then layer any non-null per-request overrides yourself before rendering.
	 */
	@Value
	@Builder(toBuilder = true)
	public static class Style {
		int size;
		int quietZoneModules;
		Color background;              // null ⇒ transparent
		ModuleShape moduleShape;
		double moduleSizeRatio;
		boolean gradientEnabled;
		Color gradientInner;
		Color gradientOuter;
		Color foreground;
		boolean styledFinder;
		double finderCornerRatio;
		Color finderColor;
		boolean centerBadgeEnabled;
		double centerBadgeRatio;
		Color centerBadgeInner;
		Color centerBadgeOuter;
		boolean centerRingEnabled;
		Color centerRingColor;
		double centerRingRatio;
		String centerText;
		Color centerTextColor;
		String centerTextFont;
		String centerLogoResource;
		ErrorCorrectionLevel errorCorrection;

		/** Resolve a Style straight from configured defaults. */
		public static Style from(QrStyleProperties p) {
			return Style.builder()
					.size(p.getSize())
					.quietZoneModules(p.getQuietZoneModules())
					.background(parseColor(p.getBackgroundColor()))
					.moduleShape(p.getModuleShape())
					.moduleSizeRatio(clamp(p.getModuleSizeRatio(), 0.4, 1.0))
					.gradientEnabled(p.isGradientEnabled())
					.gradientInner(parseColor(p.getGradientInnerColor()))
					.gradientOuter(parseColor(p.getGradientOuterColor()))
					.foreground(parseColor(p.getForegroundColor()))
					.styledFinder(p.isStyledFinder())
					.finderCornerRatio(clamp(p.getFinderCornerRatio(), 0.0, 0.5))
					.finderColor(parseColor(p.getFinderColor()))
					.centerBadgeEnabled(p.isCenterBadgeEnabled())
					.centerBadgeRatio(clamp(p.getCenterBadgeRatio(), 0.0, 0.32))
					.centerBadgeInner(parseColor(p.getCenterBadgeInnerColor()))
					.centerBadgeOuter(parseColor(p.getCenterBadgeOuterColor()))
					.centerRingEnabled(p.isCenterRingEnabled())
					.centerRingColor(parseColor(p.getCenterRingColor()))
					.centerRingRatio(clamp(p.getCenterRingRatio(), 0.0, 0.15))
					.centerText(p.getCenterText())
					.centerTextColor(parseColor(p.getCenterTextColor()))
					.centerTextFont(p.getCenterTextFont())
					.centerLogoResource(p.getCenterLogoResource())
					.errorCorrection(parseEc(p.getErrorCorrection()))
					.build();
		}
	}

	/** Render to a {@code data:image/png;base64,…} URI, ready for an {@code <img src>}. */
	public String renderDataUri(String data, Style style) {
		byte[] png = renderPng(data, style);
		return "data:image/png;base64," + Base64.getEncoder().encodeToString(png);
	}

	/** Render to PNG bytes. */
	public byte[] renderPng(String data, Style style) {
		BufferedImage img = render(data, style);
		try (ByteArrayOutputStream out = new ByteArrayOutputStream()) {
			ImageIO.write(img, "png", out);
			return out.toByteArray();
		} catch (IOException e) {
			throw new IllegalStateException("Failed to encode QR PNG", e);
		}
	}

	/** Render to a {@link BufferedImage}. */
	public BufferedImage render(String data, Style style) {
		if (!StringUtils.hasText(data)) {
			throw new IllegalArgumentException("QR payload must not be blank");
		}
		BitMatrix matrix = encodeBareMatrix(data, style.getErrorCorrection());
		int modules = matrix.getWidth(); // square, quiet zone excluded

		int size = style.getSize();
		int dims = modules + 2 * style.getQuietZoneModules();
		int cell = Math.max(1, size / dims);
		int drawn = cell * dims;
		int origin = (size - drawn) / 2; // centre the code in the canvas
		int qz = style.getQuietZoneModules();

		BufferedImage img = new BufferedImage(size, size, BufferedImage.TYPE_INT_ARGB);
		Graphics2D g = img.createGraphics();
		try {
			g.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
			g.setRenderingHint(RenderingHints.KEY_RENDERING, RenderingHints.VALUE_RENDER_QUALITY);
			g.setRenderingHint(RenderingHints.KEY_TEXT_ANTIALIASING, RenderingHints.VALUE_TEXT_ANTIALIAS_ON);

			paintBackground(g, style, size);

			double cx = size / 2.0;
			double cy = size / 2.0;
			// Modules whose centre falls inside this radius are cleared for the badge.
			double badgeClearR = style.isCenterBadgeEnabled()
					? size * (style.getCenterBadgeRatio() / 2.0 + style.getCenterRingRatio())
					: -1;

			g.setPaint(dataPaint(style, origin + qz * cell, drawn - 2 * qz * cell));

			for (int my = 0; my < modules; my++) {
				for (int mx = 0; mx < modules; mx++) {
					if (!matrix.get(mx, my)) continue;
					if (style.isStyledFinder() && inFinder(mx, my, modules)) continue; // drawn separately
					double px = origin + (qz + mx) * cell;
					double py = origin + (qz + my) * cell;
					if (badgeClearR > 0) {
						double mcx = px + cell / 2.0, mcy = py + cell / 2.0;
						if (Math.hypot(mcx - cx, mcy - cy) <= badgeClearR) continue; // under badge
					}
					g.fill(moduleShape(style, px, py, cell));
				}
			}

			if (style.isStyledFinder()) {
				int f = 7 * cell;
				drawFinder(g, style, origin + qz * cell, origin + qz * cell, f);
				drawFinder(g, style, origin + (qz + modules - 7) * cell, origin + qz * cell, f);
				drawFinder(g, style, origin + qz * cell, origin + (qz + modules - 7) * cell, f);
			}

			if (style.isCenterBadgeEnabled()) {
				drawCenterBadge(g, style, cx, cy);
			}
		} finally {
			g.dispose();
		}
		return img;
	}

	// ---- encoding -----------------------------------------------------------

	private BitMatrix encodeBareMatrix(String data, ErrorCorrectionLevel ec) {
		Map<EncodeHintType, Object> hints = new EnumMap<>(EncodeHintType.class);
		hints.put(EncodeHintType.ERROR_CORRECTION, ec);
		hints.put(EncodeHintType.CHARACTER_SET, StandardCharsets.UTF_8.name());
		hints.put(EncodeHintType.MARGIN, 0); // we add the quiet zone ourselves
		try {
			// width/height==0 asks ZXing for the natural, one-pixel-per-module matrix.
			return new QRCodeWriter().encode(data, com.google.zxing.BarcodeFormat.QR_CODE, 0, 0, hints);
		} catch (WriterException e) {
			throw new IllegalArgumentException("Cannot encode QR payload (too long?)", e);
		}
	}

	// ---- painting helpers ---------------------------------------------------

	private void paintBackground(Graphics2D g, Style style, int size) {
		if (style.getBackground() == null) {
			g.setComposite(AlphaComposite.Clear);
			g.fillRect(0, 0, size, size);
			g.setComposite(AlphaComposite.SrcOver);
		} else {
			g.setColor(style.getBackground());
			g.fillRect(0, 0, size, size);
		}
	}

	/** Radial gradient (inner→outer) across the code, or a flat colour when disabled. */
	private java.awt.Paint dataPaint(Style style, int codeOrigin, int codeSpan) {
		if (!style.isGradientEnabled()) return style.getForeground();
		float cx = codeOrigin + codeSpan / 2f;
		float cy = cx; // square
		float radius = (float) (codeSpan / 2f * Math.sqrt(2)); // reach the corners
		return new RadialGradientPaint(
				new Point2D.Float(cx, cy), radius,
				new float[]{0f, 1f},
				new Color[]{style.getGradientInner(), style.getGradientOuter()},
				CycleMethod.NO_CYCLE);
	}

	private java.awt.Shape moduleShape(Style style, double px, double py, int cell) {
		double d = cell * style.getModuleSizeRatio();
		double off = (cell - d) / 2.0;
		switch (style.getModuleShape()) {
			case SQUARE:
				return new RoundRectangle2D.Double(px, py, cell, cell, 0, 0);
			case ROUNDED:
				return new RoundRectangle2D.Double(px + off, py + off, d, d, d * 0.5, d * 0.5);
			case DOTS:
			default:
				return new Ellipse2D.Double(px + off, py + off, d, d);
		}
	}

	/** Concentric rounded finder: outer ring (7) → hole (5) → solid eye (3). */
	private void drawFinder(Graphics2D g, Style style, double x, double y, int box) {
		double arc = box * style.getFinderCornerRatio();
		double unit = box / 7.0;
		g.setColor(style.getFinderColor());
		g.fill(new RoundRectangle2D.Double(x, y, box, box, arc, arc));
		// punch a 5x5 hole using the background (transparent-safe)
		double hole = unit * 5, hx = x + unit, hy = y + unit, harc = hole * (arc / box);
		java.awt.Composite prev = g.getComposite();
		if (style.getBackground() == null) {
			g.setComposite(AlphaComposite.Clear);
			g.fill(new RoundRectangle2D.Double(hx, hy, hole, hole, harc, harc));
			g.setComposite(prev);
		} else {
			g.setColor(style.getBackground());
			g.fill(new RoundRectangle2D.Double(hx, hy, hole, hole, harc, harc));
		}
		double eye = unit * 3, ex = x + unit * 2, ey = y + unit * 2, earc = eye * (arc / box);
		g.setColor(style.getFinderColor());
		g.fill(new RoundRectangle2D.Double(ex, ey, eye, eye, earc, earc));
	}

	private void drawCenterBadge(Graphics2D g, Style style, double cx, double cy) {
		double badgeR = style.getSize() * style.getCenterBadgeRatio() / 2.0;
		if (style.isCenterRingEnabled()) {
			double ringR = badgeR + style.getSize() * style.getCenterRingRatio();
			g.setColor(style.getCenterRingColor());
			g.fill(new Ellipse2D.Double(cx - ringR, cy - ringR, ringR * 2, ringR * 2));
		}
		// gradient disc
		g.setPaint(new RadialGradientPaint(
				new Point2D.Double(cx - badgeR * 0.25, cy - badgeR * 0.25), (float) (badgeR * 1.4),
				new float[]{0f, 1f},
				new Color[]{style.getCenterBadgeInner(), style.getCenterBadgeOuter()},
				CycleMethod.NO_CYCLE));
		g.fill(new Ellipse2D.Double(cx - badgeR, cy - badgeR, badgeR * 2, badgeR * 2));

		double contentTop = drawCenterLogo(g, style, cx, cy, badgeR);
		drawCenterText(g, style, cx, cy, badgeR, contentTop);
	}

	/** @return y where text should start (below the logo), or cy for text-only badges. */
	private double drawCenterLogo(Graphics2D g, Style style, double cx, double cy, double badgeR) {
		if (!StringUtils.hasText(style.getCenterLogoResource())) return Double.NaN;
		try {
			Resource res = RESOURCE_LOADER.getResource(style.getCenterLogoResource());
			try (InputStream in = res.getInputStream()) {
				BufferedImage logo = ImageIO.read(in);
				if (logo == null) return Double.NaN;
				double max = badgeR * (StringUtils.hasText(style.getCenterText()) ? 0.9 : 1.3);
				double scale = max / Math.max(logo.getWidth(), logo.getHeight());
				double w = logo.getWidth() * scale, h = logo.getHeight() * scale;
				boolean textToo = StringUtils.hasText(style.getCenterText());
				double top = textToo ? cy - badgeR * 0.72 : cy - h / 2;
				g.drawImage(logo, (int) Math.round(cx - w / 2), (int) Math.round(top),
						(int) Math.round(w), (int) Math.round(h), null);
				return top + h + badgeR * 0.08;
			}
		} catch (IOException e) {
			log.warn("Centre logo '{}' not loadable, falling back to text", style.getCenterLogoResource(), e);
			return Double.NaN;
		}
	}

	private void drawCenterText(Graphics2D g, Style style, double cx, double cy, double badgeR, double startY) {
		if (!StringUtils.hasText(style.getCenterText())) return;
		String[] lines = style.getCenterText().split("\\r?\\n");
		g.setColor(style.getCenterTextColor());

		// First line is the brand line (largest); the rest share a smaller size.
		double innerW = badgeR * 1.5;
		double brandSize = badgeR * 0.42;
		double restSize = badgeR * 0.26;

		double totalH = 0;
		double[] heights = new double[lines.length];
		for (int i = 0; i < lines.length; i++) {
			Font f = fitFont(g, style.getCenterTextFont(), i == 0 ? Font.BOLD : Font.BOLD,
					i == 0 ? brandSize : restSize, lines[i], innerW);
			heights[i] = f.getSize2D() * 1.12;
			totalH += heights[i];
		}
		double y = Double.isNaN(startY) ? cy - totalH / 2 : startY;
		for (int i = 0; i < lines.length; i++) {
			Font f = fitFont(g, style.getCenterTextFont(), Font.BOLD,
					i == 0 ? brandSize : restSize, lines[i], innerW);
			g.setFont(f);
			FontMetrics fm = g.getFontMetrics();
			int tx = (int) Math.round(cx - fm.stringWidth(lines[i]) / 2.0);
			int ty = (int) Math.round(y + fm.getAscent());
			g.drawString(lines[i], tx, ty);
			y += heights[i];
		}
	}

	/** Shrink the font until the line fits {@code maxWidth}. */
	private Font fitFont(Graphics2D g, String family, int weightStyle, double px, String text, double maxWidth) {
		float sz = (float) px;
		Font f = new Font(family, weightStyle, Math.max(1, Math.round(sz)));
		while (sz > 6) {
			f = new Font(family, weightStyle, Math.round(sz));
			if (g.getFontMetrics(f).stringWidth(text) <= maxWidth) break;
			sz -= 1f;
		}
		return f;
	}

	// ---- finder geometry & parsing -----------------------------------------

	private static boolean inFinder(int mx, int my, int modules) {
		return (mx < 7 && my < 7)                       // top-left
				|| (mx >= modules - 7 && my < 7)        // top-right
				|| (mx < 7 && my >= modules - 7);       // bottom-left
	}

	/** Parse {@code #RRGGBB} / {@code #AARRGGBB} / {@code "transparent"} (→ null). Public for overrides. */
	public static Color parseColor(String hex) {
		if (!StringUtils.hasText(hex) || "transparent".equalsIgnoreCase(hex.trim())) return null;
		String h = hex.trim();
		if (h.startsWith("#")) h = h.substring(1);
		try {
			if (h.length() == 6) {
				return new Color(Integer.parseInt(h, 16));
			} else if (h.length() == 8) { // AARRGGBB
				long v = Long.parseLong(h, 16);
				return new Color((int) (v >> 16) & 0xFF, (int) (v >> 8) & 0xFF, (int) v & 0xFF, (int) (v >> 24) & 0xFF);
			}
		} catch (NumberFormatException ignored) {
			// fall through
		}
		throw new IllegalArgumentException("Invalid colour: " + hex + " (use #RRGGBB, #AARRGGBB, or 'transparent')");
	}

	private static ErrorCorrectionLevel parseEc(String level) {
		if (!StringUtils.hasText(level)) return ErrorCorrectionLevel.H;
		switch (level.trim().toUpperCase()) {
			case "L": return ErrorCorrectionLevel.L;
			case "M": return ErrorCorrectionLevel.M;
			case "Q": return ErrorCorrectionLevel.Q;
			case "H":
			default:  return ErrorCorrectionLevel.H;
		}
	}

	private static double clamp(double v, double lo, double hi) {
		return Math.max(lo, Math.min(hi, v));
	}
}
