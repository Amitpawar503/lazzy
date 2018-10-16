package ogs.wapi.mock.dao.entities;

import java.util.Date;

import javax.persistence.Column;
import javax.persistence.Embeddable;
import javax.persistence.JoinColumn;

@Embeddable
public class GameTransaction 
{

    @Column(name="trans_id")
    private Long transactionId;
    @Column(name="trans_type")
	private TransactionType transactionType;
    @Column(name="amount")
	private double amount;
    @Column(name="start_time")
	private Date start;
    @Column(name="end_time")
	private Date end;
	
    @Column(name="real_bet")
	private double realbet;
    
    @Column(name="bonus_bet")
	private double bonusbet;

    public Long getTransactionId() {
		return transactionId;
	}
	public void setTransactionId(Long transactionId) {
		this.transactionId = transactionId;
	}
	public TransactionType getTransactionType() {
		return transactionType;
	}
	public void setTransactionType(TransactionType transactionType) {
		this.transactionType = transactionType;
	}
	public double getAmount() {
		return amount;
	}
	public void setAmount(double amount) {
		this.amount = amount;
	}
	public Date getStart() {
		return start;
	}
	public void setStart(Date start) {
		this.start = start;
	}
	public Date getEnd() {
		return end;
	}
	public void setEnd(Date end) {
		this.end = end;
	}
	public double getRealbet() {
		return realbet;
	}
	public void setRealbet(double realbet) {
		this.realbet = realbet;
	}
	public double getBonusbet() {
		return bonusbet;
	}
	public void setBonusbet(double bonusbet) {
		this.bonusbet = bonusbet;
	}
}
