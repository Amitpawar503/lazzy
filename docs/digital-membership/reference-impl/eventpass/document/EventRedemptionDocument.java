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

/**
 * The exactly-once anchor for event entry / goodie redemption.
 *
 * <p>One row exists per successful redemption. The unique compound index
 * {@code (eventId, msisdn, checkpoint)} is what makes redemption atomic: two concurrent scans of
 * the same QR at the same checkpoint both try to insert this key, exactly one wins, the other gets
 * a {@link org.springframework.dao.DuplicateKeyException} — the same pattern the contest module
 * uses for {@code orderId} uniqueness on {@code contest_entries}.
 *
 * <p>{@code deviceId} stores the customer device of the FIRST redemption, which powers the
 * {@code DUPLICATE_ENTRY} (same device) vs {@code ALREADY_ENTERED_OTHER_DEVICE} (different device)
 * split. {@code scanRequestId} is unique for idempotent retries.
 */
@Data
@Document(collection = "event_redemptions")
@JsonIgnoreProperties(ignoreUnknown = true)
@NoArgsConstructor
@AllArgsConstructor
@Builder
@CompoundIndexes({
		@CompoundIndex(name = "uq_event_msisdn_checkpoint",
				def = "{'eventId': 1, 'msisdn': 1, 'checkpoint': 1}", unique = true)
})
public class EventRedemptionDocument {

	@Id
	private String id;

	private String eventId;
	private String msisdn;
	private Checkpoint checkpoint;

	/** Customer device that generated the QR used for the FIRST successful redemption. */
	private String deviceId;

	/** MSISDN of the agent whose session recorded the redemption. */
	private String redeemedByAgentMsisdn;

	/** Idempotency key from the scanner; unique so a retried scan cannot create a second row. */
	@Indexed(unique = true, sparse = true)
	private String scanRequestId;

	private Instant redeemedAt;
}
