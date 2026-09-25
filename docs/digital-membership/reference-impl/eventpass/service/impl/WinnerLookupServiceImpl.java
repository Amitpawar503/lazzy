package com.airtel.userprofile.eventpass.service.impl;

import com.airtel.userprofile.contest.document.EntryDocument;
import com.airtel.userprofile.eventpass.service.WinnerLookupService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.mongodb.core.MongoTemplate;
import org.springframework.data.mongodb.core.query.Criteria;
import org.springframework.data.mongodb.core.query.Query;
import org.springframework.stereotype.Service;

import java.util.HashSet;
import java.util.List;
import java.util.Set;

/**
 * Reads winners straight from the contest collection. A winning entry is one where
 * {@code winnerInfo} exists (set by the draw). {@code programId} is treated as the eventId.
 *
 * <p>We query only the fields we need (projection) and never expose PII from here — the caller
 * only receives event ids / a boolean.
 */
@Service
@Slf4j
@RequiredArgsConstructor
public class WinnerLookupServiceImpl implements WinnerLookupService {

	private final MongoTemplate mongoTemplate;

	private static Query winningEntriesOf(String msisdn) {
		// winnerInfo present == winner (mirrors DrawServiceImpl.upsertWinnerInfoOnEntries)
		return new Query(Criteria.where("msisdn").is(msisdn).and("winnerInfo").exists(true));
	}

	@Override
	public Set<String> findWonEventIds(String msisdn) {
		if (msisdn == null || msisdn.isBlank()) {
			return Set.of();
		}
		Query q = winningEntriesOf(msisdn);
		q.fields().include("programId");
		List<EntryDocument> entries = mongoTemplate.find(q, EntryDocument.class);
		Set<String> eventIds = new HashSet<>();
		for (EntryDocument e : entries) {
			if (e.getProgramId() != null && !e.getProgramId().isBlank()) {
				eventIds.add(e.getProgramId());
			}
		}
		log.debug("Winner lookup: msisdn={} won {} event(s)", msisdn, eventIds.size());
		return eventIds;
	}

	@Override
	public boolean isWinner(String msisdn, String eventId) {
		if (msisdn == null || msisdn.isBlank() || eventId == null || eventId.isBlank()) {
			return false;
		}
		Query q = winningEntriesOf(msisdn);
		q.addCriteria(Criteria.where("programId").is(eventId));
		return mongoTemplate.exists(q, EntryDocument.class);
	}
}
