package com.airtel.userprofile.eventpass.dto.response;

import com.airtel.userprofile.eventpass.enums.Checkpoint;
import com.fasterxml.jackson.annotation.JsonInclude;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.Set;

/** One event an agent is authorized to scan, and the checkpoints allowed there. */
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
@JsonInclude(JsonInclude.Include.NON_NULL)
public class AgentEventAccess {

	private String eventId;
	private String eventName;
	private String venue;
	private Set<Checkpoint> checkpoints;
}
