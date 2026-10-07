package com.airtel.userprofile.eventpass.service;

import com.airtel.userprofile.eventpass.document.AgentSessionDocument;
import com.airtel.userprofile.eventpass.document.AgentWhitelistDocument;
import com.airtel.userprofile.eventpass.dto.request.WhitelistUpsertRequest;
import com.airtel.userprofile.eventpass.dto.response.AgentValidateResponse;
import com.airtel.userprofile.eventpass.enums.Checkpoint;

/** Agent whitelist validation + scanning-session lifecycle (all inside the User Profile Service). */
public interface AgentAccessService {

	// ---- Whitelist admin CRUD (API 1) ----

	/** CREATE (POST) — idempotently whitelist an agent MSISDN for an event with its checkpoints. */
	AgentWhitelistDocument upsertWhitelist(WhitelistUpsertRequest request, String actor);

	/** READ (GET) — one whitelist row for (eventId, msisdn), or all rows for an event when msisdn is null. */
	java.util.List<AgentWhitelistDocument> getWhitelist(String eventId, String msisdn);

	/** UPDATE (PUT) — change checkpoints and/or active on an existing row. @throws IllegalArgumentException if absent. */
	AgentWhitelistDocument updateWhitelist(WhitelistUpsertRequest request, String actor);

	/** DELETE — remove the (eventId, msisdn) row. @throws IllegalArgumentException if absent. */
	void deleteWhitelist(String eventId, String msisdn, String actor);

	/**
	 * API 2 (single call) — validate the agent and **open a single-active session** in one shot.
	 * Returns the events + checkpoints the agent may scan plus an {@code agentSessionId}; empty /
	 * {@code authorized=false} (and no session) if the MSISDN is not an event agent.
	 */
	AgentValidateResponse validate(String agentMsisdn, String deviceInfo);

	/**
	 * Resolve an active session and confirm the agent is (still) whitelisted for the requested
	 * (eventId, checkpoint) — checked live against the whitelist, since the session is per-agent.
	 * @return the authorizing whitelist relation (carries agent msisdn, endTime and cleanupAt).
	 * @throws com.airtel.userprofile.eventpass.exception.AgentSessionInvalidException if missing,
	 *         revoked, expired, or not whitelisted for that event/checkpoint.
	 */
	AgentWhitelistDocument requireAuthorizedSession(String sessionId, String eventId, Checkpoint requestedCheckpoint);
}
