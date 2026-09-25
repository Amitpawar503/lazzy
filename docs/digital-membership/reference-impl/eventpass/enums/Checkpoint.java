package com.airtel.userprofile.eventpass.enums;

import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonValue;

/**
 * The two ingresses at a live Advantage Club event. Each is an independent, one-time redemption
 * per (event, customer): a winner is admitted once at {@link #ENTRY} and collects once at
 * {@link #GOODIE}; order does not matter and one does not consume the other.
 */
public enum Checkpoint {

	ENTRY("entry"),
	GOODIE("goodie");

	private final String value;

	Checkpoint(String value) {
		this.value = value;
	}

	@JsonValue
	public String getValue() {
		return value;
	}

	@JsonCreator
	public static Checkpoint fromValue(String value) {
		if (value == null || value.isBlank()) {
			throw new IllegalArgumentException("checkpoint is required");
		}
		String normalized = value.trim();
		for (Checkpoint c : values()) {
			if (c.value.equalsIgnoreCase(normalized) || c.name().equalsIgnoreCase(normalized)) {
				return c;
			}
		}
		throw new IllegalArgumentException("Unsupported checkpoint: " + value);
	}
}
