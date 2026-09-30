package com.airtel.userprofile.eventpass.util;

import org.springframework.util.StringUtils;

import java.awt.Color;

/**
 * Parses configured / request colour strings into {@link Color}. One place, one job (SRP) so the
 * renderer, the config→style mapping, and per-request overrides all agree on the accepted syntax:
 * {@code #RRGGBB}, {@code #AARRGGBB}, or {@code "transparent"} (→ {@code null}, i.e. no fill).
 */
public final class HexColors {

	private HexColors() {
	}

	/**
	 * @return the colour, or {@code null} for blank / {@code "transparent"}.
	 * @throws IllegalArgumentException if non-blank and not a valid 6-/8-digit hex.
	 */
	public static Color parse(String hex) {
		if (!StringUtils.hasText(hex) || "transparent".equalsIgnoreCase(hex.trim())) {
			return null;
		}
		String h = hex.trim();
		if (h.startsWith("#")) {
			h = h.substring(1);
		}
		try {
			if (h.length() == 6) {
				return new Color(Integer.parseInt(h, 16));
			}
			if (h.length() == 8) { // AARRGGBB
				long v = Long.parseLong(h, 16);
				return new Color((int) (v >> 16) & 0xFF, (int) (v >> 8) & 0xFF, (int) v & 0xFF, (int) (v >> 24) & 0xFF);
			}
		} catch (NumberFormatException ignored) {
			// fall through to the common error
		}
		throw new IllegalArgumentException("Invalid colour: " + hex + " (use #RRGGBB, #AARRGGBB, or 'transparent')");
	}
}
