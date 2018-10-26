package com.ogc.poc.model;

import com.fasterxml.jackson.dataformat.xml.annotation.JacksonXmlProperty;

public class Payline
{
	@JacksonXmlProperty(isAttribute=true)
    private String content;

	@JacksonXmlProperty(isAttribute=true)
    private String index;

	@JacksonXmlProperty(isAttribute=true)
    private String selectable;
    
	@JacksonXmlProperty(isAttribute=false)
    private String value;

    public String getContent ()
    {
        return content;
    }

    public void setContent (String content)
    {
        this.content = content;
    }

    public String getIndex ()
    {
        return index;
    }

    public void setIndex (String index)
    {
        this.index = index;
    }

    public String getSelectable ()
    {
        return selectable;
    }

    public void setSelectable (String selectable)
    {
        this.selectable = selectable;
    }

	public String getValue() {
		return value;
	}

	public void setValue(String value) {
		this.value = value;
	}


}
