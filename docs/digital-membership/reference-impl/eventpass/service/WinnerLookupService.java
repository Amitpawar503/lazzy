package com.airtel.userprofile.eventpass.service;

import java.util.Set;

/**
 * The "draw winner check" for event access. Reuses the Contest module's winner data: a winner is a
 * {@code contest_entries} row whose {@code winnerInfo} is set (that is how {@code DrawServiceImpl}
 * marks winners). A live event maps to a contest {@code programId}, so:
 * <ul>
 *   <li>{@link #findWonEventIds(String)} → the programIds this msisdn has won (embedded into the QR at generation).</li>
 *   <li>{@link #isWinner(String, String)} → server-side re-check at entry time (defense in depth).</li>
 * </ul>
 */
public interface WinnerLookupService {

	/** Distinct programIds (= eventIds) where this msisdn has a winning contest entry. */
	Set<String> findWonEventIds(String msisdn);

	/** True if this msisdn has a winning entry for the given event (programId). */
	boolean isWinner(String msisdn, String eventId);
}
