package com.airtel.userprofile.eventpass.controller;

import com.airtel.core.dto.genericResponse.Response;
import com.airtel.core.enums.Entity;
import com.airtel.core.enums.Operation;
import com.airtel.core.logging.AuditLog;
import com.airtel.userprofile.constants.UserProfileConstants;
import com.airtel.userprofile.eventpass.dto.request.QrGenerateRequest;
import com.airtel.userprofile.eventpass.dto.response.QrGenerateResponse;
import com.airtel.userprofile.eventpass.service.MembershipQrService;
import io.swagger.annotations.Api;
import io.swagger.annotations.ApiOperation;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.RestController;

import jakarta.validation.Valid;

/**
 * API 4 — customer app (User Profile Service). {@code IV_USER} carries the authenticated customer
 * MSISDN, matching the contest controllers' convention.
 */
@RestController
@Api(value = "Event Pass — Membership QR")
@Slf4j
@RequiredArgsConstructor
public class MembershipQrController {

	private final MembershipQrService membershipQrService;

	/** Create a new QR (always mints). */
	@PostMapping("/v1/membership/qr")
	@ApiOperation(value = "Generate the signed membership QR (carries won eventIds)")
	@AuditLog(entity = Entity.USERPROFILE, operation = Operation.API, createNewLog = true, publishEvent = false)
	public Response<QrGenerateResponse> generate(
			@RequestHeader(name = UserProfileConstants.IV_USER) String ivUser,
			@Valid @RequestBody QrGenerateRequest request) {
		return Response.getSuccessResponse(membershipQrService.generate(ivUser, request.getDeviceId()));
	}

	/** Validate / get-or-create: return the cached live QR if present, else mint a new one. */
	@PostMapping("/v1/membership/qr/validate")
	@ApiOperation(value = "Return the cached live QR if present in the fast store, else create a new one")
	@AuditLog(entity = Entity.USERPROFILE, operation = Operation.API, createNewLog = true, publishEvent = false)
	public Response<QrGenerateResponse> validate(
			@RequestHeader(name = UserProfileConstants.IV_USER) String ivUser,
			@Valid @RequestBody QrGenerateRequest request) {
		return Response.getSuccessResponse(membershipQrService.validateOrGenerate(ivUser, request.getDeviceId()));
	}

	/** Explicit refresh: always mint a new QR, superseding the previous one. */
	@PostMapping("/v1/membership/qr/refresh")
	@ApiOperation(value = "Force a new membership QR (supersedes the previous one)")
	@AuditLog(entity = Entity.USERPROFILE, operation = Operation.API, createNewLog = true, publishEvent = false)
	public Response<QrGenerateResponse> refresh(
			@RequestHeader(name = UserProfileConstants.IV_USER) String ivUser,
			@Valid @RequestBody QrGenerateRequest request) {
		return Response.getSuccessResponse(membershipQrService.refresh(ivUser, request.getDeviceId()));
	}
}
