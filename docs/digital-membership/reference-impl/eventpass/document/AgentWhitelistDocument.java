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
import org.springframework.data.mongodb.core.mapping.Document;

import java.time.Instant;
import java.util.Set;

/**
 * Which events, and which checkpoints, an agent MSISDN may scan. One agent MSISDN can hold many
 * rows (one per event). {@code checkpoints} is the set the agent is authorized for at that event —
 * {@code ENTRY} only, {@code GOODIE} only, or both. Loaded/appended by engineering (admin API 1).
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
	private String msisdn;
	private Set<Checkpoint> checkpoints;
	private boolean active;
	private String createdBy;
	private Instant createdAt;
	private Instant updatedAt;
}
