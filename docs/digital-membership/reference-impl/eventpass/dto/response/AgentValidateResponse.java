package com.airtel.userprofile.eventpass.dto.response;

import com.fasterxml.jackson.annotation.JsonInclude;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;

/**
 * API 2 response — the events + checkpoints this agent MSISDN may scan. Empty {@code events}
 * means "not an event agent" (no data leaked). {@code agentSessionId} is issued once the agent
 * picks an event + checkpoint (single-active per msisdn).
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
@JsonInclude(JsonInclude.Include.NON_NULL)
public class AgentValidateResponse {

	private boolean authorized;
	private List<AgentEventAccess> events;
	private String agentSessionId;
}
