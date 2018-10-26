package com.ogc.poc.Controller;

import java.io.IOException;
import java.net.MalformedURLException;

import javax.xml.bind.JAXBException;

import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import com.ogc.poc.Constants.RollBackConstants;
import com.ogc.poc.Exception.CoreException;
import com.ogc.poc.Service.RollBackManagerService;
import com.ogc.poc.model.RollbackResponse;
import com.ogc.poc.model.Player;
import com.ogc.poc.model.RollBack;

@RestController
@RequestMapping(RollBackConstants.ROOT_CONTEXT)
public class RollBackController {

	private static final Logger LOGGER = LogManager.getLogger(RollBackController.class);

	@Autowired
	public RollBackManagerService rollBackManager;

	@GetMapping(value=RollBackConstants.ROLL_BACK_URI_PATH,produces= {MediaType.APPLICATION_XML_VALUE})
	public ResponseEntity<RollbackResponse> doRollBack(@RequestParam(name = RollBackConstants.REQUEST, required = false) String request,
			@RequestParam(name = RollBackConstants.SESSION_ID, required = false) String sessionId) throws CoreException,MalformedURLException,IOException,JAXBException  {
		 LOGGER.info("RollBackController :: doRollBack Enter");
			return new ResponseEntity<RollbackResponse>( rollBackManager.doroll(request, sessionId),HttpStatus.OK);
			
	}
	
	
}
