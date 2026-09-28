package com.airtel.userprofile.eventpass.service;

/** API 5 — mark/update a winner on the customer's existing contest entry (writes winnerInfo). */
public interface WinnerAdminService {

	/**
	 * @return number of contest entries updated for (eventId, msisdn).
	 * @throws IllegalArgumentException if the customer has no contest entry for this event.
	 */
	long markWinner(String eventId, String msisdn, Integer rank, String drawId, String actor);
}
