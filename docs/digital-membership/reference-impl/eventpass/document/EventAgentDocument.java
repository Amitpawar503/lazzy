package com.airtel.userprofile.eventpass.document;

import com.airtel.userprofile.eventpass.enums.Checkpoint;
import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;
import org.springframework.data.annotation.Id;
import org.springframework.data.mongodb.core.index.Indexed;
import org.springframework.data.mongodb.core.mapping.Document;

import java.time.Duration;
import java.time.Instant;
import java.util.Set;

/**
 * The <b>single</b> Event-Pass collection: one document per <b>(agent, event)</b>, keyed by a
 * composite {@code _id} of {@code msisdn::eventId}. Each row carries the <b>agent</b> (which
 * {@code checkpoints} they may scan, {@code active}) <b>and that one event's info</b> (name, venue,
 * window) denormalized onto it — there is no separate {@code event} collection and no embedded agent
 * array. One agent whitelisted for three events is three rows; one event with 50 agents is 50 rows.
 *
 * <p>TTL: {@code cleanupAt = endTime + 30d}; the per-row TTL index auto-deletes each row 30 days
 * after its event ends. When an agent's last row expires, no Event-Pass data about that agent
 * remains — so "an agent with no events for 30 days is removed" falls out for free, with no cron.
 */
@Data
@Document(collection = "event_agent")
@JsonIgnoreProperties(ignoreUnknown = true)
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class EventAgentDocument {

	/** 30-day retention window after an event ends. */
	public static final long CLEANUP_AFTER_DAYS = 30L;

	/** Composite primary key: {@code msisdn::eventId} (one row per agent per event). */
	@Id
	private String id;

	// ---- agent ----
	/** Agent MSISDN. */
	@Indexed(name = "idx_ea_msisdn")
	private String msisdn;

	/** Checkpoints this agent may scan at this event. */
	private Set<Checkpoint> checkpoints;

	/** Soft on/off without deleting the row. */
	private boolean active;

	// ---- the one event this row is about ----
	@Indexed(name = "idx_ea_event")
	private String eventId;          // e.g. ARTLPPAZK
	private String eventName;
	private String venue;
	private Instant startTime;
	private Instant endTime;

	// ---- lifecycle ----
	/** = endTime + 30d. TTL index deletes this row once this instant passes. */
	@Indexed(name = "ttl_event_agent_cleanup", expireAfterSeconds = 0)
	private Instant cleanupAt;

	private String createdBy;
	private Instant createdAt;
	private Instant updatedAt;

	/** Composite id for a (agent, event) pair. */
	public static String idOf(String msisdn, String eventId) {
		return msisdn + "::" + eventId;
	}

	public static Instant cleanupFrom(Instant endTime) {
		return endTime == null ? null : endTime.plus(Duration.ofDays(CLEANUP_AFTER_DAYS));
	}
}
