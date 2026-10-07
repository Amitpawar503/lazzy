package com.airtel.userprofile.eventpass.dao;

import com.airtel.userprofile.eventpass.document.EventAgentDocument;
import com.airtel.userprofile.eventpass.enums.Checkpoint;

import java.util.List;
import java.util.Optional;
import java.util.Set;

/**
 * The single {@code event_agent} collection — one row per (agent, event), keyed by the composite
 * {@code _id = msisdn::eventId}. All whitelist CRUD (API 1), the agent-centric lookups (API 2 +
 * per-scan authorization), and event-info reuse are served from here; there is no event collection.
 */
public interface EventAgentDao {

	/** Idempotent create/replace of the (agent, event) row (by composite id). */
	EventAgentDocument upsert(EventAgentDocument doc);

	/** The row for a specific (eventId, msisdn), active or not. */
	Optional<EventAgentDocument> findByEventAndAgent(String eventId, String msisdn);

	/** The <b>active</b> row for (eventId, msisdn) — used to authorize a scan. */
	Optional<EventAgentDocument> findActive(String eventId, String msisdn);

	/** All rows for an event (admin listing of its agents). */
	List<EventAgentDocument> findByEvent(String eventId);

	/** Any one existing row for an event — used to inherit event info when adding another agent. */
	Optional<EventAgentDocument> findAnyByEvent(String eventId);

	/** All <b>active</b> rows for an agent — API 2 lists the events/checkpoints they may scan. */
	List<EventAgentDocument> findActiveByAgent(String msisdn);

	/** UPDATE: set checkpoints and/or active on an existing (eventId, msisdn) row. @return matched. */
	long update(String eventId, String msisdn, Set<Checkpoint> checkpoints, Boolean active);

	/** DELETE: hard-delete the (eventId, msisdn) row. @return deleted count. */
	long delete(String eventId, String msisdn);
}
