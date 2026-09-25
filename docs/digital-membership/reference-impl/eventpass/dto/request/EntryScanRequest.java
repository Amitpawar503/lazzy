package com.airtel.userprofile.eventpass.dto.request;

import com.airtel.userprofile.eventpass.enums.Checkpoint;
import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonInclude;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * API 3 — agent posts a decoded QR for a decision. The {@code eventId} is NOT taken from the body;
 * it comes from the agent session. {@code checkpoint} is validated against the agent's authorized
 * set. {@code scanRequestId} is the idempotency key (reuse the same value on retry).
 */
@Data
@NoArgsConstructor
@JsonIgnoreProperties(ignoreUnknown = true)
@JsonInclude(JsonInclude.Include.NON_NULL)
public class EntryScanRequest {

	@NotBlank
	private String qrToken;

	@NotNull
	private Checkpoint checkpoint;

	@NotBlank
	private String scanRequestId;
}
