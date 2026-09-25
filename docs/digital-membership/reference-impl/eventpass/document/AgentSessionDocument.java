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

/**
 * An active agent scanning session, bound to (msisdn, eventId, checkpoint). Single-active per
 * msisdn: opening a new session revokes prior non-expired ones (mirrors the "one session per
 * number" rule). Identity is already proven by the Thanks App login; this only carries scanning
 * authority + the selected checkpoint.
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
	private String eventId;
	private Checkpoint checkpoint;
	private boolean revoked;
	private Instant createdAt;
	private Instant expiresAt;
	private String deviceInfo;
}
