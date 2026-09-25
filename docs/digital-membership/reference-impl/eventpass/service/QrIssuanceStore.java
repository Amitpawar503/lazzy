package com.airtel.userprofile.eventpass.service;

/**
 * Per-customer "latest jti" pointer with a TTL — the single-active anchor that makes a refresh (or
 * a shared old screenshot) stop working immediately, even within the TTL. Backed by the same fast
 * store the contest module uses (Aerospike / Redis) so it is shared across service instances.
 */
public interface QrIssuanceStore {

	/** Record {@code jti} as the latest token for {@code msisdn}, expiring after {@code ttlSeconds}. */
	void setLatest(String msisdn, String jti, long ttlSeconds);

	/** True iff {@code jti} is still the latest recorded token for {@code msisdn}. */
	boolean isLatest(String msisdn, String jti);
}
