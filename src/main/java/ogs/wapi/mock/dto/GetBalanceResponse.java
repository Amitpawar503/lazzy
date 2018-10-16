package ogs.wapi.mock.dto;

import com.fasterxml.jackson.dataformat.xml.annotation.JacksonXmlProperty;
import com.fasterxml.jackson.dataformat.xml.annotation.JacksonXmlRootElement;

@JacksonXmlRootElement(localName="RSP")
public class GetBalanceResponse  extends RSP 
{
	@JacksonXmlProperty(isAttribute = false, localName = "REALBALANCE")
	public double RealBalance;
	
	@JacksonXmlProperty(isAttribute = false, localName = "BONUSBALANCE")
	public double BonusBalance;
	
	@JacksonXmlProperty(isAttribute = false, localName = "CURRENCY")
	public String currency;
}
