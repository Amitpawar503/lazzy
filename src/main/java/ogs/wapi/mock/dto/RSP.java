package ogs.wapi.mock.dto;

import com.fasterxml.jackson.dataformat.xml.annotation.JacksonXmlProperty;
import com.fasterxml.jackson.dataformat.xml.annotation.JacksonXmlRootElement;

@JacksonXmlRootElement(localName="RSP")
public class RSP 
{
	@JacksonXmlProperty(isAttribute = true, localName = "request")
	public String request;
	
	@JacksonXmlProperty(isAttribute = true, localName = "rc")
	public Integer rc;

	@JacksonXmlProperty(isAttribute = true, localName = "msg")
	public String msg;
	
	@JacksonXmlProperty(isAttribute = false)
	public String apiVersion;
	
}
