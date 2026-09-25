package com.airtel.userprofile.eventpass.exception;

/** Token is malformed, unsupported version, bad signature, or not Airtel-issued → INVALID_QR. */
public class QrInvalidException extends RuntimeException {

	public QrInvalidException(String message) {
		super(message);
	}
}
