package ogs.wapi.mock.dto;

import com.fasterxml.jackson.dataformat.xml.annotation.JacksonXmlProperty;
import com.fasterxml.jackson.dataformat.xml.annotation.JacksonXmlRootElement;

@JacksonXmlRootElement(localName="RSP")
public class GetAccountResponse extends RSP 
{
	@JacksonXmlProperty(isAttribute = false)
	public String accountId;
	
	@JacksonXmlProperty(isAttribute = false)
	public String country;

	@JacksonXmlProperty(isAttribute = false)
	public String gameSessionId;
	
	@JacksonXmlProperty(isAttribute = false)
	public String jurisdiction;

}
