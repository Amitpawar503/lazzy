package com.airtel.userprofile.eventpass.exception;

import com.airtel.core.dto.genericResponse.Error;
import com.airtel.core.dto.genericResponse.Response;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

/**
 * Mirrors {@code ContestExceptionHandler}. NOTE: on the entry path (API 3) all gate DECISIONS —
 * including {@code INVALID_QR}, {@code QR_EXPIRED}, {@code STAFF_SESSION_INVALID} — are returned by
 * the service as a 200 {@code EntryScanResponse} carrying the callback, so the scanner always
 * parses a decision. This handler covers the admin/validate paths and unexpected failures.
 */
@RestControllerAdvice(basePackages = "com.airtel.userprofile.eventpass.controller")
@Slf4j
public class EventPassExceptionHandler {

	@ExceptionHandler(IllegalArgumentException.class)
	public ResponseEntity<Response<Object>> handleBadRequest(IllegalArgumentException ex) {
		log.warn("EventPass bad request: {}", ex.getMessage());
		return failure(ex.getMessage(), "bad_request", HttpStatus.BAD_REQUEST);
	}

	@ExceptionHandler(AgentSessionInvalidException.class)
	public ResponseEntity<Response<Object>> handleSession(AgentSessionInvalidException ex) {
		log.warn("EventPass agent session invalid: {}", ex.getMessage());
		return failure(ex.getMessage(), "staff_session_invalid", HttpStatus.UNAUTHORIZED);
	}

	private static ResponseEntity<Response<Object>> failure(String message, String code, HttpStatus status) {
		Error error = new Error().setMessage(message).setCode(code);
		return ResponseEntity.status(status).body(Response.getFailureResponseWithError(error, status.value()));
	}
}
