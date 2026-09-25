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

	/** API 2 — list the events + checkpoints this agent MSISDN may scan. Empty if not an agent. */
	AgentValidateResponse validate(String agentMsisdn);

	/** Open a single-active session bound to (msisdn, eventId, checkpoint); returns the session id. */
	String openSession(String agentMsisdn, String eventId, Checkpoint checkpoint, String deviceInfo);

	/**
	 * Resolve an active session and confirm it is still authorized for the requested checkpoint.
	 * @throws com.airtel.userprofile.eventpass.exception.AgentSessionInvalidException if missing,
	 *         revoked, expired, checkpoint mismatch, or whitelist no longer active.
	 */
	AgentSessionDocument requireAuthorizedSession(String sessionId, Checkpoint requestedCheckpoint);
}
