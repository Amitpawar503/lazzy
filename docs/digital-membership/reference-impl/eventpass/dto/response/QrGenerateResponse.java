package com.airtel.userprofile.eventpass.dto.response;

import com.fasterxml.jackson.annotation.JsonInclude;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.Instant;

/** API 4 response — the signed membership QR string and its expiry. */
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
@JsonInclude(JsonInclude.Include.NON_NULL)
public class QrGenerateResponse {

	/** Opaque signed token to render as a QR (not a URL). */
	private String qrToken;
	private Instant expiresAt;
}
