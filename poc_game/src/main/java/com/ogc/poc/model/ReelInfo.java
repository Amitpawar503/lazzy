package com.ogc.poc.model;

import java.util.List;

import com.fasterxml.jackson.dataformat.xml.annotation.JacksonXmlProperty;
import com.fasterxml.jackson.dataformat.xml.annotation.JacksonXmlRootElement;

@JacksonXmlRootElement
public class ReelInfo {

    @JacksonXmlProperty(isAttribute = true, localName = "numReelSets")
	private String numReelSets;

    
	private List<ReelSet> ReelSet;

	public String getNumReelSets() {
		return numReelSets;
	}

	public void setNumReelSets(String numReelSets) {
		this.numReelSets = numReelSets;
	}

	public List<ReelSet> getReelSet() {
		return ReelSet;
	}

	public void setReelSet(List<ReelSet> reelSet) {
		ReelSet = reelSet;
	}

	@Override
	public String toString() {
		return "ClassPojo [numReelSets = " + numReelSets + ", ReelSet = " + ReelSet + "]";
	}
}
