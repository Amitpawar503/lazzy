package com.ogc.poc.Helper;

import java.util.ResourceBundle;

import org.springframework.stereotype.Service;

@Service
public class LogicHelper {
	private static ResourceBundle rb = ResourceBundle.getBundle("ruleBook");
	
	public Integer giveWinAmount(String award) {
		return  Integer.parseInt(rb.getString("award"+rb.getString(award)));
	}
}
