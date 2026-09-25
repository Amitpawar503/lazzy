package com.airtel.userprofile.eventpass.document;

import com.airtel.userprofile.eventpass.enums.Checkpoint;
import com.airtel.userprofile.eventpass.enums.EntryCallback;
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
 * Append-only audit of every scan attempt (allow AND deny), for dispute resolution and the
 * scan-history API. Indexed by customer msisdn, agent msisdn, and eventId. {@code scanRequestId}
 * is unique so an idempotent retry replays the original decision instead of re-running the chain.
 */
@Data
@Document(collection = "event_scan_logs")
@JsonIgnoreProperties(ignoreUnknown = true)
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class ScanLogDocument {

	@Id
	private String id;

	@Indexed(unique = true, sparse = true)
	private String scanRequestId;

	private String eventId;
	private Checkpoint checkpoint;

	@Indexed
	private String agentMsisdn;

	/** Customer resolved from the token; null when the token could not be resolved (e.g. INVALID_QR). */
	@Indexed
	private String customerMsisdn;

	private String deviceId;
	private EntryCallback callback;
	private String tokenJti;
	private Instant serverTs;
}
