package com.airtel.userprofile.eventpass.service.impl;

import com.airtel.userprofile.contest.document.WinnerInfo;
import com.airtel.userprofile.eventpass.dao.ContestWinnerAdminDao;
import com.airtel.userprofile.eventpass.service.WinnerAdminService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.time.Instant;

/**
 * Manual winner override. Builds a {@link WinnerInfo} (reusing the contest document) and writes it
 * onto the customer's existing {@code contest_entries} row(s). Because the winner list is embedded
 * into the QR at generation, a customer picks up a newly-marked win on their next QR refresh.
 */
@Service
@Slf4j
@RequiredArgsConstructor
public class WinnerAdminServiceImpl implements WinnerAdminService {

	private final ContestWinnerAdminDao winnerAdminDao;

	@Override
	public long markWinner(String eventId, String msisdn, Integer rank, String drawId, String actor) {
		WinnerInfo info = WinnerInfo.builder()
				.rank(rank)
				.drawId(drawId)
				.createdAt(Instant.now())
				.build();

		long updated = winnerAdminDao.markWinner(eventId, msisdn, info);
		if (updated == 0) {
			// Never fabricate an entry — the customer must have played the contest first.
			throw new IllegalArgumentException(
					"No contest entry found for msisdn in event " + eventId + "; cannot mark winner");
		}
		log.info("Winner marked by {}: event={} msisdn={} entriesUpdated={}", actor, eventId, msisdn, updated);
		return updated;
	}
}
