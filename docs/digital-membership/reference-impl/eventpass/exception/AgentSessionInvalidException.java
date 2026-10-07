package com.airtel.userprofile.eventpass.exception;

/** Agent (authenticated {@code IV_USER}) is not whitelisted for the requested event/checkpoint. */
public class AgentSessionInvalidException extends RuntimeException {

	public AgentSessionInvalidException(String message) {
		super(message);
	}
}
