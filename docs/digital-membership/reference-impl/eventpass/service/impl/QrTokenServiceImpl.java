package com.airtel.userprofile.eventpass.service.impl;

import com.airtel.userprofile.contest.service.PiiEncryptionDecryption;
import com.airtel.userprofile.eventpass.config.EventPassProperties;
import com.airtel.userprofile.eventpass.exception.QrExpiredException;
import com.airtel.userprofile.eventpass.exception.QrInvalidException;
import com.airtel.userprofile.eventpass.service.QrClaims;
import com.airtel.userprofile.eventpass.service.QrIssuanceStore;
import com.airtel.userprofile.eventpass.service.QrTokenService;
import io.jsonwebtoken.Claims;
import io.jsonwebtoken.ExpiredJwtException;
import io.jsonwebtoken.JwtException;
import io.jsonwebtoken.Jws;
import io.jsonwebtoken.Jwts;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.security.PrivateKey;
import java.security.PublicKey;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Date;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.UUID;

/**
 * Signs/verifies the membership QR (compact JWS, ES256). Claims: {@code sub} = opaque (encrypted)
 * msisdn — never raw PII (Q3); {@code dev} = deviceId; {@code events} = won programIds;
 * {@code ver} = schema version; {@code jti}/{@code iat}/{@code exp} standard.
 *
 * <p>Single-active: {@code issue} registers {@code jti} as the latest for the customer; {@code verify}
 * requires the token to still be the latest, so a refresh (or an old shared screenshot) fails as
 * {@code QR_EXPIRED} even within the TTL.
 *
 * <p>Keys are provided by a KMS/HSM-backed {@code @Configuration}: {@code signingKey} (private,
 * backend-only) and {@code verificationKey} (public), rotated via the {@code kid} header.
 */
@Service
@Slf4j
@RequiredArgsConstructor
public class QrTokenServiceImpl implements QrTokenService {

	private static final String CLAIM_VERSION = "ver";
	private static final String CLAIM_DEVICE = "dev";
	private static final String CLAIM_EVENTS = "events";

	private final EventPassProperties props;
	private final QrIssuanceStore issuanceStore;
	private final PiiEncryptionDecryption pii;
	private final PrivateKey signingKey;      // from KMS/HSM config bean
	private final PublicKey verificationKey;  // from KMS/HSM config bean

	@Override
	public String issue(String msisdn, String deviceId, Set<String> wonEventIds) {
		Instant now = Instant.now();
		Instant exp = now.plusSeconds(props.getQrTtlSeconds());
		String jti = UUID.randomUUID().toString();

		String token = Jwts.builder()
				.header().keyId(props.getSigningKeyId()).and()
				.id(jti)
				.issuer(props.getIssuer())
				.subject(pii.encrypt(msisdn))                 // opaque subject, never raw MSISDN
				.issuedAt(Date.from(now))
				.expiration(Date.from(exp))
				.claim(CLAIM_VERSION, props.getTokenVersion())
				.claim(CLAIM_DEVICE, deviceId)
				.claim(CLAIM_EVENTS, new ArrayList<>(wonEventIds == null ? Set.of() : wonEventIds))
				.signWith(signingKey)
				.compact();

		// register as the single-active token; TTL matches the token so the pointer self-expires
		issuanceStore.setLatest(msisdn, jti, props.getQrTtlSeconds());
		log.debug("Issued QR for msisdn={} jti={} events={}", msisdn, jti, wonEventIds);
		return token;
	}

	@Override
	@SuppressWarnings("unchecked")
	public QrClaims verify(String qrToken) {
		Jws<Claims> jws;
		try {
			jws = Jwts.parser()
					.verifyWith(verificationKey)
					.requireIssuer(props.getIssuer())
					.build()
					.parseSignedClaims(qrToken);
		} catch (ExpiredJwtException e) {
			throw new QrExpiredException("QR token past TTL");
		} catch (JwtException | IllegalArgumentException e) {
			// bad signature, malformed, unsupported alg, wrong issuer, etc.
			throw new QrInvalidException("QR token invalid: " + e.getClass().getSimpleName());
		}

		Claims c = jws.getPayload();

		Integer ver = c.get(CLAIM_VERSION, Integer.class);
		if (ver == null || ver > props.getTokenVersion()) {
			throw new QrInvalidException("Unsupported token version: " + ver);
		}

		String msisdn = pii.decrypt(c.getSubject());
		if (msisdn == null || msisdn.isBlank()) {
			throw new QrInvalidException("Unresolvable subject");
		}

		// single-active: superseded token (older screenshot / pre-refresh) → treat as expired
		if (!issuanceStore.isLatest(msisdn, c.getId())) {
			throw new QrExpiredException("QR superseded by a newer issuance");
		}

		Set<String> events = new HashSet<>();
		Object raw = c.get(CLAIM_EVENTS);
		if (raw instanceof List<?> list) {
			for (Object o : list) {
				if (o != null) events.add(o.toString());
			}
		}

		return new QrClaims(msisdn, c.get(CLAIM_DEVICE, String.class), events,
				c.getId(), c.getIssuedAt().toInstant());
	}
}
