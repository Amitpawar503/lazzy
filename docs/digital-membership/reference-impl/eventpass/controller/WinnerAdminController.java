package com.airtel.userprofile.eventpass.controller;

import com.airtel.core.dto.genericResponse.Response;
import com.airtel.core.enums.Entity;
import com.airtel.core.enums.Operation;
import com.airtel.core.logging.AuditLog;
import com.airtel.userprofile.constants.UserProfileConstants;
import com.airtel.userprofile.eventpass.dto.request.WinnerUpsertRequest;
import com.airtel.userprofile.eventpass.service.WinnerAdminService;
import io.swagger.annotations.Api;
import io.swagger.annotations.ApiOperation;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.RestController;

import jakarta.validation.Valid;
import java.util.Map;

/**
 * API 5 — mark/update a winner on the customer's existing {@code contest_entries} document
 * (admin / engineering only; secured upstream). Sets {@code winnerInfo}; the customer's next QR
 * refresh embeds the new event id.
 */
@RestController
@Api(value = "Event Pass — Winner Admin")
@Slf4j
@RequiredArgsConstructor
public class WinnerAdminController {

	private final WinnerAdminService winnerAdminService;

	@PostMapping("/v1/admin/winners")
	@ApiOperation(value = "Mark/update a winner on the customer's contest entry (writes winnerInfo)")
	@AuditLog(entity = Entity.USERPROFILE, operation = Operation.API, createNewLog = true, publishEvent = false)
	public Response<Map<String, Object>> markWinner(
			@RequestHeader(name = UserProfileConstants.IV_USER) String actor,
			@Valid @RequestBody WinnerUpsertRequest request) {
		long updated = winnerAdminService.markWinner(
				request.getEventId(), request.getMsisdn(), request.getRank(), request.getDrawId(), actor);
		return Response.getSuccessResponse(Map.of(
				"eventId", request.getEventId(),
				"msisdn", request.getMsisdn(),
				"entriesUpdated", updated,
				"status", "WINNER_MARKED"));
	}
}
