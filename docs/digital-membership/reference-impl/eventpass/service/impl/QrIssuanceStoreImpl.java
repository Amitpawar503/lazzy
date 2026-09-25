package com.airtel.userprofile.eventpass.service.impl;

import com.airtel.userprofile.eventpass.service.QrIssuanceStore;
import com.airtel.userprofile.service.impl.helper.AerospikeManager;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

/**
 * Aerospike-backed single-active pointer, mirroring how {@code UsedOrderCacheServiceImpl} uses
 * {@link AerospikeManager}. Key = customer msisdn; value = latest jti; record TTL = QR TTL, so the
 * pointer self-expires with the token.
 *
 * <p>Platform note: add an {@code AerospikeDetails.EVENT_QR_LATEST} namespace/set and a
 * TTL-aware {@code putDetails} overload to match existing conventions; wired here by name.
 */
@Service
@Slf4j
public class QrIssuanceStoreImpl implements QrIssuanceStore {

	private static final boolean USE_DISK = false;

	@Autowired(required = false)
	private AerospikeManager aerospikeManager;

	@Override
	public void setLatest(String msisdn, String jti, long ttlSeconds) {
		if (aerospikeManager == null) {
			log.warn("AerospikeManager unavailable; single-active QR pointer not persisted for msisdn={}", msisdn);
			return;
		}
		// putDetails(key, value, details, ttlSeconds, useDisk) — TTL-aware overload
		aerospikeManager.putDetails(key(msisdn), jti,
				com.airtel.userprofile.constants.AerospikeDetails.EVENT_QR_LATEST, (int) ttlSeconds, USE_DISK);
	}

	@Override
	public boolean isLatest(String msisdn, String jti) {
		if (aerospikeManager == null) {
			// Fail safe: cannot confirm single-active → treat as not latest so the customer refreshes.
			return false;
		}
		Object latest = aerospikeManager.getDetails(key(msisdn),
				com.airtel.userprofile.constants.AerospikeDetails.EVENT_QR_LATEST, USE_DISK);
		return latest != null && latest.toString().equals(jti);
	}

	private static String key(String msisdn) {
		return "qr:latest:" + msisdn;
	}
}
