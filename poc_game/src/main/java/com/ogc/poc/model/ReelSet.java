package com.ogc.poc.model;

import java.util.List;

import com.fasterxml.jackson.dataformat.xml.annotation.JacksonXmlProperty;
import com.fasterxml.jackson.dataformat.xml.annotation.JacksonXmlRootElement;

@JacksonXmlRootElement
public class ReelSet
{
	@JacksonXmlProperty(isAttribute = true, localName = "featIndex")
    private String featIndex;

	@JacksonXmlProperty(isAttribute = true, localName = "reelSetIndex")
    private String reelSetIndex;

    @JacksonXmlProperty(isAttribute = true, localName = "numReels")
    private String numReels;
    
    private List<Reel> reel;

    public String getFeatIndex ()
    {
        return featIndex;
    }

    public void setFeatIndex (String featIndex)
    {
        this.featIndex = featIndex;
    }

    public String getReelSetIndex ()
    {
        return reelSetIndex;
    }

    public void setReelSetIndex (String reelSetIndex)
    {
        this.reelSetIndex = reelSetIndex;
    }


    public String getNumReels ()
    {
        return numReels;
    }

    public void setNumReels (String numReels)
    {
        this.numReels = numReels;
    }

	public List<Reel> getReel() {
		return reel;
	}

	public void setReel(List<Reel> reel) {
		this.reel = reel;
	}

	@Override
	public String toString() {
		return "ReelSet [featIndex=" + featIndex + ", reelSetIndex=" + reelSetIndex + ", reel=" + reel + ", numReels="
				+ numReels + "]";
	}

 
}
			
			