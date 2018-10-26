package com.ogc.poc.model;


import com.fasterxml.jackson.dataformat.xml.annotation.JacksonXmlProperty;
import com.fasterxml.jackson.dataformat.xml.annotation.JacksonXmlRootElement;

@JacksonXmlRootElement(localName="RSP")
public class RollbackResponse extends RSP
{
	@JacksonXmlProperty(isAttribute = false, localName = "CURRENCY")
	public String currency;

	@JacksonXmlProperty(isAttribute = false, localName = "BONUSBALANCE")
	public double bonusBalance;
	
	@JacksonXmlProperty(isAttribute = false, localName = "REALBALANCE")
	public double realBalance;

	@JacksonXmlProperty(isAttribute = false, localName = "TOTALAMOUNT")
	public double totalAmount;

	@Override
	public String toString() {
		return "RollbackResponse [currency=" + currency + ", bonusBalance=" + bonusBalance + ", realBalance=" + realBalance
				+ ", totalAmount=" + totalAmount + "]";
	}
	
}
