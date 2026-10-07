package com.airtel.userprofile.eventpass.service.impl;

import com.airtel.userprofile.eventpass.dao.EventAgentDao;
import com.airtel.userprofile.eventpass.document.EventAgentDocument;
import com.airtel.userprofile.eventpass.dto.request.WhitelistUpsertRequest;
import com.airtel.userprofile.eventpass.dto.response.AgentEventAccess;
import com.airtel.userprofile.eventpass.dto.response.AgentValidateResponse;
import com.airtel.userprofile.eventpass.enums.Checkpoint;
import com.airtel.userprofile.eventpass.exception.AgentSessionInvalidException;
import com.airtel.userprofile.eventpass.service.AgentAccessService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.time.Instant;
import java.util.List;
import java.util.stream.Collectors;

/**
 * Agent whitelist CRUD + per-scan authorization. No session store: the agent scans inside the
 * Thanks App (already authenticated as {@code IV_USER}), so each scan is authorized live against
 * the {@code event_agent} row by {@code (agentMsisdn, eventId, checkpoint)}.
 *
 * <p>The whitelist is the single {@code event_agent} collection — one row per (agent, event),
 * carrying the agent + that event's info. The row is purged by its own TTL ({@code endTime + 30d}).
 */
@Service
@Slf4j
@RequiredArgsConstructor
public class AgentAccessServiceImpl implements AgentAccessService {

	private final EventAgentDao eventAgentDao;

	@Override
	public EventAgentDocument upsertWhitelist(WhitelistUpsertRequest request, String actor) {
		// Event info is set on the first whitelist of the event, then inherited by later agents.
		EventAgentDocument existing = eventAgentDao.findAnyByEvent(request.getEventId()).orElse(null);

		String eventName = firstNonNull(request.getEventName(), existing == null ? null : existing.getEventName());
		String venue     = firstNonNull(request.getVenue(),     existing == null ? null : existing.getVenue());
		Instant startTime = firstNonNull(request.getStartTime(), existing == null ? null : existing.getStartTime());
		Instant endTime   = firstNonNull(request.getEndTime(),   existing == null ? null : existing.getEndTime());

		if (endTime == null) {
			throw new IllegalArgumentException(
					"endTime is required the first time event " + request.getEventId() + " is whitelisted (drives 30-day cleanup)");
		}

		Instant now = Instant.now();
		EventAgentDocument doc = EventAgentDocument.builder()
				.msisdn(request.getMsisdn())
				.checkpoints(request.getCheckpoints())
				.active(request.getActive() == null || request.getActive())   // defaults active
				.eventId(request.getEventId())
				.eventName(eventName)
				.venue(venue)
				.startTime(startTime)
				.endTime(endTime)
				.createdBy(actor)
				.build();
		EventAgentDocument saved = eventAgentDao.upsert(doc);   // sets id + cleanupAt = endTime + 30d
		log.info("Whitelist created/upserted by {}: event={} msisdn={} checkpoints={} cleanupAt={}",
				actor, request.getEventId(), request.getMsisdn(), request.getCheckpoints(), saved.getCleanupAt());
		return saved;
	}

	@Override
	public List<EventAgentDocument> getWhitelist(String eventId, String msisdn) {
		if (msisdn != null && !msisdn.isBlank()) {
			EventAgentDocument row = eventAgentDao.findByEventAndAgent(eventId, msisdn)
					.orElseThrow(() -> new IllegalArgumentException(
							"No whitelist row for event " + eventId + " / msisdn " + msisdn));
			return List.of(row);
		}
		return eventAgentDao.findByEvent(eventId);
	}

	@Override
	public EventAgentDocument updateWhitelist(WhitelistUpsertRequest request, String actor) {
		long matched = eventAgentDao.update(
				request.getEventId(), request.getMsisdn(), request.getCheckpoints(), request.getActive());
		if (matched == 0) {
			throw new IllegalArgumentException(
					"No whitelist row to update for event " + request.getEventId() + " / msisdn " + request.getMsisdn());
		}
		log.info("Whitelist updated by {}: event={} msisdn={} checkpoints={} active={}",
				actor, request.getEventId(), request.getMsisdn(), request.getCheckpoints(), request.getActive());
		return eventAgentDao.findByEventAndAgent(request.getEventId(), request.getMsisdn()).orElseThrow();
	}

	@Override
	public void deleteWhitelist(String eventId, String msisdn, String actor) {
		long deleted = eventAgentDao.delete(eventId, msisdn);
		if (deleted == 0) {
			throw new IllegalArgumentException(
					"No whitelist row to delete for event " + eventId + " / msisdn " + msisdn);
		}
		log.info("Whitelist deleted by {}: event={} msisdn={}", actor, eventId, msisdn);
	}

	@Override
	public AgentValidateResponse validate(String agentMsisdn) {
		List<EventAgentDocument> rows = eventAgentDao.findActiveByAgent(agentMsisdn);
		if (rows.isEmpty()) {
			return AgentValidateResponse.builder().authorized(false).build();  // no event data leaked
		}
		List<AgentEventAccess> events = rows.stream()
				.map(r -> AgentEventAccess.builder()
						.eventId(r.getEventId())
						.eventName(r.getEventName())
						.venue(r.getVenue())
						.checkpoints(r.getCheckpoints())
						.build())
				.collect(Collectors.toList());
		return AgentValidateResponse.builder().authorized(true).events(events).build();
	}

	@Override
	public EventAgentDocument requireAuthorized(String agentMsisdn, String eventId, Checkpoint requestedCheckpoint) {
		EventAgentDocument row = eventAgentDao.findActive(eventId, agentMsisdn)
				.orElseThrow(() -> new AgentSessionInvalidException(
						"Agent " + agentMsisdn + " not whitelisted for event " + eventId));
		if (row.getCheckpoints() == null || !row.getCheckpoints().contains(requestedCheckpoint)) {
			throw new AgentSessionInvalidException("Not authorized for checkpoint " + requestedCheckpoint);
		}
		return row;   // carries endTime + cleanupAt for the entry path
	}

	private static <T> T firstNonNull(T a, T b) {
		return a != null ? a : b;
	}
}
