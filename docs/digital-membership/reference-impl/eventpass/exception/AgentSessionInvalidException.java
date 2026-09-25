package com.airtel.userprofile.eventpass.exception;

/** Agent session missing, revoked, expired, or not authorized for the event/checkpoint. */
public class AgentSessionInvalidException extends RuntimeException {

	public AgentSessionInvalidException(String message) {
		super(message);
	}
}
