package com.airtel.userprofile.eventpass.dao;

import com.airtel.userprofile.eventpass.document.AgentSessionDocument;

import java.util.Optional;

public interface AgentSessionDao {

	/** Revoke all non-revoked sessions for a msisdn (single-active), then persist the new one. */
	AgentSessionDocument openExclusive(AgentSessionDocument session);

	/** Active (not revoked, not expired) session by id — used to authorize a scan. */
	Optional<AgentSessionDocument> findActiveById(String sessionId);
}
