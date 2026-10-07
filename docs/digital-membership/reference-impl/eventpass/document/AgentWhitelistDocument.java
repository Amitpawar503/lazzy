package com.airtel.userprofile.eventpass.document;

import com.airtel.userprofile.eventpass.enums.Checkpoint;
import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;
import org.springframework.data.annotation.Id;
import org.springframework.data.mongodb.core.index.CompoundIndex;
import org.springframework.data.mongodb.core.index.CompoundIndexes;
import org.springframework.data.mongodb.core.index.Indexed;
import org.springframework.data.mongodb.core.mapping.Document;

import java.time.Instant;
import java.util.Set;

/**
 * The <b>agent ↔ event relation</b> (one doc per {@code (agent, event)}) — the recommended shape
 * over an embedded event list, because each row can be TTL-expired independently. Holds which
 * {@code checkpoints} the agent is authorized for at that event. One agent MSISDN holds many rows.
 *
 * <p>{@code endTime}/{@code cleanupAt} are copied from the event at whitelist time; the TTL index on
 * {@code cleanupAt} ({@code = endTime + 30d}) auto-deletes the relation 30 days after the event ends.
 * When an agent's last relation row expires, the agent has no Event-Pass data left in Mongo.
 */
@Data
@Document(collection = "event_agent_whitelist")
@JsonIgnoreProperties(ignoreUnknown = true)
@NoArgsConstructor
@AllArgsConstructor
@Builder
@CompoundIndexes({
		@CompoundIndex(name = "uq_event_agent", def = "{'eventId': 1, 'msisdn': 1}", unique = true)
})
public class AgentWhitelistDocument {

	@Id
	private String id;

	private String eventId;
	private String msisdn;              // agent MSISDN
	private Set<Checkpoint> checkpoints;
	private boolean active;

	private Instant endTime;            // copied from the event (for cleanup alignment)

	/** = endTime + 30d. TTL index purges the relation 30 days after the event ends. */
	@Indexed(name = "ttl_whitelist_cleanup", expireAfterSeconds = 0)
	private Instant cleanupAt;

	private String createdBy;
	private Instant createdAt;
	private Instant updatedAt;
}
