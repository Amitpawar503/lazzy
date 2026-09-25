package com.airtel.userprofile.eventpass.service;

import com.airtel.userprofile.eventpass.dto.response.QrGenerateResponse;

/** API 4 — generate/refresh the signed membership QR shown in the Thanks App. */
public interface MembershipQrService {

	QrGenerateResponse generate(String msisdn, String deviceId);
}
