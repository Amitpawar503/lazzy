package com.airtel.userprofile.eventpass.config;

import lombok.Data;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.cloud.context.config.annotation.RefreshScope;
import org.springframework.stereotype.Component;

/**
 * Visual style for the rendered membership QR (the circular, dotted, gradient card shown in the
 * Thanks App). Everything here is environment-tunable via {@code eventpass.qr-style.*} and picked up
 * without a redeploy ({@link RefreshScope}). Colours are hex strings ({@code #RRGGBB} or
 * {@code #AARRGGBB}); {@code "transparent"} is accepted for {@link #backgroundColor}.
 *
 * <p>These knobs only affect how the QR <em>looks</em>. The payload (the signed token / deeplink /
 * info) is untouched, so restyling never changes what a scanner reads.
 */
@Data
@Component
@RefreshScope
@ConfigurationProperties(prefix = "eventpass.qr-style")
public class QrStyleProperties {

	/** How each QR module (cell) is drawn. */
	public enum ModuleShape { DOTS, ROUNDED, SQUARE }

	// ---- canvas -------------------------------------------------------------

	/** Output image edge length in px (square). */
	private int size = 720;

	/** Quiet zone in modules around the code (ZXing margin). Keep >= 2 so scanners lock on. */
	private int quietZoneModules = 2;

	/** PNG background. {@code "transparent"} renders on alpha=0 (good for overlaying on a card). */
	private String backgroundColor = "#FFFFFF";

	// ---- modules ------------------------------------------------------------

	/** Shape used for the data modules. */
	private ModuleShape moduleShape = ModuleShape.DOTS;

	/** Diameter/size of a drawn module as a fraction of the cell (0.5–1.0). 0.86 leaves airy gaps. */
	private double moduleSizeRatio = 0.86;

	/**
	 * When true, data modules are filled with a radial gradient from {@link #gradientInnerColor}
	 * (centre) to {@link #gradientOuterColor} (edge) — the Advantage-Club look. When false, the flat
	 * {@link #foregroundColor} is used.
	 */
	private boolean gradientEnabled = true;

	private String gradientInnerColor = "#F5A623";
	private String gradientOuterColor = "#C8102E";

	/** Flat module colour when {@link #gradientEnabled} is false. */
	private String foregroundColor = "#C8102E";

	// ---- finder patterns (the three "eyes") --------------------------------

	/** Draw the three finder patterns as rounded concentric rings instead of plain modules. */
	private boolean styledFinder = true;

	/** Corner radius of the finder rings as a fraction of the finder box (0 = square, 0.5 = pill). */
	private double finderCornerRatio = 0.35;

	private String finderColor = "#C8102E";

	// ---- centre badge (logo / changeable text) -----------------------------

	/** Render the centre badge (circle + text/logo) over the middle of the code. EC level H covers it. */
	private boolean centerBadgeEnabled = true;

	/** Badge diameter as a fraction of the image edge (0.15–0.30). Larger needs EC level H. */
	private double centerBadgeRatio = 0.24;

	private String centerBadgeInnerColor = "#E4002B";
	private String centerBadgeOuterColor = "#8B0000";

	/** White ring drawn between the badge and the surrounding modules for separation. */
	private boolean centerRingEnabled = true;
	private String centerRingColor = "#FFFFFF";
	private double centerRingRatio = 0.04;

	/**
	 * Default centre text. Newlines split into stacked lines; the first line is drawn largest
	 * (brand line). Override per request via {@code QrRenderRequest.centerText}. Empty/blank hides it
	 * (e.g. when {@link #centerLogoResource} is set).
	 */
	private String centerText = "airtel\nPOSTPAID\nADVANTAGE\nCLUB";
	private String centerTextColor = "#FFFFFF";
	private String centerTextFont = "SansSerif";

	/**
	 * Optional classpath image (e.g. {@code classpath:qr/advantage-logo.png}) drawn inside the badge
	 * instead of, or above, the text. Null/blank ⇒ text only.
	 */
	private String centerLogoResource;

	// ---- encoding -----------------------------------------------------------

	/**
	 * Error-correction level: L/M/Q/H. Use H (30%) whenever {@link #centerBadgeEnabled} is true so the
	 * covered centre still decodes.
	 */
	private String errorCorrection = "H";

	/**
	 * Resilience: when the styled render fails for an otherwise-encodable payload (e.g. a bad centre
	 * logo, font, or colour), fall back to a plain black-on-white QR of the same data instead of
	 * failing the request. A payload that cannot be encoded at all still errors.
	 */
	private boolean resilientRender = true;
}
