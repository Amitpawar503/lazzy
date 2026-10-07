package com.airtel.userprofile.eventpass.controller;

import com.airtel.core.dto.genericResponse.Response;
import com.airtel.core.enums.Entity;
import com.airtel.core.enums.Operation;
import com.airtel.core.logging.AuditLog;
import com.airtel.userprofile.constants.UserProfileConstants;
import com.airtel.userprofile.eventpass.dto.request.EventUpsertRequest;
import com.airtel.userprofile.eventpass.dto.response.EventResponse;
import com.airtel.userprofile.eventpass.service.EventAdminService;
import io.swagger.annotations.Api;
import io.swagger.annotations.ApiOperation;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.*;

import jakarta.validation.Valid;
import java.util.Map;

/**
 * Admin — create/update, read, and close events (engineering only; secured upstream). The event's
 * {@code endTime} drives the 30-day TTL cleanup of the event and all its per-event data.
 */
@RestController
@Api(value = "Event Pass — Event Admin")
@Slf4j
@RequiredArgsConstructor
public class EventAdminController {

	private final EventAdminService eventAdminService;

	@PostMapping("/v1/admin/events")
	@ApiOperation(value = "Create/update an event (endTime drives the 30-day cleanup)")
	@AuditLog(entity = Entity.USERPROFILE, operation = Operation.API, createNewLog = true, publishEvent = false)
	public Response<EventResponse> upsert(
			@RequestHeader(name = UserProfileConstants.IV_USER) String actor,
			@Valid @RequestBody EventUpsertRequest request) {
		return Response.getSuccessResponse(EventResponse.from(eventAdminService.upsert(request, actor)));
	}

	@GetMapping("/v1/admin/events/{eventId}")
	@ApiOperation(value = "Get an event")
	@AuditLog(entity = Entity.USERPROFILE, operation = Operation.API, createNewLog = true, publishEvent = false)
	public Response<EventResponse> get(@PathVariable String eventId) {
		return Response.getSuccessResponse(EventResponse.from(eventAdminService.get(eventId)));
	}

	@PostMapping("/v1/admin/events/{eventId}/close")
	@ApiOperation(value = "Close an event (active=false); TTL still purges at endTime+30d")
	@AuditLog(entity = Entity.USERPROFILE, operation = Operation.API, createNewLog = true, publishEvent = false)
	public Response<Map<String, Object>> close(
			@RequestHeader(name = UserProfileConstants.IV_USER) String actor,
			@PathVariable String eventId) {
		eventAdminService.close(eventId, actor);
		return Response.getSuccessResponse(Map.of("eventId", eventId, "status", "CLOSED"));
	}
}
