package com.airtel.userprofile.eventpass.dto.request;

import com.airtel.userprofile.eventpass.enums.Checkpoint;
import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonInclude;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotEmpty;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.Instant;
import java.util.Set;

/**
 * API 1 — whitelist an agent MSISDN for an event with the checkpoints they may scan. Each row is
 * one (agent, event) pair in the single {@code event_agent} collection.
 *
 * <p>The event fields ({@code eventName}, {@code venue}, {@code startTime}, {@code endTime}) are
 * supplied the <b>first</b> time an event is whitelisted (they set the row's info and, via
 * {@code endTime}, the TTL); on later agents for the same event they may be omitted and are
 * inherited from the existing rows. {@code endTime} must be known (given or inherited) so the 30-day
 * cleanup can be computed.
 */
@Data
@NoArgsConstructor
@JsonIgnoreProperties(ignoreUnknown = true)
@JsonInclude(JsonInclude.Include.NON_NULL)
public class WhitelistUpsertRequest {

	@NotBlank
	private String eventId;

	@NotBlank
	private String msisdn;

	@NotEmpty
	private Set<Checkpoint> checkpoints;

	/** Optional on create (defaults to true). On UPDATE (PUT) it toggles the row active/inactive. */
	private Boolean active;

	// ---- event info (first whitelist of the event; inherited afterwards) ----
	private String eventName;
	private String venue;
	private Instant startTime;
	private Instant endTime;
}
