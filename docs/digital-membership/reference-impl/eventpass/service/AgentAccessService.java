package com.airtel.userprofile.eventpass.service;

import com.airtel.userprofile.eventpass.document.EventAgentDocument;
import com.airtel.userprofile.eventpass.dto.request.WhitelistUpsertRequest;
import com.airtel.userprofile.eventpass.dto.response.AgentValidateResponse;
import com.airtel.userprofile.eventpass.enums.Checkpoint;

import java.util.List;

/**
 * Agent whitelist CRUD + per-scan authorization (no session — app login is the auth). Every row is
 * one (agent, event) document in the single {@code event_agent} collection; there is no separate
 * event or session collection.
 */
public interface AgentAccessService {

	// ---- Whitelist admin CRUD (API 1), each a (agent, event) row ----

	/** CREATE (POST) — idempotently whitelist an agent MSISDN for an event with its checkpoints. */
	EventAgentDocument upsertWhitelist(WhitelistUpsertRequest request, String actor);

	/** READ (GET) — rows for an event (all, or one when msisdn is given). */
	List<EventAgentDocument> getWhitelist(String eventId, String msisdn);

	/** UPDATE (PUT) — change checkpoints and/or active on an existing row. @throws IllegalArgumentException if absent. */
	EventAgentDocument updateWhitelist(WhitelistUpsertRequest request, String actor);

	/** DELETE — remove the (eventId, msisdn) row. @throws IllegalArgumentException if absent. */
	void deleteWhitelist(String eventId, String msisdn, String actor);

	/**
	 * API 2 — pure read: the events + checkpoints this agent MSISDN may scan, enriched with event
	 * name/venue. {@code authorized=false} with no events if the MSISDN is not an event agent. No session.
	 */
	AgentValidateResponse validate(String agentMsisdn);

	/**
	 * Confirm the (already app-authenticated) agent is whitelisted for the requested
	 * (eventId, checkpoint) — checked live against the {@code event_agent} row on every scan.
	 * @return the authorizing row (carries {@code endTime} and {@code cleanupAt} for the entry path).
	 * @throws com.airtel.userprofile.eventpass.exception.AgentSessionInvalidException if the agent
	 *         is not whitelisted for that event/checkpoint.
	 */
	EventAgentDocument requireAuthorized(String agentMsisdn, String eventId, Checkpoint requestedCheckpoint);
}
