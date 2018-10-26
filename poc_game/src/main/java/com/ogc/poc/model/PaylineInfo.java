package com.ogc.poc.model;

import java.util.List;

import com.fasterxml.jackson.dataformat.xml.annotation.JacksonXmlProperty;
import com.fasterxml.jackson.dataformat.xml.annotation.JacksonXmlRootElement;

@JacksonXmlRootElement
public class PaylineInfo {

	@JacksonXmlProperty(isAttribute = true, localName = "default")
	private Integer default1;

	@JacksonXmlProperty(isAttribute = true)
	private String paylineCount;

	private List<Payline> payLine;

	public String getPaylineCount() {
		return paylineCount;
	}

	public void setPaylineCount(String paylineCount) {
		this.paylineCount = paylineCount;
	}

	public List<Payline> getPayLine() {
		return payLine;
	}

	public void setPayLine(List<Payline> payLine) {
		this.payLine = payLine;
	}

	public Integer getDefault1() {
		return default1;
	}

	public void setDefault1(Integer default1) {
		this.default1 = default1;
	}

	public PaylineInfo() {
		super();
	}

}
