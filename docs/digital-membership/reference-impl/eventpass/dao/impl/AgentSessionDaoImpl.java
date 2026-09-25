package com.airtel.userprofile.eventpass.dao.impl;

import com.airtel.userprofile.eventpass.dao.AgentSessionDao;
import com.airtel.userprofile.eventpass.document.AgentSessionDocument;
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
public class AgentSessionDaoImpl implements AgentSessionDao {

	private final MongoTemplate mongoTemplate;

	@Override
	public AgentSessionDocument openExclusive(AgentSessionDocument session) {
		// single-active: revoke any prior live session for this msisdn
		Query prior = new Query(Criteria.where("msisdn").is(session.getMsisdn()).and("revoked").is(false));
		mongoTemplate.updateMulti(prior, new Update().set("revoked", true), AgentSessionDocument.class);
		return mongoTemplate.insert(session);
	}

	@Override
	public Optional<AgentSessionDocument> findActiveById(String sessionId) {
		Query q = new Query(Criteria.where("_id").is(sessionId)
				.and("revoked").is(false)
				.and("expiresAt").gt(Instant.now()));
		return Optional.ofNullable(mongoTemplate.findOne(q, AgentSessionDocument.class));
	}
}
