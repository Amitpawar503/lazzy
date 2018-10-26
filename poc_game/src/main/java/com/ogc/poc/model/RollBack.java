package com.ogc.poc.model;

import org.springframework.data.annotation.Id;
import org.springframework.data.mongodb.core.mapping.Document;
@Document(collection="RollBack")
public class RollBack {
	
	private int apiVersion;
	@Id
	private String sessionId;
	private float balanceAmount;
	private String currencyCode;
	
	public int getApiVersion() {
		return apiVersion;
	}
	public void setApiVersion(int apiVersion) {
		this.apiVersion = apiVersion;
	}
	public String getSessionId() {
		return sessionId;
	}
	public void setSessionId(String sessionId) {
		this.sessionId = sessionId;
	}
	public float getBalanceAmount() {
		return balanceAmount;
	}
	public void setBalanceAmount(float balanceAmount) {
		this.balanceAmount = balanceAmount;
	}
	public String getCurrencyCode() {
		return currencyCode;
	}
	public void setCurrencyCode(String currencyCode) {
		this.currencyCode = currencyCode;
	}
	
	@Override
	public String toString() {
		return "RollBack [apiVersion=" + apiVersion + ", sessionId=" + sessionId + ", balanceAmount=" + balanceAmount
				+ ", currencyCode=" + currencyCode + "]";
	}
	
}
