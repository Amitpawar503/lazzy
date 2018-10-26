package com.ogc.poc.Controller;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestMethod;
import org.springframework.web.bind.annotation.RestController;

import com.ogc.poc.Constants.Constants;
import com.ogc.poc.Service.InitService;
import com.ogc.poc.model.InitGameResponse;


@RestController
public class InitController {
	
	@Autowired
	private InitService initService;

	@RequestMapping(value = Constants.GET_INIT, method = RequestMethod.GET, produces = { "application/xml", "text/xml" })
	public ResponseEntity<InitGameResponse> getInit() {
	return new ResponseEntity<InitGameResponse>(initService.getInitResponse(),HttpStatus.OK);
	}
	
	
}
