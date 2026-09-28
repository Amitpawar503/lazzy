package com.airtel.userprofile.eventpass.dto.request;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonInclude;
import jakarta.validation.constraints.NotBlank;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * API 5 — admin marks/updates a winner on the customer's existing {@code contest_entries} document
 * (sets {@code winnerInfo}). {@code eventId} is the contest {@code programId} (Q23). Optional
 * {@code rank}/{@code drawId} let ops record which draw/position produced the win; for a purely
 * manual override they can be omitted.
 */
@Data
@NoArgsConstructor
@JsonIgnoreProperties(ignoreUnknown = true)
@JsonInclude(JsonInclude.Include.NON_NULL)
public class WinnerUpsertRequest {

	@NotBlank
	private String eventId;   // == contest programId

	@NotBlank
	private String msisdn;

	private Integer rank;
	private String drawId;
}
