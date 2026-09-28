package com.airtel.userprofile.eventpass.service;

import java.util.Optional;

/**
 * Per-customer active-QR cache with a TTL (Aerospike / Redis), shared across service instances.
 * It is both the single-active anchor (a refresh/screenshot older than the stored {@code jti}
 * fails) <b>and</b> the source for QR "validate" (get-or-create): if a live QR is cached, it is
 * returned as-is instead of minting a new one.
 */
public interface QrIssuanceStore {

	/** Store {@code qr} as the active QR for {@code msisdn}, expiring after {@code ttlSeconds}. */
	void store(String msisdn, CachedQr qr, long ttlSeconds);

	/** The active (not-yet-expired) cached QR for {@code msisdn}, if any. */
	Optional<CachedQr> getActive(String msisdn);

	/** True iff {@code jti} is still the active token for {@code msisdn} (single-active check). */
	default boolean isLatest(String msisdn, String jti) {
		return getActive(msisdn).map(c -> jti != null && jti.equals(c.getJti())).orElse(false);
	}
}
