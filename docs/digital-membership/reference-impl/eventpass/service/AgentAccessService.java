package com.airtel.userprofile.eventpass.service;

import com.airtel.userprofile.eventpass.document.AgentSessionDocument;
import com.airtel.userprofile.eventpass.document.AgentWhitelistDocument;
import com.airtel.userprofile.eventpass.dto.request.WhitelistUpsertRequest;
import com.airtel.userprofile.eventpass.dto.response.AgentValidateResponse;
import com.airtel.userprofile.eventpass.enums.Checkpoint;

/** Agent whitelist validation + scanning-session lifecycle (all inside the User Profile Service). */
public interface AgentAccessService {

	/** API 1 (admin) — idempotently whitelist an agent MSISDN for an event with its checkpoints. */
	AgentWhitelistDocument upsertWhitelist(WhitelistUpsertRequest request, String actor);

	/**
	 * API 2 (single call) — validate the agent and **open a single-active session** in one shot.
	 * Returns the events + checkpoints the agent may scan plus an {@code agentSessionId}; empty /
	 * {@code authorized=false} (and no session) if the MSISDN is not an event agent.
	 */
	AgentValidateResponse validate(String agentMsisdn, String deviceInfo);

	/**
	 * Resolve an active session and confirm the agent is (still) whitelisted for the requested
	 * (eventId, checkpoint) — checked live against the whitelist, since the session is per-agent.
	 * @throws com.airtel.userprofile.eventpass.exception.AgentSessionInvalidException if missing,
	 *         revoked, expired, or not whitelisted for that event/checkpoint.
	 */
	AgentSessionDocument requireAuthorizedSession(String sessionId, String eventId, Checkpoint requestedCheckpoint);
}
