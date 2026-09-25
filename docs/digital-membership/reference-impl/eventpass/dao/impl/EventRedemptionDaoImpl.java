package com.airtel.userprofile.eventpass.dao.impl;

import com.airtel.userprofile.eventpass.dao.EventRedemptionDao;
import com.airtel.userprofile.eventpass.dao.RedeemOutcome;
import com.airtel.userprofile.eventpass.document.EventRedemptionDocument;
import com.airtel.userprofile.eventpass.enums.Checkpoint;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.dao.DuplicateKeyException;
import org.springframework.data.mongodb.core.MongoTemplate;
import org.springframework.data.mongodb.core.query.Criteria;
import org.springframework.data.mongodb.core.query.Query;
import org.springframework.stereotype.Repository;

import java.time.Instant;
import java.util.Optional;
import java.util.UUID;

/**
 * MongoTemplate implementation of the atomic redemption.
 *
 * <p>The concurrency guarantee is the DB's, not the app's: the unique compound index
 * {@code (eventId, msisdn, checkpoint)} means an {@code insert} either creates the one row (this
 * scan won) or throws {@link DuplicateKeyException} (someone already claimed). We never
 * read-then-write, so there is no lost-update window — exactly the pattern the contest module uses
 * for {@code orderId} on {@code contest_entries}.
 */
@Repository
@Slf4j
@RequiredArgsConstructor
public class EventRedemptionDaoImpl implements EventRedemptionDao {

	private final MongoTemplate mongoTemplate;

	@Override
	public RedeemOutcome tryRedeem(String eventId, String msisdn, Checkpoint checkpoint,
								   String deviceId, String agentMsisdn, String scanRequestId) {
		EventRedemptionDocument doc = EventRedemptionDocument.builder()
				.id(UUID.randomUUID().toString())
				.eventId(eventId)
				.msisdn(msisdn)
				.checkpoint(checkpoint)
				.deviceId(deviceId)
				.redeemedByAgentMsisdn(agentMsisdn)
				.scanRequestId(scanRequestId)
				.redeemedAt(Instant.now())
				.build();
		try {
			mongoTemplate.insert(doc);
			// won the race — first and only claim for this (event, msisdn, checkpoint)
			return new RedeemOutcome(true, doc);
		} catch (DuplicateKeyException dup) {
			// someone already claimed this checkpoint; return the existing first-claim record so the
			// service can decide DUPLICATE_ENTRY vs ALREADY_ENTERED_OTHER_DEVICE and show first-claim time
			EventRedemptionDocument existing = find(eventId, msisdn, checkpoint)
					.orElseThrow(() -> dup); // unique conflict but no row → surface as infra error (SERVICE_UNAVAILABLE)
			return new RedeemOutcome(false, existing);
		}
	}

	@Override
	public Optional<EventRedemptionDocument> find(String eventId, String msisdn, Checkpoint checkpoint) {
		Query q = new Query(Criteria.where("eventId").is(eventId)
				.and("msisdn").is(msisdn)
				.and("checkpoint").is(checkpoint));
		return Optional.ofNullable(mongoTemplate.findOne(q, EventRedemptionDocument.class));
	}
}
