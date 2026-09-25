package com.airtel.userprofile.eventpass.dto.request;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonInclude;
import jakarta.validation.constraints.NotBlank;
import lombok.Data;
import lombok.NoArgsConstructor;

/** API 4 — customer app asks the User Profile Service to (re)generate the signed membership QR. */
@Data
@NoArgsConstructor
@JsonIgnoreProperties(ignoreUnknown = true)
@JsonInclude(JsonInclude.Include.NON_NULL)
public class QrGenerateRequest {

	/** Stable customer-device identifier (install id / keychain-backed), NOT reset per launch. */
	@NotBlank
	private String deviceId;

	/** Client timestamp (advisory only — the server clock is authoritative for iat/exp). */
	private Long timestamp;
}
