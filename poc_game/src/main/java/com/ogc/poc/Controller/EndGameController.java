package com.ogc.poc.Controller;

import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestMethod;

import com.ogc.poc.Constants.Constants;
import com.ogc.poc.model.EndGameResponse;



@Controller
public class EndGameController {

	
	@RequestMapping(value = Constants.GET_ENDGAME, method = RequestMethod.GET, produces = { "application/xml", "text/xml" })
	public ResponseEntity<EndGameResponse> getEndGameResponse() {
		Double balance=20.00;
		String currency="INR";
		EndGameResponse endGameResponse=new com.ogc.poc.model.EndGameResponse();
		endGameResponse.setBalance(balance);
		endGameResponse.setCurrency(currency);
		endGameResponse.setMsg("Your game over....Thanks for playing this game.... your winning amount is  "+balance);
		return new ResponseEntity<EndGameResponse>(endGameResponse,HttpStatus.OK);
	}
}
