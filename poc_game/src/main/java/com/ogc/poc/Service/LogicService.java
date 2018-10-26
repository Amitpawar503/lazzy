package com.ogc.poc.Service;

import java.util.List;

import com.ogc.poc.Exception.CoreException;
import com.ogc.poc.model.GameResult;

public interface LogicService {
	public List<GameResult> getLogic(String gameType, String autoPlay) throws CoreException;
}
