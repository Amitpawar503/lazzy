package com.ogc.poc.Controller;

import java.util.List;

import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import com.ogc.poc.Constants.RollBackConstants;
import com.ogc.poc.Exception.CoreException;
import com.ogc.poc.Service.LogicService;
import com.ogc.poc.model.GameResult;

@RestController
public class LogicController {
	private static final Logger LOGGER = LogManager.getLogger(LogicController.class);

	@Autowired
	public LogicService logicService;

	@GetMapping("/getLogic")
	public ResponseEntity<List<GameResult>> getLogic(@RequestParam(name = "auto", required = false) String auto)
			throws CoreException {
		LOGGER.info("LogicController: Enter getLogic");
		return new ResponseEntity<List<GameResult>>(logicService.getLogic(RollBackConstants.BASE_GAME, auto),
				HttpStatus.OK);
	}

	@GetMapping("/getLogic/FreeGame")
	public ResponseEntity<List<GameResult>> getLogicFreeGame() throws CoreException {
		LOGGER.info("LogicController: Enter getLogic");
		return new ResponseEntity<List<GameResult>>(logicService.getLogic(RollBackConstants.FREE_GAME, "0"),
				HttpStatus.OK);
	}

}
