package com.airtel.userprofile.eventpass.document;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;
import org.springframework.data.annotation.Id;
import org.springframework.data.mongodb.core.index.Indexed;
import org.springframework.data.mongodb.core.mapping.Document;

import java.time.Instant;

/**
 * An active agent scanning session, opened by the single {@code GET /v1/agents/validate} call. It
 * is per-agent (not bound to one event/checkpoint) — the agent may scan any (event, checkpoint) it
 * is whitelisted for, checked live per scan. Single-active per msisdn: opening a new session
 * revokes prior non-expired ones. Identity is already proven by the Thanks App login.
 */
@Data
@Document(collection = "event_agent_sessions")
@JsonIgnoreProperties(ignoreUnknown = true)
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class AgentSessionDocument {

	@Id
	private String id;

	@Indexed
	private String msisdn;
	private boolean revoked;
	private Instant createdAt;
	private Instant expiresAt;
	private String deviceInfo;
}
