package com.airtel.userprofile.eventpass.controller;

import com.airtel.core.dto.genericResponse.Response;
import com.airtel.core.enums.Entity;
import com.airtel.core.enums.Operation;
import com.airtel.core.logging.AuditLog;
import com.airtel.userprofile.constants.UserProfileConstants;
import com.airtel.userprofile.eventpass.dto.request.WhitelistUpsertRequest;
import com.airtel.userprofile.eventpass.dto.response.AgentValidateResponse;
import com.airtel.userprofile.eventpass.enums.Checkpoint;
import com.airtel.userprofile.eventpass.service.AgentAccessService;
import io.swagger.annotations.Api;
import io.swagger.annotations.ApiOperation;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.*;

import jakarta.validation.Valid;
import java.util.Map;

/**
 * API 1 (admin whitelist) + API 2 (agent validate / open session). No OTP, no microsite — the
 * agent uses the Thanks App in agent mode, so {@code IV_USER} is the authenticated agent MSISDN.
 */
@RestController
@Api(value = "Event Pass — Agent")
@Slf4j
@RequiredArgsConstructor
public class AgentController {

	private final AgentAccessService agentAccessService;

	// ---- API 1: admin whitelist (engineering only; secured upstream) ----
	@PostMapping("/v1/agents/whitelist")
	@ApiOperation(value = "Whitelist an agent MSISDN for an event with checkpoints (admin)")
	@AuditLog(entity = Entity.USERPROFILE, operation = Operation.API, createNewLog = true, publishEvent = false)
	public Response<Map<String, Object>> whitelist(
			@RequestHeader(name = UserProfileConstants.IV_USER) String actor,
			@Valid @RequestBody WhitelistUpsertRequest request) {
		var saved = agentAccessService.upsertWhitelist(request, actor);
		return Response.getSuccessResponse(Map.of("whitelistId", saved.getId(), "status", "UPSERTED"));
	}

	// ---- API 2: validate agent, list authorized events + checkpoints ----
	@GetMapping("/v1/agents/validate")
	@ApiOperation(value = "List the events + checkpoints this agent may scan")
	@AuditLog(entity = Entity.USERPROFILE, operation = Operation.API, createNewLog = true, publishEvent = false)
	public Response<AgentValidateResponse> validate(
			@RequestHeader(name = UserProfileConstants.IV_USER) String agentMsisdn) {
		return Response.getSuccessResponse(agentAccessService.validate(agentMsisdn));
	}

	// ---- API 2b: open a scanning session for a chosen event + checkpoint ----
	@PostMapping("/v1/agents/session")
	@ApiOperation(value = "Open a single-active scanning session (event + checkpoint)")
	@AuditLog(entity = Entity.USERPROFILE, operation = Operation.API, createNewLog = true, publishEvent = false)
	public Response<Map<String, Object>> openSession(
			@RequestHeader(name = UserProfileConstants.IV_USER) String agentMsisdn,
			@RequestParam String eventId,
			@RequestParam Checkpoint checkpoint,
			@RequestHeader(name = "User-Agent", required = false) String userAgent) {
		String sessionId = agentAccessService.openSession(agentMsisdn, eventId, checkpoint, userAgent);
		return Response.getSuccessResponse(Map.of("agentSessionId", sessionId));
	}
}
