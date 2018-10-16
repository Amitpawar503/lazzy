package ogs.wapi.mock.dao.entities;

import java.util.ArrayList;
import java.util.Date;
import java.util.Iterator;
import java.util.List;

import javax.persistence.CollectionTable;
import javax.persistence.Column;
import javax.persistence.ElementCollection;
import javax.persistence.Entity;
import javax.persistence.GeneratedValue;
import javax.persistence.Id;
import javax.persistence.JoinColumn;
import javax.persistence.Table;
import javax.persistence.Temporal;
import javax.persistence.TemporalType;


@Entity
@Table(name = "game_rounds", schema = "WIAPI")
public class GameRound 
{
	public GameRound()
	{
		transactions = new ArrayList<GameTransaction>();
	}
	
    @Id
    @GeneratedValue
    @Column(name="round_id")
    private Long roundIndex;	
    
    @JoinColumn
    @Column(name="gameround_id")
    private Long gameRoundId;
    
    @Column(name="account_id")
	private String accountId;
    
    @Column(name="session_id")
	private String gameSessionId;
    
    @ElementCollection
    @CollectionTable(name = "game_transactions", joinColumns = @JoinColumn(name = "gameround_id"))    
    @Column(name="transactions")
	private List<GameTransaction> transactions;
    
    @Temporal(TemporalType.DATE)
    @Column(name="start_time")
 	private Date start;
    
    @Temporal(TemporalType.DATE)
    @Column(name="end_time")
	private Date end;
    
    @Column(name="game_status")
    private String gameStatus;
    
    @Column(name="closetrans_type")
	private TransactionType closeTransactionType;


	public Long getId() {
		return roundIndex;
	}
	
	public Long getGameRoundId() {
		return gameRoundId;
	}
	
	public List<GameTransaction> getTransactions() {
		return transactions;
	}

	public void setGameRoundId(Long gameRoundId) {
		this.gameRoundId = gameRoundId;
	}
	public String getAccountId() {
		return accountId;
	}
	public void setAccountId(String accountId) {
		this.accountId = accountId;
	}
	public String getGameSessionId() {
		return gameSessionId;
	}
	public void setGameSessionId(String gameSessionId) {
		this.gameSessionId = gameSessionId;
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
	
	public boolean addTransaction(GameTransaction transaction)
	{
		transactions.add(transaction);
		return true;
	}
	
	public boolean removeTransaction(GameTransaction transaction)
	{
		TransactionComparer<GameTransaction> itemComparer =  new TransactionComparer<GameTransaction>();
		itemComparer.trans1 = transaction;
		transactions.removeIf(itemComparer);
		return true;
	}
	
	public boolean updateTransaction(GameTransaction transaction)
	{
		removeTransaction(transaction);
		addTransaction(transaction);
		return true;
	}

	public String getGameStatus() {
		return gameStatus;
	}

	public void setGameStatus(String gameStatus) {
		this.gameStatus = gameStatus;
	}

	public TransactionType getCloseTransactionType() {
		return closeTransactionType;
	}

	public void setCloseTransactionType(TransactionType closeTransactionType) {
		this.closeTransactionType = closeTransactionType;
	}
}
