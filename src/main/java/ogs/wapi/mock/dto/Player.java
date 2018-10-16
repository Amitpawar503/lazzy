package ogs.wapi.mock.dto;

public class Player 
{
	    private Long playerId;
	    
	    private String accountId;

	    private String country;
	    
	    private String currency;
	    
	    private String loginSessionId;
	    
	    private String jurisdiction;
	    
	    private double realBalance;
	    
	    private double bonusBalance;

	    public Player(){}
	    
	    public Player(String accountId, String country, String currency, String sessionId, String jurisdiction,
	    		double realBalance, double bonusBalance)
	    {
	    	this.accountId = accountId;
	    	this.country = country;
	    	this.currency = currency;
	    	this.loginSessionId = sessionId;
	    	this.jurisdiction = jurisdiction;
	    	this.realBalance = realBalance;
	    	this.bonusBalance = bonusBalance;
	    }
	    
	    public Long getPlayerId()
	    {
	    	return playerId;
	    }
	    
	    public void setPlayerId(Long playerId)
	    {
	    	this.playerId = playerId;
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
