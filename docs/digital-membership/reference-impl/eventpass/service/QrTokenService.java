package com.airtel.userprofile.eventpass.service;

import java.util.Set;

/** Mints and verifies the signed membership QR token. Signing key lives in KMS/HSM, backend-only. */
public interface QrTokenService {

	/**
	 * Mint a signed token for the customer, embedding the won events, and cache it as the
	 * single-active QR (supersedes any previous QR immediately).
	 * @return the minted {@link CachedQr} (token + jti + expiresAt).
	 */
	CachedQr issue(String msisdn, String deviceId, Set<String> wonEventIds);

	/**
	 * Verify signature, version, TTL and single-active status.
	 * @throws com.airtel.userprofile.eventpass.exception.QrInvalidException malformed/forged/unsupported
	 * @throws com.airtel.userprofile.eventpass.exception.QrExpiredException past TTL or superseded
	 */
	QrClaims verify(String qrToken);
}
