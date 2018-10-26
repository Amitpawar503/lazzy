package com.ogc.poc.RepoImpl;

import java.util.List;
import java.util.Optional;

import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.domain.Example;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.domain.Sort;
import org.springframework.data.mongodb.core.MongoTemplate;
import org.springframework.data.mongodb.core.query.Criteria;
import org.springframework.data.mongodb.repository.Query;
import org.springframework.stereotype.Repository;

import com.ogc.poc.Controller.RollBackController;
import com.ogc.poc.Repo.RollBackRepository;
import com.ogc.poc.Repo.RollBackRepositoryCustom;
import com.ogc.poc.model.RollBack;

@Repository
public class RollBackRepositoryImpl implements RollBackRepositoryCustom {
	private static final Logger LOGGER = LogManager.getLogger(RollBackRepositoryImpl.class);

	@Autowired
	public MongoTemplate mongo;

	@Override
	public List<RollBack> findRollBackData(String name) {
		// TODO Auto-generated method stub
		LOGGER.info("RollBackRepositoryImpl ENTER ::findRollBackData");
		RollBack roll = new RollBack();
		roll.setApiVersion(10);
		roll.setBalanceAmount(4000);
		roll.setSessionId("123");
		roll.setCurrencyCode(name);
		System.out.println("saving");
		mongo.save(roll);
		LOGGER.debug("RollBackRepositoryImpl inserted data :{}",mongo.findAll(RollBack.class));
		LOGGER.info("RollBackRepositoryImpl EXIT ::findRollBackData");
		return mongo.findAll(RollBack.class);
	}

}
