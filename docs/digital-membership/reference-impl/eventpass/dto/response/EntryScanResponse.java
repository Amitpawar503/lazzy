package com.airtel.userprofile.eventpass.dto.response;

import com.airtel.userprofile.eventpass.enums.EntryCallback;
import com.fasterxml.jackson.annotation.JsonInclude;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.Instant;

/** API 3 response — the gate decision. Only {@code ENTRY_ALLOWED} admits. */
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
@JsonInclude(JsonInclude.Include.NON_NULL)
public class EntryScanResponse {

	private EntryCallback callback;
	private boolean admit;
	private String displayColor;
	private String message;

	/** Masked holder identity for the agent to eyeball, e.g. "Amit ***** 3210". Never raw PII. */
	private String holderMasked;

	/** Set on DUPLICATE_ENTRY / ALREADY_ENTERED_OTHER_DEVICE — when the first claim happened. */
	private Instant firstClaimAt;

	/** Set on ALREADY_ENTERED_OTHER_DEVICE — the device that made the first claim. */
	private String otherDeviceId;

	public static EntryScanResponse of(EntryCallback cb) {
		return EntryScanResponse.builder()
				.callback(cb)
				.admit(cb.isAdmit())
				.displayColor(cb.getColor())
				.message(cb.getDefaultMessage())
				.build();
	}
}
