package com.ogc.poc.Repo;

import java.util.List;

import com.ogc.poc.model.RollBack;

public interface RollBackRepositoryCustom {
	public  List<RollBack> findRollBackData(String sessionId);
}
