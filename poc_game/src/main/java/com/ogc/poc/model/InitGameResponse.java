package com.ogc.poc.model;

import java.util.List;

import javax.xml.bind.annotation.XmlAttribute;
import javax.xml.bind.annotation.XmlRootElement;

import com.fasterxml.jackson.dataformat.xml.annotation.JacksonXmlProperty;
import com.fasterxml.jackson.dataformat.xml.annotation.JacksonXmlRootElement;

@JacksonXmlRootElement(localName = "GameResponse")
public class InitGameResponse {

	@JacksonXmlProperty(isAttribute = true)
	public String type;

	public String getType() {
		return type;
	}

	public void setType(String type) {
		this.type = type;
	}

	ReelInfo ReelInfo;

	Paylines payLines;

	public ReelInfo getReelInfo() {
		return ReelInfo;
	}

	public void setReelInfo(ReelInfo reelInfo) {
		ReelInfo = reelInfo;
	}

	public Paylines getPayLines() {
		return payLines;
	}

	public void setPayLines(Paylines payLines) {
		this.payLines = payLines;
	}

	@Override
	public String toString() {
		return "InitGameResponse [type=" + type + ", ReelInfo=" + ReelInfo + ", payLines=" + payLines + "]";
	}

}
