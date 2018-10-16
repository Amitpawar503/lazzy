package ogs.wapi.mock.dto;

import com.fasterxml.jackson.dataformat.xml.annotation.JacksonXmlProperty;

public class WagerResponse extends RSP
{
	@JacksonXmlProperty(isAttribute = false, localName = "CURRENCY")
	public String currency;
	
	@JacksonXmlProperty(isAttribute = false, localName = "BONUSBALANCE")
	public double bonusBalance;
	
	@JacksonXmlProperty(isAttribute = false, localName = "REALBALANCE")
	public double realBalance;
	
	@JacksonXmlProperty(isAttribute = false, localName = "BONUSMONEYBET")
	public double bonusMoneyBet;
	
	@JacksonXmlProperty(isAttribute = false, localName = "REALMONEYBET")
	public double realMoneyBet;

}
