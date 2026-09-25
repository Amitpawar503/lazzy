package com.airtel.userprofile.eventpass.service.impl;

import com.airtel.userprofile.eventpass.config.EventPassProperties;
import com.airtel.userprofile.eventpass.dto.response.QrGenerateResponse;
import com.airtel.userprofile.eventpass.service.MembershipEligibilityService;
import com.airtel.userprofile.eventpass.service.MembershipQrService;
import com.airtel.userprofile.eventpass.service.QrTokenService;
import com.airtel.userprofile.eventpass.service.WinnerLookupService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.time.Instant;
import java.util.Set;

@Service
@Slf4j
@RequiredArgsConstructor
public class MembershipQrServiceImpl implements MembershipQrService {

	private final MembershipEligibilityService eligibility;
	private final WinnerLookupService winnerLookup;
	private final QrTokenService qrTokenService;
	private final EventPassProperties props;

	@Override
	public QrGenerateResponse generate(String msisdn, String deviceId) {
		if (!eligibility.isAdvantageClubMember(msisdn)) {
			// Non-members never get a membership QR.
			throw new IllegalArgumentException("Not an Advantage Club member");
		}

		// Every member gets a QR; the won events (possibly empty) are embedded and signed in.
		Set<String> wonEventIds = winnerLookup.findWonEventIds(msisdn);
		String token = qrTokenService.issue(msisdn, deviceId, wonEventIds);

		return QrGenerateResponse.builder()
				.qrToken(token)
				.expiresAt(Instant.now().plusSeconds(props.getQrTtlSeconds()))
				.build();
	}
}
