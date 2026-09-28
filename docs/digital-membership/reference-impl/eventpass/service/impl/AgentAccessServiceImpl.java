package com.airtel.userprofile.eventpass.service.impl;

import com.airtel.userprofile.eventpass.config.EventPassProperties;
import com.airtel.userprofile.eventpass.dao.AgentSessionDao;
import com.airtel.userprofile.eventpass.dao.AgentWhitelistDao;
import com.airtel.userprofile.eventpass.document.AgentSessionDocument;
import com.airtel.userprofile.eventpass.document.AgentWhitelistDocument;
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
	private final EventPassProperties props;

	@Override
	public AgentWhitelistDocument upsertWhitelist(WhitelistUpsertRequest request, String actor) {
		AgentWhitelistDocument doc = AgentWhitelistDocument.builder()
				.eventId(request.getEventId())
				.msisdn(request.getMsisdn())
				.checkpoints(request.getCheckpoints())
				.active(true)
				.createdBy(actor)
				.build();
		AgentWhitelistDocument saved = whitelistDao.upsert(doc);
		log.info("Whitelist upserted by {}: event={} msisdn={} checkpoints={}",
				actor, request.getEventId(), request.getMsisdn(), request.getCheckpoints());
		return saved;
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
	public AgentSessionDocument requireAuthorizedSession(String sessionId, String eventId, Checkpoint requestedCheckpoint) {
		AgentSessionDocument session = sessionDao.findActiveById(sessionId)
				.orElseThrow(() -> new AgentSessionInvalidException("Session missing, revoked, or expired"));

		// authorize live against the whitelist for the (eventId, checkpoint) this scan targets
		AgentWhitelistDocument wl = whitelistDao.findActive(eventId, session.getMsisdn())
				.orElseThrow(() -> new AgentSessionInvalidException("Not whitelisted for event " + eventId));
		if (wl.getCheckpoints() == null || !wl.getCheckpoints().contains(requestedCheckpoint)) {
			throw new AgentSessionInvalidException("Not authorized for checkpoint " + requestedCheckpoint);
		}
		return session;
	}
}
