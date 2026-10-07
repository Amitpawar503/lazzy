package com.airtel.userprofile.eventpass.dto.request;

import com.airtel.userprofile.eventpass.enums.Checkpoint;
import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonInclude;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.Instant;
import java.util.Set;

/** Admin — create/update an event. {@code endTime} drives the 30-day cleanup (TTL). */
@Data
@NoArgsConstructor
@JsonIgnoreProperties(ignoreUnknown = true)
@JsonInclude(JsonInclude.Include.NON_NULL)
public class EventUpsertRequest {

	@NotBlank
	private String eventId;

	@NotBlank
	private String eventName;

	private String venue;

	@NotNull
	private Instant startTime;

	@NotNull
	private Instant endTime;

	private Set<Checkpoint> checkpointsEnabled;
}
