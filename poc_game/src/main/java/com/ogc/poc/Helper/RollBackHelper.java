package com.ogc.poc.Helper;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;

@Service
public class RollBackHelper {

	private final Logger LOGGER = LoggerFactory.getLogger(this.getClass());
	
	public boolean rollValidate(String request,String sessionId) {
		LOGGER.info("RollBackHelper :: rollValidate Enter");
		boolean validationStatus=false;
		if(!StringUtils.isEmpty(request) && !StringUtils.isEmpty(sessionId)) {
			validationStatus=true;
		}
		LOGGER.info("RollBackHelper :: rollValidate Exit");
		return validationStatus;
	}
}
