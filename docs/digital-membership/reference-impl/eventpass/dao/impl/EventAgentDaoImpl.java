package com.airtel.userprofile.eventpass.dao.impl;

import com.airtel.userprofile.eventpass.dao.EventAgentDao;
import com.airtel.userprofile.eventpass.document.EventAgentDocument;
import com.airtel.userprofile.eventpass.enums.Checkpoint;
import lombok.RequiredArgsConstructor;
import org.springframework.data.mongodb.core.MongoTemplate;
import org.springframework.data.mongodb.core.query.Criteria;
import org.springframework.data.mongodb.core.query.Query;
import org.springframework.data.mongodb.core.query.Update;
import org.springframework.stereotype.Repository;

import java.time.Instant;
import java.util.List;
import java.util.Optional;
import java.util.Set;

@Repository
@RequiredArgsConstructor
public class EventAgentDaoImpl implements EventAgentDao {

	private final MongoTemplate mongoTemplate;

	@Override
	public EventAgentDocument upsert(EventAgentDocument doc) {
		doc.setId(EventAgentDocument.idOf(doc.getMsisdn(), doc.getEventId()));
		doc.setCleanupAt(EventAgentDocument.cleanupFrom(doc.getEndTime()));
		doc.setUpdatedAt(Instant.now());
		if (doc.getCreatedAt() == null) {
			doc.setCreatedAt(Instant.now());
		}
		return mongoTemplate.save(doc);   // _id == msisdn::eventId → create or replace
	}

	@Override
	public Optional<EventAgentDocument> findByEventAndAgent(String eventId, String msisdn) {
		return Optional.ofNullable(mongoTemplate.findById(
				EventAgentDocument.idOf(msisdn, eventId), EventAgentDocument.class));
	}

	@Override
	public Optional<EventAgentDocument> findActive(String eventId, String msisdn) {
		Query q = new Query(Criteria.where("_id").is(EventAgentDocument.idOf(msisdn, eventId)).and("active").is(true));
		return Optional.ofNullable(mongoTemplate.findOne(q, EventAgentDocument.class));
	}

	@Override
	public List<EventAgentDocument> findByEvent(String eventId) {
		return mongoTemplate.find(new Query(Criteria.where("eventId").is(eventId)), EventAgentDocument.class);
	}

	@Override
	public Optional<EventAgentDocument> findAnyByEvent(String eventId) {
		return Optional.ofNullable(mongoTemplate.findOne(
				new Query(Criteria.where("eventId").is(eventId)), EventAgentDocument.class));
	}

	@Override
	public List<EventAgentDocument> findActiveByAgent(String msisdn) {
		Query q = new Query(Criteria.where("msisdn").is(msisdn).and("active").is(true));
		return mongoTemplate.find(q, EventAgentDocument.class);
	}

	@Override
	public long update(String eventId, String msisdn, Set<Checkpoint> checkpoints, Boolean active) {
		Query q = new Query(Criteria.where("_id").is(EventAgentDocument.idOf(msisdn, eventId)));
		Update u = new Update().set("updatedAt", Instant.now());
		if (checkpoints != null) u.set("checkpoints", checkpoints);
		if (active != null) u.set("active", active);
		return mongoTemplate.updateFirst(u, q, EventAgentDocument.class).getMatchedCount();
	}

	@Override
	public long delete(String eventId, String msisdn) {
		Query q = new Query(Criteria.where("_id").is(EventAgentDocument.idOf(msisdn, eventId)));
		return mongoTemplate.remove(q, EventAgentDocument.class).getDeletedCount();
	}
}
