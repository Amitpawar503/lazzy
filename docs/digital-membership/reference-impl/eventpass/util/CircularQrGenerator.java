package com.airtel.userprofile.eventpass.util;

import com.airtel.userprofile.eventpass.config.QrStyleProperties;
import com.airtel.userprofile.eventpass.config.QrStyleProperties.ModuleShape;
import com.google.zxing.BarcodeFormat;
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
import java.awt.Composite;
import java.awt.Font;
import java.awt.FontMetrics;
import java.awt.Graphics2D;
import java.awt.MultipleGradientPaint.CycleMethod;
import java.awt.Paint;
import java.awt.RadialGradientPaint;
import java.awt.RenderingHints;
import java.awt.Shape;
import java.awt.geom.Ellipse2D;
import java.awt.geom.Point2D;
import java.awt.geom.Rectangle2D;
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
 * <p>Stateless and thread-safe: every per-call input arrives through {@link Style}. Resolve a {@link
 * Style} from {@link QrStyleProperties} with {@link Style#from}, then call {@link #renderPng} /
 * {@link #renderDataUri} as often as needed. The renderer knows nothing about web DTOs or Spring
 * config binding — layering per-request overrides onto a {@link Style} is the caller's concern.
 *
 * <p>Encoding uses ZXing ({@code com.google.zxing:core}); decoding lives in {@link QrImageDecoder}
 * ({@code :javase}). See the LLD §5A platform-wiring note for the {@code pom.xml} entries.
 */
@Component
@Slf4j
public class CircularQrGenerator {

	private static final ResourceLoader RESOURCE_LOADER = new DefaultResourceLoader();

	/** Modules per side of a QR finder pattern (the three corner "eyes"). */
	private static final int FINDER_MODULES = 7;

	// Centre-text layout, all relative to the badge radius so they scale with the badge.
	private static final double BRAND_TEXT_RATIO = 0.42; // first (brand) line
	private static final double LINE_TEXT_RATIO = 0.26;  // remaining lines
	private static final double LINE_SPACING = 1.12;
	private static final double TEXT_INNER_WIDTH_RATIO = 1.5;
	private static final double BADGE_HIGHLIGHT_SPREAD = 1.4; // radial-highlight reach vs badge radius
	private static final float MIN_FONT_PX = 6f;

	/**
	 * Immutable, fully-resolved render style. Build from config with {@link #from(QrStyleProperties)}
	 * and layer any non-null per-request overrides via {@link #toBuilder()} before rendering.
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
		boolean resilient;

		/** Resolve a Style straight from configured defaults (parsing + clamping applied here). */
		public static Style from(QrStyleProperties p) {
			return Style.builder()
					.size(p.getSize())
					.quietZoneModules(p.getQuietZoneModules())
					.background(HexColors.parse(p.getBackgroundColor()))
					.moduleShape(p.getModuleShape())
					.moduleSizeRatio(clamp(p.getModuleSizeRatio(), 0.4, 1.0))
					.gradientEnabled(p.isGradientEnabled())
					.gradientInner(HexColors.parse(p.getGradientInnerColor()))
					.gradientOuter(HexColors.parse(p.getGradientOuterColor()))
					.foreground(HexColors.parse(p.getForegroundColor()))
					.styledFinder(p.isStyledFinder())
					.finderCornerRatio(clamp(p.getFinderCornerRatio(), 0.0, 0.5))
					.finderColor(HexColors.parse(p.getFinderColor()))
					.centerBadgeEnabled(p.isCenterBadgeEnabled())
					.centerBadgeRatio(clamp(p.getCenterBadgeRatio(), 0.0, 0.32))
					.centerBadgeInner(HexColors.parse(p.getCenterBadgeInnerColor()))
					.centerBadgeOuter(HexColors.parse(p.getCenterBadgeOuterColor()))
					.centerRingEnabled(p.isCenterRingEnabled())
					.centerRingColor(HexColors.parse(p.getCenterRingColor()))
					.centerRingRatio(clamp(p.getCenterRingRatio(), 0.0, 0.15))
					.centerText(p.getCenterText())
					.centerTextColor(HexColors.parse(p.getCenterTextColor()))
					.centerTextFont(p.getCenterTextFont())
					.centerLogoResource(p.getCenterLogoResource())
					.errorCorrection(parseEc(p.getErrorCorrection()))
					.resilient(p.isResilientRender())
					.build();
		}

		/**
		 * A guaranteed-scannable variant of this style: plain black square modules on opaque white,
		 * no gradient, styled finder, or centre overlay. Keeps size, quiet zone and EC level so the
		 * fallback encodes the same payload at the same dimensions.
		 */
		Style toPlain() {
			return toBuilder()
					.background(Color.WHITE)
					.foreground(Color.BLACK)
					.gradientEnabled(false)
					.moduleShape(ModuleShape.SQUARE)
					.styledFinder(false)
					.centerBadgeEnabled(false)
					.centerRingEnabled(false)
					.build();
		}
	}

	/** Immutable pixel layout of the code on the canvas — the single source of module geometry. */
	@Value
	private static class Grid {
		BitMatrix matrix;
		int modules;      // modules per side (quiet zone excluded)
		int cell;         // px per module
		int origin;       // px offset of the whole (code + quiet zone) block
		int quietZone;    // modules

		double x(int col) { return origin + (quietZone + col) * (double) cell; }
		double y(int row) { return origin + (quietZone + row) * (double) cell; }
		double codeOrigin() { return origin + quietZone * (double) cell; }
		double codeSpan() { return modules * (double) cell; }
	}

	// ---- public API ---------------------------------------------------------

	/** Render to a {@code data:image/png;base64,…} URI, ready for an {@code <img src>}. */
	public String renderDataUri(String data, Style style) {
		return "data:image/png;base64," + Base64.getEncoder().encodeToString(renderPng(data, style));
	}

	/** Render to PNG bytes. */
	public byte[] renderPng(String data, Style style) {
		try (ByteArrayOutputStream out = new ByteArrayOutputStream()) {
			ImageIO.write(render(data, style), "png", out);
			return out.toByteArray();
		} catch (IOException e) {
			throw new IllegalStateException("Failed to encode QR PNG", e);
		}
	}

	/**
	 * Render to a {@link BufferedImage}. Encoding the payload is the only hard failure (an
	 * un-encodable/too-long payload throws); if the <em>styling</em> then fails and the style is
	 * {@link Style#isResilient() resilient}, a plain black-on-white QR of the same matrix is returned
	 * so a valid payload always yields a scannable code.
	 */
	public BufferedImage render(String data, Style style) {
		Grid grid = layout(data, style); // encode: bad payload → IllegalArgumentException (propagates)
		try {
			return draw(grid, style);
		} catch (RuntimeException e) {
			if (!style.isResilient()) throw e;
			log.warn("Styled QR render failed for a valid payload; falling back to a plain QR", e);
			return draw(grid, style.toPlain());
		}
	}

	/** Paint the (already-encoded) grid with the given style onto a fresh canvas. */
	private BufferedImage draw(Grid grid, Style style) {
		BufferedImage img = new BufferedImage(style.getSize(), style.getSize(), BufferedImage.TYPE_INT_ARGB);
		Graphics2D g = img.createGraphics();
		try {
			g.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
			g.setRenderingHint(RenderingHints.KEY_RENDERING, RenderingHints.VALUE_RENDER_QUALITY);
			g.setRenderingHint(RenderingHints.KEY_TEXT_ANTIALIASING, RenderingHints.VALUE_TEXT_ANTIALIAS_ON);

			fillOrClear(g, new Rectangle2D.Double(0, 0, style.getSize(), style.getSize()), style.getBackground());
			drawModules(g, style, grid);
			if (style.isStyledFinder()) {
				drawFinders(g, style, grid);
			}
			if (style.isCenterBadgeEnabled()) {
				drawCenterBadge(g, style, style.getSize() / 2.0, style.getSize() / 2.0);
			}
		} finally {
			g.dispose();
		}
		return img;
	}

	// ---- encoding & layout --------------------------------------------------

	private Grid layout(String data, Style style) {
		if (!StringUtils.hasText(data)) {
			throw new IllegalArgumentException("QR payload must not be blank");
		}
		BitMatrix matrix = encodeBareMatrix(data, style.getErrorCorrection());
		int modules = matrix.getWidth(); // square, quiet zone excluded
		int dims = modules + 2 * style.getQuietZoneModules();
		int cell = Math.max(1, style.getSize() / dims);
		int origin = (style.getSize() - cell * dims) / 2; // centre the block
		return new Grid(matrix, modules, cell, origin, style.getQuietZoneModules());
	}

	private BitMatrix encodeBareMatrix(String data, ErrorCorrectionLevel ec) {
		Map<EncodeHintType, Object> hints = new EnumMap<>(EncodeHintType.class);
		hints.put(EncodeHintType.ERROR_CORRECTION, ec);
		hints.put(EncodeHintType.CHARACTER_SET, StandardCharsets.UTF_8.name());
		hints.put(EncodeHintType.MARGIN, 0); // we add the quiet zone ourselves
		try {
			// width/height==0 asks ZXing for the natural, one-pixel-per-module matrix.
			return new QRCodeWriter().encode(data, BarcodeFormat.QR_CODE, 0, 0, hints);
		} catch (WriterException e) {
			throw new IllegalArgumentException("Cannot encode QR payload (too long?)", e);
		}
	}

	// ---- modules ------------------------------------------------------------

	private void drawModules(Graphics2D g, Style style, Grid grid) {
		double center = style.getSize() / 2.0;
		double badgeClearR = style.isCenterBadgeEnabled()
				? style.getSize() * (style.getCenterBadgeRatio() / 2.0 + style.getCenterRingRatio())
				: -1;
		g.setPaint(dataPaint(style, grid));

		for (int row = 0; row < grid.getModules(); row++) {
			for (int col = 0; col < grid.getModules(); col++) {
				if (!grid.getMatrix().get(col, row)) continue;
				if (style.isStyledFinder() && inFinder(col, row, grid.getModules())) continue; // drawn separately
				double px = grid.x(col);
				double py = grid.y(row);
				if (badgeClearR > 0
						&& Math.hypot(px + grid.getCell() / 2.0 - center, py + grid.getCell() / 2.0 - center) <= badgeClearR) {
					continue; // under the centre badge
				}
				g.fill(moduleShape(style, px, py, grid.getCell()));
			}
		}
	}

	/** Radial gradient (inner→outer) across the code, or a flat colour when disabled. */
	private Paint dataPaint(Style style, Grid grid) {
		if (!style.isGradientEnabled()) return style.getForeground();
		double c = grid.codeOrigin() + grid.codeSpan() / 2.0;
		double radius = grid.codeSpan() / 2.0 * Math.sqrt(2); // reach the corners
		return radial(c, c, radius, style.getGradientInner(), style.getGradientOuter());
	}

	private Shape moduleShape(Style style, double px, double py, int cell) {
		double d = cell * style.getModuleSizeRatio();
		double off = (cell - d) / 2.0;
		switch (style.getModuleShape()) {
			case SQUARE:
				return new Rectangle2D.Double(px, py, cell, cell);
			case ROUNDED:
				return new RoundRectangle2D.Double(px + off, py + off, d, d, d * 0.5, d * 0.5);
			case DOTS:
			default:
				return new Ellipse2D.Double(px + off, py + off, d, d);
		}
	}

	// ---- finders ------------------------------------------------------------

	private void drawFinders(Graphics2D g, Style style, Grid grid) {
		int box = FINDER_MODULES * grid.getCell();
		int last = grid.getModules() - FINDER_MODULES;
		int[][] corners = {{0, 0}, {last, 0}, {0, last}}; // top-left, top-right, bottom-left
		for (int[] c : corners) {
			drawFinder(g, style, grid.x(c[0]), grid.y(c[1]), box);
		}
	}

	/** Concentric rounded finder: outer ring (7 modules) → hole (5) → solid eye (3). */
	private void drawFinder(Graphics2D g, Style style, double x, double y, int box) {
		double arc = box * style.getFinderCornerRatio();
		double unit = box / (double) FINDER_MODULES;
		double cornerRatio = arc / box;

		g.setColor(style.getFinderColor());
		g.fill(roundBox(x, y, box, arc));

		double hole = unit * 5;
		fillOrClear(g, roundBox(x + unit, y + unit, hole, hole * cornerRatio), style.getBackground());

		double eye = unit * 3;
		g.setColor(style.getFinderColor());
		g.fill(roundBox(x + unit * 2, y + unit * 2, eye, eye * cornerRatio));
	}

	private static RoundRectangle2D.Double roundBox(double x, double y, double size, double arc) {
		return new RoundRectangle2D.Double(x, y, size, size, arc, arc);
	}

	private static boolean inFinder(int col, int row, int modules) {
		return (col < FINDER_MODULES && row < FINDER_MODULES)                       // top-left
				|| (col >= modules - FINDER_MODULES && row < FINDER_MODULES)        // top-right
				|| (col < FINDER_MODULES && row >= modules - FINDER_MODULES);       // bottom-left
	}

	// ---- centre badge -------------------------------------------------------

	private void drawCenterBadge(Graphics2D g, Style style, double cx, double cy) {
		double badgeR = style.getSize() * style.getCenterBadgeRatio() / 2.0;
		if (style.isCenterRingEnabled()) {
			double ringR = badgeR + style.getSize() * style.getCenterRingRatio();
			g.setColor(style.getCenterRingColor());
			g.fill(disc(cx, cy, ringR));
		}
		// gradient disc, highlight biased to the upper-left for a glossy look
		g.setPaint(radial(cx - badgeR * 0.25, cy - badgeR * 0.25, badgeR * BADGE_HIGHLIGHT_SPREAD,
				style.getCenterBadgeInner(), style.getCenterBadgeOuter()));
		g.fill(disc(cx, cy, badgeR));

		double contentTop = drawCenterLogo(g, style, cx, cy, badgeR);
		drawCenterText(g, style, cx, cy, badgeR, contentTop);
	}

	/** @return y where text should start (below the logo), or NaN when there is no logo. */
	private double drawCenterLogo(Graphics2D g, Style style, double cx, double cy, double badgeR) {
		if (!StringUtils.hasText(style.getCenterLogoResource())) return Double.NaN;
		boolean textToo = StringUtils.hasText(style.getCenterText());
		try {
			Resource res = RESOURCE_LOADER.getResource(style.getCenterLogoResource());
			try (InputStream in = res.getInputStream()) {
				BufferedImage logo = ImageIO.read(in);
				if (logo == null) return Double.NaN;
				double max = badgeR * (textToo ? 0.9 : 1.3);
				double scale = max / Math.max(logo.getWidth(), logo.getHeight());
				double w = logo.getWidth() * scale, h = logo.getHeight() * scale;
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
		double innerW = badgeR * TEXT_INNER_WIDTH_RATIO;

		Font[] fonts = new Font[lines.length];
		double totalH = 0;
		for (int i = 0; i < lines.length; i++) {
			double px = badgeR * (i == 0 ? BRAND_TEXT_RATIO : LINE_TEXT_RATIO);
			fonts[i] = fitFont(g, style.getCenterTextFont(), px, lines[i], innerW);
			totalH += fonts[i].getSize2D() * LINE_SPACING;
		}

		double y = Double.isNaN(startY) ? cy - totalH / 2 : startY;
		for (int i = 0; i < lines.length; i++) {
			g.setFont(fonts[i]);
			FontMetrics fm = g.getFontMetrics();
			g.drawString(lines[i],
					(int) Math.round(cx - fm.stringWidth(lines[i]) / 2.0),
					(int) Math.round(y + fm.getAscent()));
			y += fonts[i].getSize2D() * LINE_SPACING;
		}
	}

	/** Largest BOLD font at {@code family} whose {@code text} fits {@code maxWidth}, down to a floor. */
	private Font fitFont(Graphics2D g, String family, double px, String text, double maxWidth) {
		float sz = (float) px;
		Font f = new Font(family, Font.BOLD, Math.max(1, Math.round(sz)));
		while (sz > MIN_FONT_PX) {
			f = new Font(family, Font.BOLD, Math.round(sz));
			if (g.getFontMetrics(f).stringWidth(text) <= maxWidth) break;
			sz -= 1f;
		}
		return f;
	}

	// ---- shared paint helpers ----------------------------------------------

	/** Two-stop radial gradient centred at (cx,cy). */
	private static RadialGradientPaint radial(double cx, double cy, double radius, Color inner, Color outer) {
		return new RadialGradientPaint(new Point2D.Double(cx, cy), (float) radius,
				new float[]{0f, 1f}, new Color[]{inner, outer}, CycleMethod.NO_CYCLE);
	}

	private static Ellipse2D.Double disc(double cx, double cy, double r) {
		return new Ellipse2D.Double(cx - r, cy - r, r * 2, r * 2);
	}

	/** Fill {@code shape} with {@code color}, or clear to transparent when {@code color} is null. */
	private static void fillOrClear(Graphics2D g, Shape shape, Color color) {
		if (color == null) {
			Composite prev = g.getComposite();
			g.setComposite(AlphaComposite.Clear);
			g.fill(shape);
			g.setComposite(prev);
		} else {
			g.setColor(color);
			g.fill(shape);
		}
	}

	// ---- misc ---------------------------------------------------------------

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
