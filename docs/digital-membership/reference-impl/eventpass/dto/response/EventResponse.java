package com.airtel.userprofile.eventpass.dto.response;

import com.airtel.userprofile.eventpass.document.EventDocument;
import com.airtel.userprofile.eventpass.enums.Checkpoint;
import com.fasterxml.jackson.annotation.JsonInclude;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.Instant;
import java.util.Set;

/** Admin event view, including the computed {@code cleanupAt} (when the TTL will purge it). */
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
@JsonInclude(JsonInclude.Include.NON_NULL)
public class EventResponse {

	private String eventId;
	private String eventName;
	private String venue;
	private Instant startTime;
	private Instant endTime;
	private boolean active;
	private Set<Checkpoint> checkpointsEnabled;
	private Instant cleanupAt;

	public static EventResponse from(EventDocument d) {
		return EventResponse.builder()
				.eventId(d.getEventId())
				.eventName(d.getEventName())
				.venue(d.getVenue())
				.startTime(d.getStartTime())
				.endTime(d.getEndTime())
				.active(d.isActive())
				.checkpointsEnabled(d.getCheckpointsEnabled())
				.cleanupAt(d.getCleanupAt())
				.build();
	}
}
