package com.airtel.userprofile.eventpass.dao.impl;

import com.airtel.userprofile.contest.document.EntryDocument;
import com.airtel.userprofile.contest.document.WinnerInfo;
import com.airtel.userprofile.eventpass.dao.ContestWinnerAdminDao;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.mongodb.core.MongoTemplate;
import org.springframework.data.mongodb.core.query.Criteria;
import org.springframework.data.mongodb.core.query.Query;
import org.springframework.data.mongodb.core.query.Update;
import org.springframework.stereotype.Repository;

import java.time.Instant;

/**
 * Writes {@code winnerInfo} onto existing {@code contest_entries} documents via MongoTemplate —
 * the same field {@code DrawServiceImpl} sets, but as a manual admin override. Never creates an
 * entry: a customer must already have entered the contest to be marked a winner.
 */
@Repository
@Slf4j
@RequiredArgsConstructor
public class ContestWinnerAdminDaoImpl implements ContestWinnerAdminDao {

	private final MongoTemplate mongoTemplate;

	@Override
	public long markWinner(String programId, String msisdn, WinnerInfo winnerInfo) {
		Query q = new Query(Criteria.where("programId").is(programId).and("msisdn").is(msisdn));
		Update u = new Update()
				.set("winnerInfo", winnerInfo)
				.set("updatedAt", Instant.now());
		long matched = mongoTemplate.updateMulti(q, u, EntryDocument.class).getMatchedCount();
		log.info("markWinner: programId={} msisdn={} matchedEntries={}", programId, msisdn, matched);
		return matched;
	}
}
