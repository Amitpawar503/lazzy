package com.airtel.userprofile.eventpass.dao;

import com.airtel.userprofile.eventpass.document.EventRedemptionDocument;
import lombok.AllArgsConstructor;
import lombok.Getter;

/**
 * Result of an atomic redeem attempt.
 * <ul>
 *   <li>{@code firstClaim == true}  → this scan won the race; {@code row} is the freshly created redemption.</li>
 *   <li>{@code firstClaim == false} → already redeemed; {@code row} is the EXISTING first-claim record
 *       (used to decide DUPLICATE_ENTRY vs ALREADY_ENTERED_OTHER_DEVICE and to show first-claim time).</li>
 * </ul>
 */
@Getter
@AllArgsConstructor
public class RedeemOutcome {

	private final boolean firstClaim;
	private final EventRedemptionDocument row;
}
