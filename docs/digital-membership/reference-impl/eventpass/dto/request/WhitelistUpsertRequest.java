package com.airtel.userprofile.eventpass.dto.request;

import com.airtel.userprofile.eventpass.enums.Checkpoint;
import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonInclude;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotEmpty;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.Set;

/** API 1 — engineering whitelists an agent MSISDN for an event with the checkpoints they may scan. */
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
}
