package com.airtel.userprofile.eventpass.dao;

import com.airtel.userprofile.contest.document.WinnerInfo;

/**
 * Write side of the winner data: sets {@code winnerInfo} on the customer's existing
 * {@code contest_entries} document(s). Read side stays in {@code WinnerLookupService}.
 */
public interface ContestWinnerAdminDao {

	/**
	 * Set {@code winnerInfo} on every {@code contest_entries} row matching
	 * {@code (programId, msisdn)}.
	 * @return number of entry documents updated (0 ⇒ the customer has no entry for this event).
	 */
	long markWinner(String programId, String msisdn, WinnerInfo winnerInfo);
}
