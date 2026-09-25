package com.airtel.userprofile.eventpass.dao.impl;

import com.airtel.userprofile.eventpass.dao.ScanLogDao;
import com.airtel.userprofile.eventpass.document.ScanLogDocument;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Sort;
import org.springframework.data.mongodb.core.MongoTemplate;
import org.springframework.data.mongodb.core.query.Criteria;
import org.springframework.data.mongodb.core.query.Query;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

@Repository
@RequiredArgsConstructor
public class ScanLogDaoImpl implements ScanLogDao {

	private final MongoTemplate mongoTemplate;

	@Override
	public ScanLogDocument save(ScanLogDocument log) {
		return mongoTemplate.save(log);
	}

	@Override
	public Optional<ScanLogDocument> findByScanRequestId(String scanRequestId) {
		if (scanRequestId == null || scanRequestId.isBlank()) {
			return Optional.empty();
		}
		Query q = new Query(Criteria.where("scanRequestId").is(scanRequestId));
		return Optional.ofNullable(mongoTemplate.findOne(q, ScanLogDocument.class));
	}

	@Override
	public List<ScanLogDocument> findByCustomerMsisdnOrderByServerTs(String customerMsisdn) {
		Query q = new Query(Criteria.where("customerMsisdn").is(customerMsisdn))
				.with(Sort.by(Sort.Direction.ASC, "serverTs"));
		return mongoTemplate.find(q, ScanLogDocument.class);
	}
}
