package com.airtel.userprofile.eventpass.exception;

/** Token is genuine but past its TTL, or superseded by a newer issuance → QR_EXPIRED. */
public class QrExpiredException extends RuntimeException {

	public QrExpiredException(String message) {
		super(message);
	}
}
