package com.ogc.poc.model;

public class EndGameResponse {

	
	private String msg;
	private Double balance;
	private String currency;
	public String getMsg() {
		return msg;
	}
	public void setMsg(String msg) {
		this.msg = msg;
	}
	public Double getBalance() {
		return balance;
	}
	public void setBalance(Double balance) {
		this.balance = balance;
	}
	public String getCurrency() {
		return currency;
	}
	public void setCurrency(String currency) {
		this.currency = currency;
	}
	@Override
	public String toString() {
		return "EndGameResponse [msg=" + msg + ", balance=" + balance + ", currency=" + currency + "]";
	}
	
	
}
