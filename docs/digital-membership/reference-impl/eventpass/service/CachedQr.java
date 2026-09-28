package com.airtel.userprofile.eventpass.service;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.Instant;

/**
 * The active QR cached per customer in the fast store (Aerospike). Holds enough to (a) enforce
 * single-active via {@code jti}, and (b) <b>return the existing token</b> on validate without
 * re-minting. TTL of the cache record == the token TTL, so it self-expires with the QR.
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
@JsonIgnoreProperties(ignoreUnknown = true)
public class CachedQr {

	private String jti;
	private String token;
	private String deviceId;
	private Instant expiresAt;
}
