package com.airtel.userprofile.eventpass.dao;

import com.airtel.userprofile.eventpass.enums.Checkpoint;

import java.util.Optional;

/**
 * Persistence for the exactly-once redemption anchor. The single method that matters is
 * {@link #tryRedeem}: it must be atomic so two concurrent scans of the same QR at the same
 * checkpoint produce exactly one first-claim.
 */
public interface EventRedemptionDao {

	/**
	 * Atomically claim {@code (eventId, msisdn, checkpoint)}.
	 * <p>Implemented as an insert guarded by the unique compound index: the first insert wins
	 * ({@code firstClaim=true}); a concurrent/duplicate insert throws DuplicateKeyException, which
	 * the impl converts into {@code firstClaim=false} + the existing row. No read-then-write race.
	 */
	RedeemOutcome tryRedeem(String eventId, String msisdn, Checkpoint checkpoint,
							String deviceId, String agentMsisdn, String scanRequestId);

	Optional<com.airtel.userprofile.eventpass.document.EventRedemptionDocument> find(
			String eventId, String msisdn, Checkpoint checkpoint);
}
