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
	public AgentValidateResponse validate(String agentMsisdn) {
		List<AgentWhitelistDocument> rows = whitelistDao.findActiveByMsisdn(agentMsisdn);
		if (rows.isEmpty()) {
			return AgentValidateResponse.builder().authorized(false).build();  // no event data leaked
		}
		List<AgentEventAccess> events = rows.stream()
				.map(r -> AgentEventAccess.builder()
						.eventId(r.getEventId())
						.checkpoints(r.getCheckpoints())
						// eventName/venue enriched from event/program metadata where available
						.build())
				.collect(Collectors.toList());
		return AgentValidateResponse.builder().authorized(true).events(events).build();
	}

	@Override
	public String openSession(String agentMsisdn, String eventId, Checkpoint checkpoint, String deviceInfo) {
		AgentWhitelistDocument wl = whitelistDao.findActive(eventId, agentMsisdn)
				.orElseThrow(() -> new AgentSessionInvalidException("Not whitelisted for this event"));
		if (wl.getCheckpoints() == null || !wl.getCheckpoints().contains(checkpoint)) {
			throw new AgentSessionInvalidException("Not authorized for checkpoint " + checkpoint);
		}
		Instant now = Instant.now();
		AgentSessionDocument session = AgentSessionDocument.builder()
				.id(UUID.randomUUID().toString())
				.msisdn(agentMsisdn)
				.eventId(eventId)
				.checkpoint(checkpoint)
				.revoked(false)
				.createdAt(now)
				.expiresAt(now.plusSeconds(props.getAgentSessionTtlSeconds()))
				.deviceInfo(deviceInfo)
				.build();
		sessionDao.openExclusive(session);   // revokes prior sessions for this msisdn
		log.info("Agent session opened: msisdn={} event={} checkpoint={}", agentMsisdn, eventId, checkpoint);
		return session.getId();
	}

	@Override
	public AgentSessionDocument requireAuthorizedSession(String sessionId, Checkpoint requestedCheckpoint) {
		AgentSessionDocument session = sessionDao.findActiveById(sessionId)
				.orElseThrow(() -> new AgentSessionInvalidException("Session missing, revoked, or expired"));

		if (requestedCheckpoint != null && session.getCheckpoint() != requestedCheckpoint) {
			throw new AgentSessionInvalidException("Checkpoint mismatch for session");
		}
		// re-check the whitelist is still active for this (event, msisdn) and allows the checkpoint
		AgentWhitelistDocument wl = whitelistDao.findActive(session.getEventId(), session.getMsisdn())
				.orElseThrow(() -> new AgentSessionInvalidException("Whitelist revoked"));
		if (wl.getCheckpoints() == null || !wl.getCheckpoints().contains(session.getCheckpoint())) {
			throw new AgentSessionInvalidException("Checkpoint authorization revoked");
		}
		return session;
	}
}
