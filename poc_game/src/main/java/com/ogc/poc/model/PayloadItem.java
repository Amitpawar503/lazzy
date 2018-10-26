package com.ogc.poc.model;
public class PayloadItem
{
    private String Payload;

    private String request;

    public String getPayload ()
    {
        return Payload;
    }

    public void setPayload (String Payload)
    {
        this.Payload = Payload;
    }

    public String getRequest ()
    {
        return request;
    }

    public void setRequest (String request)
    {
        this.request = request;
    }

    @Override
    public String toString()
    {
        return "ClassPojo [Payload = "+Payload+", request = "+request+"]";
    }
}