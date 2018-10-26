package com.ogc.poc.model;

public class Payload
{
    private PayloadItem PayloadItem;

    public PayloadItem getPayloadItem ()
    {
        return PayloadItem;
    }

    public void setPayloadItem (PayloadItem PayloadItem)
    {
        this.PayloadItem = PayloadItem;
    }

    @Override
    public String toString()
    {
        return "ClassPojo [PayloadItem = "+PayloadItem+"]";
    }
}
