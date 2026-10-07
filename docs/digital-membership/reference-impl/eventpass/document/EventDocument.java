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

import java.time.Instant;
import java.util.Set;

/**
 * A live Advantage Club event. {@code active} is flipped false at {@code endTime}; the document
 * then lives for a 30-day dispute window and is auto-deleted by the <b>TTL index</b> on
 * {@code cleanupAt} ({@code = endTime + 30d}).
 *
 * <p>TTL: a Mongo TTL index with {@code expireAfterSeconds = 0} deletes a document once the date in
 * {@code cleanupAt} is in the past. Setting {@code cleanupAt = endTime + 30d} means the row is
 * purged exactly 30 days after the event ends — no cron needed.
 */
@Data
@Document(collection = "event")
@JsonIgnoreProperties(ignoreUnknown = true)
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class EventDocument {

	/** 30-day retention window after an event ends. */
	public static final long CLEANUP_AFTER_DAYS = 30L;

	@Id
	private String eventId;          // e.g. ARTLPPAZK

	private String eventName;
	private String venue;
	private Instant startTime;
	private Instant endTime;
	private boolean active;
	private Set<Checkpoint> checkpointsEnabled;

	/** = endTime + 30d. TTL index deletes the doc once this instant passes. */
	@Indexed(name = "ttl_event_cleanup", expireAfterSeconds = 0)
	private Instant cleanupAt;

	private String createdBy;
	private Instant createdAt;
	private Instant updatedAt;

	public static Instant cleanupFrom(Instant endTime) {
		return endTime == null ? null : endTime.plus(java.time.Duration.ofDays(CLEANUP_AFTER_DAYS));
	}
}
