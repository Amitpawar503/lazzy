package com.airtel.userprofile.eventpass.enums;

import lombok.Getter;

/**
 * Authoritative decision codes returned to the agent scanner (Thanks App, agent mode).
 * Only {@link #ENTRY_ALLOWED} admits. {@code color} and {@code admit} drive the result screen;
 * every code also carries explicit text (accessibility — never colour alone).
 */
@Getter
public enum EntryCallback {

	ENTRY_ALLOWED("green", true, true, "Entry allowed. Customer admitted."),
	DUPLICATE_ENTRY("red", false, true, "Already claimed on this device."),
	ALREADY_ENTERED_OTHER_DEVICE("red", false, true, "Already claimed on another device."),
	NOT_ENTITLED("red", false, true, "Member is not a winner for this event."),
	QR_EXPIRED("grey", false, true, "QR expired. Ask the customer to refresh and re-present."),
	INVALID_QR("red", false, true, "Invalid QR. Ask the customer to open it from the Airtel app."),
	STAFF_SESSION_INVALID("red", false, false, "Session expired. Re-open the scanner to continue."),
	SERVICE_UNAVAILABLE("grey", false, true, "Service error. Retry the scan.");

	private final String color;
	private final boolean admit;
	private final boolean scannerResumes;
	private final String defaultMessage;

	EntryCallback(String color, boolean admit, boolean scannerResumes, String defaultMessage) {
		this.color = color;
		this.admit = admit;
		this.scannerResumes = scannerResumes;
		this.defaultMessage = defaultMessage;
	}
}
