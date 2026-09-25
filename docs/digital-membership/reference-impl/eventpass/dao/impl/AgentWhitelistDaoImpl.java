package com.airtel.userprofile.eventpass.dao.impl;

import com.airtel.userprofile.eventpass.dao.AgentWhitelistDao;
import com.airtel.userprofile.eventpass.document.AgentWhitelistDocument;
import lombok.RequiredArgsConstructor;
import org.springframework.data.mongodb.core.MongoTemplate;
import org.springframework.data.mongodb.core.query.Criteria;
import org.springframework.data.mongodb.core.query.Query;
import org.springframework.data.mongodb.core.query.Update;
import org.springframework.stereotype.Repository;

import java.time.Instant;
import java.util.List;
import java.util.Optional;

@Repository
@RequiredArgsConstructor
public class AgentWhitelistDaoImpl implements AgentWhitelistDao {

	private final MongoTemplate mongoTemplate;

	@Override
	public AgentWhitelistDocument upsert(AgentWhitelistDocument doc) {
		Query q = new Query(Criteria.where("eventId").is(doc.getEventId()).and("msisdn").is(doc.getMsisdn()));
		Update u = new Update()
				.set("checkpoints", doc.getCheckpoints())
				.set("active", doc.isActive())
				.set("createdBy", doc.getCreatedBy())
				.set("updatedAt", Instant.now())
				.setOnInsert("createdAt", Instant.now());
		mongoTemplate.upsert(u, q, AgentWhitelistDocument.class);
		return findActive(doc.getEventId(), doc.getMsisdn()).orElse(doc);
	}

	@Override
	public List<AgentWhitelistDocument> findActiveByMsisdn(String msisdn) {
		Query q = new Query(Criteria.where("msisdn").is(msisdn).and("active").is(true));
		return mongoTemplate.find(q, AgentWhitelistDocument.class);
	}

	@Override
	public Optional<AgentWhitelistDocument> findActive(String eventId, String msisdn) {
		Query q = new Query(Criteria.where("eventId").is(eventId).and("msisdn").is(msisdn).and("active").is(true));
		return Optional.ofNullable(mongoTemplate.findOne(q, AgentWhitelistDocument.class));
	}
}
