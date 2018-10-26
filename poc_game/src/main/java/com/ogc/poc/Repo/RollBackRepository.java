package com.ogc.poc.Repo;

import java.util.List;

import org.springframework.data.mongodb.repository.MongoRepository;
import org.springframework.stereotype.Repository;

import com.ogc.poc.model.RollBack;

public interface RollBackRepository extends MongoRepository<RollBack, String>,RollBackRepositoryCustom{
	
}
