package com.airtel.userprofile.eventpass.service;

/**
 * Membership eligibility gate for QR generation. Backed by the existing User Profile eligibility
 * logic (active Postpaid + Fastlane / Advantage Club). Wired to the platform's existing bean; the
 * eventpass module only depends on this narrow contract.
 */
public interface MembershipEligibilityService {

	boolean isAdvantageClubMember(String msisdn);
}
