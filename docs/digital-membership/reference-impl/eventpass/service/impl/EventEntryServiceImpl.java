package com.airtel.userprofile.eventpass.service.impl;

import com.airtel.userprofile.eventpass.dao.EventRedemptionDao;
import com.airtel.userprofile.eventpass.dao.RedeemOutcome;
import com.airtel.userprofile.eventpass.dao.ScanLogDao;
import com.airtel.userprofile.eventpass.document.AgentSessionDocument;
import com.airtel.userprofile.eventpass.document.EventRedemptionDocument;
import com.airtel.userprofile.eventpass.document.ScanLogDocument;
import com.airtel.userprofile.eventpass.dto.request.EntryScanRequest;
import com.airtel.userprofile.eventpass.dto.response.EntryScanResponse;
import com.airtel.userprofile.eventpass.enums.Checkpoint;
import com.airtel.userprofile.eventpass.enums.EntryCallback;
import com.airtel.userprofile.eventpass.exception.AgentSessionInvalidException;
import com.airtel.userprofile.eventpass.exception.QrExpiredException;
import com.airtel.userprofile.eventpass.exception.QrInvalidException;
import com.airtel.userprofile.eventpass.service.AgentAccessService;
import com.airtel.userprofile.eventpass.service.EventEntryService;
import com.airtel.userprofile.eventpass.service.QrClaims;
import com.airtel.userprofile.eventpass.service.QrTokenService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.time.Instant;
import java.util.Optional;

/**
 * The gate authority. Order mirrors the HLD validation chain: session → token → winner → atomic
 * redeem → audit. Every DECISION (allow and deny) is returned as a 200 {@link EntryScanResponse};
 * only unexpected infra faults become {@code SERVICE_UNAVAILABLE} and never auto-allow.
 */
@Service
@Slf4j
@RequiredArgsConstructor
public class EventEntryServiceImpl implements EventEntryService {

	private final AgentAccessService agentAccess;
	private final QrTokenService qrTokenService;
	private final EventRedemptionDao redemptionDao;
	private final ScanLogDao scanLogDao;

	@Override
	public EntryScanResponse recordEntry(String agentSessionId, EntryScanRequest request) {
		try {
			// 0) Idempotency: a retried scanRequestId replays the original decision (no re-redeem)
			Optional<ScanLogDocument> prior = scanLogDao.findByScanRequestId(request.getScanRequestId());
			if (prior.isPresent()) {
				log.debug("Idempotent replay for scanRequestId={} -> {}",
						request.getScanRequestId(), prior.get().getCallback());
				return rebuild(prior.get());
			}

			// 1–2) Agent session valid & authorized for this checkpoint (event derived from session)
			AgentSessionDocument session;
			try {
				session = agentAccess.requireAuthorizedSession(agentSessionId, request.getCheckpoint());
			} catch (AgentSessionInvalidException e) {
				log.warn("Scan rejected — session invalid: {}", e.getMessage());
				return audit(EntryScanResponse.of(EntryCallback.STAFF_SESSION_INVALID),
						null, null, request, null);
			}
			String eventId = session.getEventId();
			Checkpoint checkpoint = session.getCheckpoint();
			String agentMsisdn = session.getMsisdn();

			// 3–5) Verify token (signature, version, TTL, single-active)
			QrClaims claims;
			try {
				claims = qrTokenService.verify(request.getQrToken());
			} catch (QrExpiredException e) {
				return audit(EntryScanResponse.of(EntryCallback.QR_EXPIRED), eventId, null, request, agentMsisdn);
			} catch (QrInvalidException e) {
				return audit(EntryScanResponse.of(EntryCallback.INVALID_QR), eventId, null, request, agentMsisdn);
			}

			// 6) Winner check — the scanned event must be among the QR's won events
			if (claims.getWonEventIds() == null || !claims.getWonEventIds().contains(eventId)) {
				return audit(EntryScanResponse.of(EntryCallback.NOT_ENTITLED),
						eventId, claims, request, agentMsisdn);
			}

			// 7) Atomic redeem (event, msisdn, checkpoint) — exactly one first-claim
			RedeemOutcome outcome = redemptionDao.tryRedeem(
					eventId, claims.getMsisdn(), checkpoint,
					claims.getDeviceId(), agentMsisdn, request.getScanRequestId());

			EntryScanResponse response;
			if (outcome.isFirstClaim()) {
				response = EntryScanResponse.of(EntryCallback.ENTRY_ALLOWED);
			} else {
				EventRedemptionDocument first = outcome.getRow();
				boolean sameDevice = first.getDeviceId() != null
						&& first.getDeviceId().equals(claims.getDeviceId());
				response = EntryScanResponse.of(
						sameDevice ? EntryCallback.DUPLICATE_ENTRY : EntryCallback.ALREADY_ENTERED_OTHER_DEVICE);
				response.setFirstClaimAt(first.getRedeemedAt());
				if (!sameDevice) {
					response.setOtherDeviceId(first.getDeviceId());
				}
			}
			response.setHolderMasked(mask(claims.getMsisdn()));

			// 8) Audit (always)
			return audit(response, eventId, claims, request, agentMsisdn);

		} catch (Exception e) {
			// Never auto-allow on infra failure; nothing that committed is lost (idempotency replays it)
			log.error("Scan failed unexpectedly for scanRequestId={}", request.getScanRequestId(), e);
			return EntryScanResponse.of(EntryCallback.SERVICE_UNAVAILABLE);
		}
	}

	private EntryScanResponse audit(EntryScanResponse response, String eventId, QrClaims claims,
									EntryScanRequest request, String agentMsisdn) {
		try {
			scanLogDao.save(ScanLogDocument.builder()
					.scanRequestId(request.getScanRequestId())
					.eventId(eventId)
					.checkpoint(request.getCheckpoint())
					.agentMsisdn(agentMsisdn)
					.customerMsisdn(claims != null ? claims.getMsisdn() : null)
					.deviceId(claims != null ? claims.getDeviceId() : null)
					.callback(response.getCallback())
					.tokenJti(claims != null ? claims.getJti() : null)
					.serverTs(Instant.now())
					.build());
		} catch (Exception logEx) {
			// A duplicate scanRequestId here means a concurrent retry already logged it — replay that.
			return scanLogDao.findByScanRequestId(request.getScanRequestId())
					.map(this::rebuild)
					.orElse(response);
		}
		return response;
	}

	@Override
	public java.util.List<ScanLogDocument> scanHistory(String customerMsisdn) {
		return scanLogDao.findByCustomerMsisdnOrderByServerTs(customerMsisdn);
	}

	/** Rebuild a response from a stored log entry (idempotent replay). */
	private EntryScanResponse rebuild(ScanLogDocument log) {
		EntryScanResponse r = EntryScanResponse.of(log.getCallback());
		if (log.getCustomerMsisdn() != null) {
			r.setHolderMasked(mask(log.getCustomerMsisdn()));
		}
		return r;
	}

	/** Mask an MSISDN for the agent screen — never expose the full number. e.g. "***** 3210". */
	private static String mask(String msisdn) {
		if (msisdn == null || msisdn.length() < 4) {
			return "*****";
		}
		return "***** " + msisdn.substring(msisdn.length() - 4);
	}
}
