package com.ogc.poc.model;

import javax.xml.bind.annotation.XmlAttribute;
import javax.xml.bind.annotation.XmlRootElement;

import com.fasterxml.jackson.dataformat.xml.annotation.JacksonXmlProperty;
import com.fasterxml.jackson.dataformat.xml.annotation.JacksonXmlRootElement;

@JacksonXmlRootElement
public class Reel {
	
	@JacksonXmlProperty(isAttribute = true, localName = "content")
	private String content;

	@JacksonXmlProperty(isAttribute = true, localName = "reelIndex")
	private String reelIndex;

	@JacksonXmlProperty(isAttribute = true, localName = "length")
	private String length;

	@JacksonXmlProperty(isAttribute = false, localName = "")
	private String value;

	public Reel(String s) {
		super();
	}

	public String getContent() {
		return content;
	}

	public void setContent(String content) {
		this.content = content;
	}

	public String getReelIndex() {
		return reelIndex;
	}

	public void setReelIndex(String reelIndex) {
		this.reelIndex = reelIndex;
	}

	public String getLength() {
		return length;
	}

	public void setLength(String length) {
		this.length = length;
	}

	
	public String getValue() {
		return value;
	}

	public void setValue(String value) {
		this.value = value;
	}

	@Override
	public String toString() {
		return "ClassPojo [content = " + content + ", reelIndex = " + reelIndex + ", length = " + length + "]";
	}
}
