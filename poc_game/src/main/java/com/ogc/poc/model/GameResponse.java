package com.ogc.poc.model;

import java.util.List;

import com.fasterxml.jackson.dataformat.xml.annotation.JacksonXmlRootElement;

@JacksonXmlRootElement(localName="GameResponse")
public class GameResponse {

	public String type;

	public String getType() {
		return type;
	}

	public void setType(String type) {
		this.type = type;
	}

	@Override
	public String toString() {
		return "GameResponse [type=" + type + "]";
	}
	
	public List<String> reels;
	
}
