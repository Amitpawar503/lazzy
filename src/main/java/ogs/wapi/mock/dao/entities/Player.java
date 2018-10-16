package ogs.wapi.mock.dao.entities;

import javax.persistence.Column;
import javax.persistence.Entity;
import javax.persistence.GeneratedValue;
import javax.persistence.Id;
import javax.persistence.Table;

@Entity
@Table(name = "player", schema = "WIAPI")
public class Player 
{
    @Id
    @GeneratedValue
    @Column(name="player_id")
    private Long playerId;
    
    @Column(name="account_id")
    private String accountId;

    @Column(name="country")
    private String country;
    
    @Column(name="currency")
    private String currency;
    
    @Column(name="loginSessionId")
    private String loginSessionId;
    
    @Column(name="jurisdiction")
    private String jurisdiction;
    
    @Column(name="real_balance")
   private double realBalance;
    
    @Column(name="bonus_balance")
   private double bonusBalance;

    public Player(){}
    
    public Player(String country, String currency, String sessionId, String jurisdiction)
    {
    	this.country = country;
    	this.currency = currency;
    	this.loginSessionId = sessionId;
    	this.jurisdiction = jurisdiction;
    }
    
    public Long getPlayerId()
    {
    	return playerId;
    }
 
    public String getAccountId()
    {
    	return accountId;
    }
    
    public void setAccountId(String accountId)
    {
    	this.accountId = accountId;
    }
    
    public String getCountry()
    {
    	return country;
    }
    
    public void setCountry(String country)
    {
    	this.country = country;
    }
    
    public String getCurrency()
    {
    	return currency;
    }
    
    public void setCurrency(String currency)
    {
    	this.currency = currency;
    }
    
    public String getLoginSessionId()
    {
    	return loginSessionId;
    }
    
    public void setLoginSessionId(String loginSessionId)
    {
    	this.loginSessionId = loginSessionId;
    }
    
    public String getJurisdiction()
    {
    	return jurisdiction;
    }
    
    public void setJurisdiction(String jurisdiction)
    {
    	this.jurisdiction = jurisdiction;
    }
    
    public double getRealBalance()
    {
    	return realBalance;
    }
    
    public void setRealBalance(double realBalance)
    {
    	this.realBalance = realBalance;
    }	   
    
    public double getBonusBalance()
    {
    	return bonusBalance;
    }
    
    public void setBonusBalance(double bonusBalance)
    {
    	this.bonusBalance = bonusBalance;
    }	   	    
}

