package com.airtel.userprofile.eventpass.service.impl;

import com.airtel.userprofile.eventpass.service.CachedQr;
import com.airtel.userprofile.eventpass.service.QrIssuanceStore;
import com.airtel.userprofile.service.impl.helper.AerospikeManager;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.time.Instant;
import java.util.Optional;

/**
 * Aerospike-backed active-QR cache, mirroring how {@code UsedOrderCacheServiceImpl} uses
 * {@link AerospikeManager}. Key = customer msisdn; value = the {@link CachedQr} as JSON; record
 * TTL = QR TTL, so it self-expires with the token.
 *
 * <p>Platform note: add an {@code AerospikeDetails.EVENT_QR_LATEST} namespace/set and a TTL-aware
 * {@code putDetails(key, value, details, ttl, useDisk)} overload; wired here by name.
 */
@Service
@Slf4j
public class QrIssuanceStoreImpl implements QrIssuanceStore {

	private static final boolean USE_DISK = false;
	private final ObjectMapper mapper = new ObjectMapper().findAndRegisterModules();

	@Autowired(required = false)
	private AerospikeManager aerospikeManager;

	@Override
	public void store(String msisdn, CachedQr qr, long ttlSeconds) {
		if (aerospikeManager == null) {
			log.warn("AerospikeManager unavailable; active QR not cached for msisdn={}", msisdn);
			return;
		}
		try {
			String json = mapper.writeValueAsString(qr);
			aerospikeManager.putDetails(key(msisdn), json,
					com.airtel.userprofile.constants.AerospikeDetails.EVENT_QR_LATEST, (int) ttlSeconds, USE_DISK);
		} catch (Exception e) {
			log.warn("Failed to cache active QR for msisdn={}: {}", msisdn, e.getMessage());
		}
	}

	@Override
	public Optional<CachedQr> getActive(String msisdn) {
		if (aerospikeManager == null) {
			return Optional.empty();   // fail safe: cannot confirm → caller mints a fresh QR
		}
		Object raw = aerospikeManager.getDetails(key(msisdn),
				com.airtel.userprofile.constants.AerospikeDetails.EVENT_QR_LATEST, USE_DISK);
		if (raw == null) {
			return Optional.empty();
		}
		try {
			CachedQr qr = mapper.readValue(raw.toString(), CachedQr.class);
			// defensive: honour expiry even if the record has not yet been evicted
			if (qr.getExpiresAt() != null && qr.getExpiresAt().isBefore(Instant.now())) {
				return Optional.empty();
			}
			return Optional.of(qr);
		} catch (Exception e) {
			log.warn("Failed to read cached QR for msisdn={}: {}", msisdn, e.getMessage());
			return Optional.empty();
		}
	}

	private static String key(String msisdn) {
		return "qr:latest:" + msisdn;
	}
}
