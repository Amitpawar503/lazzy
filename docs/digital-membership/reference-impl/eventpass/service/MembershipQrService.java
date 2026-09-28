package com.airtel.userprofile.eventpass.service;

import com.airtel.userprofile.eventpass.dto.response.QrGenerateResponse;

/** API 4 family — generate / validate (get-or-create) / refresh the signed membership QR. */
public interface MembershipQrService {

	/** Always mint a fresh QR (supersedes any previous one). */
	QrGenerateResponse generate(String msisdn, String deviceId);

	/**
	 * Get-or-create: if a live QR for this customer+device is already cached in the fast store,
	 * return it as-is; otherwise mint a new one. This is the default the app calls on card open.
	 */
	QrGenerateResponse validateOrGenerate(String msisdn, String deviceId);

	/** Force a new QR (explicit refresh); supersedes the previous one immediately. */
	QrGenerateResponse refresh(String msisdn, String deviceId);
}
