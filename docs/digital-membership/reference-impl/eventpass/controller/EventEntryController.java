package com.airtel.userprofile.eventpass.controller;

import com.airtel.core.dto.genericResponse.Response;
import com.airtel.core.enums.Entity;
import com.airtel.core.enums.Operation;
import com.airtel.core.logging.AuditLog;
import com.airtel.userprofile.eventpass.document.ScanLogDocument;
import com.airtel.userprofile.eventpass.dto.request.EntryScanRequest;
import com.airtel.userprofile.eventpass.dto.response.EntryScanResponse;
import com.airtel.userprofile.eventpass.service.EventEntryService;
import io.swagger.annotations.Api;
import io.swagger.annotations.ApiOperation;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.*;

import jakarta.validation.Valid;
import java.util.List;

/**
 * API 3 — record an entry after scanning (agent mode). The event is taken from the agent session
 * (header {@code X-Agent-Session}); the body carries only qrToken + checkpoint + scanRequestId.
 * Also exposes the admin scan-history API (FR35).
 */
@RestController
@Api(value = "Event Pass — Entry")
@Slf4j
@RequiredArgsConstructor
public class EventEntryController {

	public static final String HEADER_AGENT_SESSION = "X-Agent-Session";

	private final EventEntryService eventEntryService;

	@PostMapping("/v1/entry")
	@ApiOperation(value = "Record entry/goodie redemption after scanning a customer QR")
	@AuditLog(entity = Entity.USERPROFILE, operation = Operation.API, createNewLog = true, publishEvent = false)
	public Response<EntryScanResponse> recordEntry(
			@RequestHeader(name = HEADER_AGENT_SESSION) String agentSessionId,
			@Valid @RequestBody EntryScanRequest request) {
		// Every gate decision (allow/deny) returns 200 with a callback so the scanner always renders.
		return Response.getSuccessResponse(eventEntryService.recordEntry(agentSessionId, request));
	}

	@GetMapping("/v1/admin/scan-history")
	@ApiOperation(value = "Full chronological scan history for a customer (dispute resolution)")
	@AuditLog(entity = Entity.USERPROFILE, operation = Operation.API, createNewLog = true, publishEvent = false)
	public Response<List<ScanLogDocument>> scanHistory(@RequestParam String msisdn) {
		return Response.getSuccessResponse(eventEntryService.scanHistory(msisdn));
	}
}
