package com.airtel.userprofile.eventpass.service;

import lombok.AllArgsConstructor;
import lombok.Getter;

import java.time.Instant;
import java.util.Set;

/** Verified, trusted contents of a membership QR token (all read from inside the signature). */
@Getter
@AllArgsConstructor
public class QrClaims {

	/** Customer MSISDN resolved from the opaque subject. */
	private final String msisdn;
	/** Customer device that generated the QR. */
	private final String deviceId;
	/** Events (programIds) the customer had won at issue time. */
	private final Set<String> wonEventIds;
	private final String jti;
	private final Instant issuedAt;
}
