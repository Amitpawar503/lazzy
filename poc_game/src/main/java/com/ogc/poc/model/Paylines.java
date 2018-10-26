package com.ogc.poc.model;

import com.fasterxml.jackson.dataformat.xml.annotation.JacksonXmlProperty;
import com.fasterxml.jackson.dataformat.xml.annotation.JacksonXmlRootElement;

@JacksonXmlRootElement
public class Paylines
{
	@JacksonXmlProperty(isAttribute = true)
	private String gameMode;

    private PaylineInfo payLineInfo;

    public String getGameMode ()
    {
        return gameMode;
    }

    public void setGameMode (String gameMode)
    {
        this.gameMode = gameMode;
    }

    public PaylineInfo getPaylineInfo ()
    {
        return payLineInfo;
    }

    public void setPaylineInfo (PaylineInfo PaylineInfo)
    {
        this.payLineInfo = PaylineInfo;
    }

    @Override
    public String toString()
    {
        return "ClassPojo [gameMode = "+gameMode+", PaylineInfo = "+payLineInfo+"]";
    }
}
			
	