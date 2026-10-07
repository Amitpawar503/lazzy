package com.airtel.userprofile.eventpass.dao.impl;

import com.airtel.userprofile.eventpass.dao.EventDao;
import com.airtel.userprofile.eventpass.document.EventDocument;
import lombok.RequiredArgsConstructor;
import org.springframework.data.mongodb.core.MongoTemplate;
import org.springframework.data.mongodb.core.query.Criteria;
import org.springframework.data.mongodb.core.query.Query;
import org.springframework.data.mongodb.core.query.Update;
import org.springframework.stereotype.Repository;

import java.time.Instant;
import java.util.Optional;

@Repository
@RequiredArgsConstructor
public class EventDaoImpl implements EventDao {

	private final MongoTemplate mongoTemplate;

	@Override
	public EventDocument upsert(EventDocument event) {
		event.setCleanupAt(EventDocument.cleanupFrom(event.getEndTime()));
		event.setUpdatedAt(Instant.now());
		if (event.getCreatedAt() == null) {
			event.setCreatedAt(Instant.now());
		}
		return mongoTemplate.save(event);   // _id == eventId → create or replace
	}

	@Override
	public Optional<EventDocument> findById(String eventId) {
		return Optional.ofNullable(mongoTemplate.findById(eventId, EventDocument.class));
	}

	@Override
	public long setActive(String eventId, boolean active) {
		Query q = new Query(Criteria.where("_id").is(eventId));
		Update u = new Update().set("active", active).set("updatedAt", Instant.now());
		return mongoTemplate.updateFirst(u, q, EventDocument.class).getMatchedCount();
	}
}
