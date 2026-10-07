package com.airtel.userprofile.eventpass.dto.response;

import com.airtel.userprofile.eventpass.document.EventAgentDocument;
import com.airtel.userprofile.eventpass.enums.Checkpoint;
import com.fasterxml.jackson.annotation.JsonInclude;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.Instant;
import java.util.Set;

/** DTO for whitelist read/update responses — never exposes the raw Mongo document to the API. */
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
@JsonInclude(JsonInclude.Include.NON_NULL)
public class AgentWhitelistResponse {

	private String eventId;
	private String eventName;
	private String venue;
	private String msisdn;
	private Set<Checkpoint> checkpoints;
	private boolean active;
	private Instant updatedAt;

	public static AgentWhitelistResponse from(EventAgentDocument d) {
		return AgentWhitelistResponse.builder()
				.eventId(d.getEventId())
				.eventName(d.getEventName())
				.venue(d.getVenue())
				.msisdn(d.getMsisdn())
				.checkpoints(d.getCheckpoints())
				.active(d.isActive())
				.updatedAt(d.getUpdatedAt())
				.build();
	}
}
