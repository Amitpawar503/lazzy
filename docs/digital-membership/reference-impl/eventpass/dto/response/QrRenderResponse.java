package com.airtel.userprofile.eventpass.dto.response;

import com.fasterxml.jackson.annotation.JsonInclude;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * A rendered styled QR image. {@code imageDataUri} is a ready-to-use {@code data:image/png;base64,…}
 * string the app can drop straight into an {@code <img>} / {@code Image}. {@code width}/{@code height}
 * are the pixel dimensions. {@code encoded} echoes the exact payload embedded, so callers can assert
 * the round-trip without re-decoding.
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
@JsonInclude(JsonInclude.Include.NON_NULL)
public class QrRenderResponse {

	/** {@code data:image/png;base64,<...>} — renderable as-is. */
	private String imageDataUri;

	private int width;
	private int height;

	/** The payload embedded in the image (== request {@code data}). */
	private String encoded;
}
