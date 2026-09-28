package com.airtel.userprofile.eventpass.controller;

import com.airtel.core.dto.genericResponse.Response;
import com.airtel.core.enums.Entity;
import com.airtel.core.enums.Operation;
import com.airtel.core.logging.AuditLog;
import com.airtel.userprofile.constants.UserProfileConstants;
import com.airtel.userprofile.eventpass.dto.request.WhitelistUpsertRequest;
import com.airtel.userprofile.eventpass.dto.response.AgentValidateResponse;
import com.airtel.userprofile.eventpass.dto.response.AgentWhitelistResponse;
import com.airtel.userprofile.eventpass.service.AgentAccessService;
import io.swagger.annotations.Api;
import io.swagger.annotations.ApiOperation;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.*;

import jakarta.validation.Valid;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

/**
 * API 1 (admin whitelist) + API 2 (single agent validate — which also opens the scanning session).
 * No OTP, no microsite — the agent uses the Thanks App in agent mode, so {@code IV_USER} is the
 * authenticated agent MSISDN.
 */
@RestController
@Api(value = "Event Pass — Agent")
@Slf4j
@RequiredArgsConstructor
public class AgentController {

	private final AgentAccessService agentAccessService;

	// ---- API 1: admin whitelist CRUD (engineering only; secured upstream) ----

	// CREATE
	@PostMapping("/v1/agents/whitelist")
	@ApiOperation(value = "Create/whitelist an agent MSISDN for an event with checkpoints (admin)")
	@AuditLog(entity = Entity.USERPROFILE, operation = Operation.API, createNewLog = true, publishEvent = false)
	public Response<Map<String, Object>> createWhitelist(
			@RequestHeader(name = UserProfileConstants.IV_USER) String actor,
			@Valid @RequestBody WhitelistUpsertRequest request) {
		var saved = agentAccessService.upsertWhitelist(request, actor);
		return Response.getSuccessResponse(Map.of("whitelistId", saved.getId(), "status", "UPSERTED"));
	}

	// READ (one when msisdn given, else all rows for the event)
	@GetMapping("/v1/agents/whitelist")
	@ApiOperation(value = "Get whitelist row(s) for an event (all rows, or one when msisdn is given)")
	@AuditLog(entity = Entity.USERPROFILE, operation = Operation.API, createNewLog = true, publishEvent = false)
	public Response<List<AgentWhitelistResponse>> getWhitelist(
			@RequestHeader(name = UserProfileConstants.IV_USER) String actor,
			@RequestParam String eventId,
			@RequestParam(required = false) String msisdn) {
		List<AgentWhitelistResponse> rows = agentAccessService.getWhitelist(eventId, msisdn).stream()
				.map(AgentWhitelistResponse::from).collect(Collectors.toList());
		return Response.getSuccessResponse(rows);
	}

	// UPDATE
	@PutMapping("/v1/agents/whitelist")
	@ApiOperation(value = "Update checkpoints and/or active flag on an existing whitelist row (admin)")
	@AuditLog(entity = Entity.USERPROFILE, operation = Operation.API, createNewLog = true, publishEvent = false)
	public Response<AgentWhitelistResponse> updateWhitelist(
			@RequestHeader(name = UserProfileConstants.IV_USER) String actor,
			@Valid @RequestBody WhitelistUpsertRequest request) {
		return Response.getSuccessResponse(
				AgentWhitelistResponse.from(agentAccessService.updateWhitelist(request, actor)));
	}

	// DELETE
	@DeleteMapping("/v1/agents/whitelist")
	@ApiOperation(value = "Delete a whitelist row for (eventId, msisdn) (admin)")
	@AuditLog(entity = Entity.USERPROFILE, operation = Operation.API, createNewLog = true, publishEvent = false)
	public Response<Map<String, Object>> deleteWhitelist(
			@RequestHeader(name = UserProfileConstants.IV_USER) String actor,
			@RequestParam String eventId,
			@RequestParam String msisdn) {
		agentAccessService.deleteWhitelist(eventId, msisdn, actor);
		return Response.getSuccessResponse(Map.of("eventId", eventId, "msisdn", msisdn, "status", "DELETED"));
	}

	// ---- API 2: validate agent + open session (single call) ----
	@GetMapping("/v1/agents/validate")
	@ApiOperation(value = "Validate the agent and open a scanning session; returns authorized events + checkpoints + agentSessionId")
	@AuditLog(entity = Entity.USERPROFILE, operation = Operation.API, createNewLog = true, publishEvent = false)
	public Response<AgentValidateResponse> validate(
			@RequestHeader(name = UserProfileConstants.IV_USER) String agentMsisdn,
			@RequestHeader(name = "User-Agent", required = false) String userAgent) {
		return Response.getSuccessResponse(agentAccessService.validate(agentMsisdn, userAgent));
	}
}
