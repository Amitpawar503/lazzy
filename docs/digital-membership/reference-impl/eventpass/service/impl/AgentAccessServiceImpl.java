package com.airtel.userprofile.eventpass.service.impl;

import com.airtel.userprofile.eventpass.config.EventPassProperties;
import com.airtel.userprofile.eventpass.dao.AgentSessionDao;
import com.airtel.userprofile.eventpass.dao.AgentWhitelistDao;
import com.airtel.userprofile.eventpass.dao.EventDao;
import com.airtel.userprofile.eventpass.document.AgentSessionDocument;
import com.airtel.userprofile.eventpass.document.AgentWhitelistDocument;
import com.airtel.userprofile.eventpass.document.EventDocument;
import com.airtel.userprofile.eventpass.dto.request.WhitelistUpsertRequest;
import com.airtel.userprofile.eventpass.dto.response.AgentEventAccess;
import com.airtel.userprofile.eventpass.dto.response.AgentValidateResponse;
import com.airtel.userprofile.eventpass.enums.Checkpoint;
import com.airtel.userprofile.eventpass.exception.AgentSessionInvalidException;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.time.Instant;
import java.util.List;
import java.util.UUID;
import java.util.stream.Collectors;

@Service
@Slf4j
@RequiredArgsConstructor
public class AgentAccessServiceImpl implements AgentAccessService {

	private final AgentWhitelistDao whitelistDao;
	private final AgentSessionDao sessionDao;
	private final EventDao eventDao;
	private final EventPassProperties props;

	@Override
	public AgentWhitelistDocument upsertWhitelist(WhitelistUpsertRequest request, String actor) {
		// Require the event to exist so we can align the relation's cleanup with the event's end.
		EventDocument event = eventDao.findById(request.getEventId())
				.orElseThrow(() -> new IllegalArgumentException(
						"Unknown event " + request.getEventId() + "; create the event first"));
		AgentWhitelistDocument doc = AgentWhitelistDocument.builder()
				.eventId(request.getEventId())
				.msisdn(request.getMsisdn())
				.checkpoints(request.getCheckpoints())
				.active(request.getActive() == null || request.getActive())   // defaults active
				.endTime(event.getEndTime())
				.cleanupAt(event.getCleanupAt())                              // = endTime + 30d (TTL)
				.createdBy(actor)
				.build();
		AgentWhitelistDocument saved = whitelistDao.upsert(doc);
		log.info("Whitelist created/upserted by {}: event={} msisdn={} checkpoints={} cleanupAt={}",
				actor, request.getEventId(), request.getMsisdn(), request.getCheckpoints(), saved.getCleanupAt());
		return saved;
	}

	@Override
	public java.util.List<AgentWhitelistDocument> getWhitelist(String eventId, String msisdn) {
		if (msisdn != null && !msisdn.isBlank()) {
			AgentWhitelistDocument row = whitelistDao.findOne(eventId, msisdn)
					.orElseThrow(() -> new IllegalArgumentException(
							"No whitelist row for event " + eventId + " / msisdn " + msisdn));
			return java.util.List.of(row);
		}
		return whitelistDao.findByEvent(eventId);
	}

	@Override
	public AgentWhitelistDocument updateWhitelist(WhitelistUpsertRequest request, String actor) {
		long matched = whitelistDao.update(
				request.getEventId(), request.getMsisdn(), request.getCheckpoints(), request.getActive());
		if (matched == 0) {
			throw new IllegalArgumentException(
					"No whitelist row to update for event " + request.getEventId() + " / msisdn " + request.getMsisdn());
		}
		log.info("Whitelist updated by {}: event={} msisdn={} checkpoints={} active={}",
				actor, request.getEventId(), request.getMsisdn(), request.getCheckpoints(), request.getActive());
		return whitelistDao.findOne(request.getEventId(), request.getMsisdn()).orElseThrow();
	}

	@Override
	public void deleteWhitelist(String eventId, String msisdn, String actor) {
		long deleted = whitelistDao.delete(eventId, msisdn);
		if (deleted == 0) {
			throw new IllegalArgumentException(
					"No whitelist row to delete for event " + eventId + " / msisdn " + msisdn);
		}
		log.info("Whitelist deleted by {}: event={} msisdn={}", actor, eventId, msisdn);
	}

	@Override
	public AgentValidateResponse validate(String agentMsisdn, String deviceInfo) {
		List<AgentWhitelistDocument> rows = whitelistDao.findActiveByMsisdn(agentMsisdn);
		if (rows.isEmpty()) {
			return AgentValidateResponse.builder().authorized(false).build();  // no event data / no session
		}
		List<AgentEventAccess> events = rows.stream()
				.map(r -> AgentEventAccess.builder()
						.eventId(r.getEventId())
						.checkpoints(r.getCheckpoints())
						// eventName/venue enriched from event/program metadata where available
						.build())
				.collect(Collectors.toList());

		// open a single-active per-agent session in the same call (revokes any prior session)
		Instant now = Instant.now();
		AgentSessionDocument session = AgentSessionDocument.builder()
				.id(UUID.randomUUID().toString())
				.msisdn(agentMsisdn)
				.revoked(false)
				.createdAt(now)
				.expiresAt(now.plusSeconds(props.getAgentSessionTtlSeconds()))
				.deviceInfo(deviceInfo)
				.build();
		sessionDao.openExclusive(session);
		log.info("Agent validated + session opened: msisdn={} events={}", agentMsisdn, events.size());

		return AgentValidateResponse.builder()
				.authorized(true)
				.events(events)
				.agentSessionId(session.getId())
				.build();
	}

	@Override
	public AgentWhitelistDocument requireAuthorizedSession(String sessionId, String eventId, Checkpoint requestedCheckpoint) {
		AgentSessionDocument session = sessionDao.findActiveById(sessionId)
				.orElseThrow(() -> new AgentSessionInvalidException("Session missing, revoked, or expired"));

		// authorize live against the whitelist for the (eventId, checkpoint) this scan targets
		AgentWhitelistDocument wl = whitelistDao.findActive(eventId, session.getMsisdn())
				.orElseThrow(() -> new AgentSessionInvalidException("Not whitelisted for event " + eventId));
		if (wl.getCheckpoints() == null || !wl.getCheckpoints().contains(requestedCheckpoint)) {
			throw new AgentSessionInvalidException("Not authorized for checkpoint " + requestedCheckpoint);
		}
		return wl;   // carries agent msisdn + endTime + cleanupAt for the entry path
	}
}
