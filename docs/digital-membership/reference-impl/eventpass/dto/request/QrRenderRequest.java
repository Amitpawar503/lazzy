package com.airtel.userprofile.eventpass.dto.request;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonInclude;
import jakarta.validation.constraints.NotBlank;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * Render a styled circular QR for any payload. {@code data} is what the QR carries and what a camera
 * reads back — a signed membership token, a deeplink ({@code airtelthanks://…} / {@code https://…}),
 * or any opaque info string. On scan the app decodes {@code data} locally and POSTs it to the backend
 * (e.g. API 3 {@code /v1/entry}); the image is purely a carrier, so any string round-trips unchanged.
 *
 * <p>The style fields are optional per-request overrides on top of {@code eventpass.qr-style.*}; any
 * left null falls back to config. Only {@code data} is required.
 */
@Data
@NoArgsConstructor
@JsonIgnoreProperties(ignoreUnknown = true)
@JsonInclude(JsonInclude.Include.NON_NULL)
public class QrRenderRequest {

	/** The token / deeplink / info to encode. This exact string is what a scanner recovers. */
	@NotBlank
	private String data;

	/** Overrides the configured centre text (newline-separated lines). Blank string hides the text. */
	private String centerText;

	/** Optional colour overrides (hex {@code #RRGGBB} / {@code #AARRGGBB}); null ⇒ use config. */
	private String gradientInnerColor;
	private String gradientOuterColor;
	private String finderColor;
	private String backgroundColor;

	/** Optional size override in px; null/<=0 ⇒ use config. */
	private Integer size;
}
