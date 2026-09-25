package com.airtel.userprofile.eventpass.dao;

import com.airtel.userprofile.eventpass.document.AgentWhitelistDocument;

import java.util.List;
import java.util.Optional;

public interface AgentWhitelistDao {

	/** Idempotent upsert on (eventId, msisdn) — admin API 1. */
	AgentWhitelistDocument upsert(AgentWhitelistDocument doc);

	/** All active whitelist rows for an agent — API 2 lists the events/checkpoints they may scan. */
	List<AgentWhitelistDocument> findActiveByMsisdn(String msisdn);

	/** The active row for a specific (eventId, msisdn) — used to authorize a scan. */
	Optional<AgentWhitelistDocument> findActive(String eventId, String msisdn);
}
