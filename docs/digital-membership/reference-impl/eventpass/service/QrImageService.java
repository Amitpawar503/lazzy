package com.airtel.userprofile.eventpass.service;

import com.airtel.userprofile.eventpass.dto.request.QrRenderRequest;
import com.airtel.userprofile.eventpass.dto.response.QrRenderResponse;

/**
 * Generates styled circular QR images and reads them back. Wraps the low-level utils with the
 * configured {@code eventpass.qr-style.*} defaults and per-request overrides.
 */
public interface QrImageService {

	/** Render a styled QR carrying {@code request.data} (token / deeplink / info) as a PNG data URI. */
	QrRenderResponse render(QrRenderRequest request);

	/** Render raw PNG bytes for {@code data} using the configured defaults (no overrides). */
	byte[] renderPng(String data);

	/**
	 * Decode a QR image to its payload (structural validation).
	 * @throws com.airtel.userprofile.eventpass.exception.QrInvalidException if unreadable.
	 */
	String decode(byte[] imageBytes);
}
