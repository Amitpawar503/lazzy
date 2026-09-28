package com.airtel.userprofile.eventpass.dao;

import com.airtel.userprofile.eventpass.document.AgentWhitelistDocument;
import com.airtel.userprofile.eventpass.enums.Checkpoint;

import java.util.List;
import java.util.Optional;
import java.util.Set;

public interface AgentWhitelistDao {

	/** Idempotent upsert on (eventId, msisdn) — admin CREATE (POST). */
	AgentWhitelistDocument upsert(AgentWhitelistDocument doc);

	/** All active whitelist rows for an agent — API 2 lists the events/checkpoints they may scan. */
	List<AgentWhitelistDocument> findActiveByMsisdn(String msisdn);

	/** The active row for a specific (eventId, msisdn) — used to authorize a scan. */
	Optional<AgentWhitelistDocument> findActive(String eventId, String msisdn);

	/** READ: a single row (active or not) for (eventId, msisdn). */
	Optional<AgentWhitelistDocument> findOne(String eventId, String msisdn);

	/** READ: all whitelist rows for an event (admin listing). */
	List<AgentWhitelistDocument> findByEvent(String eventId);

	/** UPDATE: set checkpoints and/or active on an existing (eventId, msisdn) row. @return matched count. */
	long update(String eventId, String msisdn, Set<Checkpoint> checkpoints, Boolean active);

	/** DELETE: hard-delete the (eventId, msisdn) row. @return deleted count. */
	long delete(String eventId, String msisdn);
}
