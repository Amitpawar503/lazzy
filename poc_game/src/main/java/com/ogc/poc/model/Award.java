package com.ogc.poc.model;

public class Award
{
    private String content;

    private String index;

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

    @Override
    public String toString()
    {
        return "ClassPojo [content = "+content+", index = "+index+"]";
    }
}