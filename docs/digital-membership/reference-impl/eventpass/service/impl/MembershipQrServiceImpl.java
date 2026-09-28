package com.airtel.userprofile.eventpass.service.impl;

import com.airtel.userprofile.eventpass.dto.response.QrGenerateResponse;
import com.airtel.userprofile.eventpass.service.CachedQr;
import com.airtel.userprofile.eventpass.service.MembershipEligibilityService;
import com.airtel.userprofile.eventpass.service.MembershipQrService;
import com.airtel.userprofile.eventpass.service.QrIssuanceStore;
import com.airtel.userprofile.eventpass.service.QrTokenService;
import com.airtel.userprofile.eventpass.service.WinnerLookupService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.util.Optional;
import java.util.Set;

@Service
@Slf4j
@RequiredArgsConstructor
public class MembershipQrServiceImpl implements MembershipQrService {

	private final MembershipEligibilityService eligibility;
	private final WinnerLookupService winnerLookup;
	private final QrTokenService qrTokenService;
	private final QrIssuanceStore issuanceStore;

	@Override
	public QrGenerateResponse generate(String msisdn, String deviceId) {
		requireMember(msisdn);
		// Every member gets a QR; the won events (possibly empty) are embedded and signed in.
		Set<String> wonEventIds = winnerLookup.findWonEventIds(msisdn);
		CachedQr issued = qrTokenService.issue(msisdn, deviceId, wonEventIds);
		return toResponse(issued);
	}

	@Override
	public QrGenerateResponse validateOrGenerate(String msisdn, String deviceId) {
		requireMember(msisdn);
		// If a live QR for this same device is cached, return it as-is (no re-mint).
		Optional<CachedQr> cached = issuanceStore.getActive(msisdn);
		if (cached.isPresent() && deviceId != null && deviceId.equals(cached.get().getDeviceId())) {
			log.debug("QR validate: returning cached active QR for msisdn={}", msisdn);
			return toResponse(cached.get());
		}
		// Miss (none cached, expired, or different device) → mint a fresh one.
		return generate(msisdn, deviceId);
	}

	@Override
	public QrGenerateResponse refresh(String msisdn, String deviceId) {
		// Explicit refresh always supersedes the cached QR.
		return generate(msisdn, deviceId);
	}

	private void requireMember(String msisdn) {
		if (!eligibility.isAdvantageClubMember(msisdn)) {
			throw new IllegalArgumentException("Not an Advantage Club member");
		}
	}

	private static QrGenerateResponse toResponse(CachedQr qr) {
		return QrGenerateResponse.builder()
				.qrToken(qr.getToken())
				.expiresAt(qr.getExpiresAt())
				.build();
	}
}
