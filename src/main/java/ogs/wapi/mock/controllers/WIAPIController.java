package ogs.wapi.mock.controllers;

import java.util.Iterator;
import java.util.List;

import ogs.wapi.mock.dao.entities.GameRound;
import ogs.wapi.mock.dao.entities.GameTransaction;
import ogs.wapi.mock.dao.entities.TransactionType;
import ogs.wapi.mock.dto.*;
import ogs.wapi.mock.services.OGSException;
import ogs.wapi.mock.services.PlayerService;
import ogs.wapi.mock.services.TransactionService;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;




@RestController
@RequestMapping("/wiapi")
public class WIAPIController 
{
	
	@Autowired
	PlayerService playerService;
	
	@Autowired
	TransactionService transactionService;

	@GetMapping("/ping")
	public String Ping() {
		return "Pong";
	}
	
	//https://operatorwalletplatform/path/to/wallet?request=getaccount&loginname=no
		//gsuser&password=qwerty&apiversion=1.3&sessionid=CF125F-1624-FDGC21-102562&dev
		//ice=desktop&product=casino&gametype=slots&gamemodel=5reels&gpid=100&nogsgamei
		//d=70002&currency=EUR
	@GetMapping("/mockapi")
	public RSP getResponse(@RequestParam String request,
			String loginname, String password, String apiversion, String sessionid,
			String device, String product, String gametype, String gamemodel, 
			String gpid, String nogsgameid,String currency, String accountid,
			String gamesessionid, Double betamount, Long roundid, Long transactionid,
			Double wonamount, String gamestatus, Double rollbackamount) 
	{
		ogs.wapi.mock.dao.entities.Player player = null;
		try
		{
			if(request.equalsIgnoreCase("getaccount"))
			{
				player = playerService.getPlayerBySessionId(sessionid);
			}
			else
			{
				player = playerService.getPlayerByAccountId(accountid);
			}
		}
		catch (Exception ex)
		{
			return getErrorResponse(1,ex.getMessage(),request);
		}
		
		if(player == null)
		{
			return getErrorResponse(1000,"The player’s session id/ account id is invalid",request);
		}
		
		if(sessionid != null && !sessionid.isEmpty() &&!player.getLoginSessionId().equalsIgnoreCase(sessionid))
		{
			return getErrorResponse(1000,"The player’s session is Expired",request);
		}
		
		if(gamesessionid != null && !gamesessionid.isEmpty() &&!player.getLoginSessionId().equalsIgnoreCase(gamesessionid))
		{
			return getErrorResponse(1000,"The player’s session is Expired",request);
		}

		if(!player.getCurrency().equalsIgnoreCase(currency) && currency !="" && currency!=null)
		{
			return getErrorResponse(1007,"Currency mismatch",request);
		}
		
		switch(request)
		{
			case "getaccount":
				return getAccountResponse(player);
			case "getbalance":
				return getBalanceResponse(player);
			case "wager":
				return getWagerResponse(player, betamount, roundid, transactionid );
			case "result":
				return getResultResponse(player, wonamount, roundid, transactionid );
			case "rollback":
				return getRollbackResponse(player, rollbackamount, roundid, transactionid );
			default:
				throw new OGSException();
		}
		
	}
	
	private GetAccountResponse getAccountResponse(ogs.wapi.mock.dao.entities.Player player)
	{
		GetAccountResponse response = new GetAccountResponse();
		response.rc = 0;
		response.apiVersion="1.5";
		response.country = player.getCountry();
		response.gameSessionId = player.getLoginSessionId();
		response.jurisdiction = player.getJurisdiction();
		response.request = "getaccount";
		response.accountId = player.getAccountId();
		
		return response;
	}
	
	private GetBalanceResponse getBalanceResponse(ogs.wapi.mock.dao.entities.Player player)
	{
		GetBalanceResponse response = new GetBalanceResponse();
		response.rc = 0;
		response.apiVersion="1.5";
		response.request = "getbalance";
		response.RealBalance = player.getRealBalance();
		response.BonusBalance = player.getBonusBalance();
		response.currency = player.getCurrency();
		return response;
	}	

	private WagerResponse getWagerResponse(ogs.wapi.mock.dao.entities.Player player, 
			double betAmount, Long roundId, Long transId)
	{
		GameRound gRound = transactionService.getGameRoundByRoundId(roundId);
		WagerResponse response = new WagerResponse();
		response.rc = 0;
		response.apiVersion="1.5";
		response.request = "wager";
		response.currency = player.getCurrency();
		if(gRound != null)
		{
			if(gRound.getGameStatus() != null && gRound.getGameStatus().equalsIgnoreCase("completed") == true)
			{
				OGSException ex = new OGSException();
				ex.setMsg("Operation not allowed");
				ex.setRc(110);
				ex.setRequest("wager");
				throw ex;
			
			}
			Iterator<GameTransaction> iterator = gRound.getTransactions().iterator();
			GameTransaction trans = null;
			boolean transFound = false;
			while(iterator.hasNext() && (trans = (GameTransaction) iterator.next())!=null)
			{
				Long test3 = trans.getTransactionId();
				boolean test1 = trans.getTransactionId().longValue() == transId.longValue();
				boolean test2 = trans.getTransactionType() == TransactionType.wager;
				if(trans.getTransactionId().longValue() == transId.longValue() && trans.getTransactionType() == TransactionType.wager)
				{
					transFound = true;
					break;
				}
			}
			
			if(!transFound)
			{
				OGSException ex = new OGSException();
				ex.setMsg("Incorrect Transaction Id");
				ex.setRc(102);
				ex.setRequest("wager");
				throw ex;
			}
			
			response.bonusMoneyBet = trans.getBonusbet();
			response.realMoneyBet = trans.getRealbet();
		}
		else
		{
			if(betAmount > player.getRealBalance()&& betAmount>(player.getRealBalance()+player.getBonusBalance()))
			{
				OGSException ex = new OGSException();
				ex.setMsg("Insufficient fund");
				ex.setRc(1006);
				ex.setRequest("wager");
				throw ex;
			}
			
			double realBalance = player.getRealBalance() - betAmount;
			if(realBalance < 0)
			{
				player.setBonusBalance(player.getBonusBalance() - realBalance);
				player.setRealBalance(0);
				response.bonusMoneyBet =  -1*realBalance;
				response.realMoneyBet = betAmount -  response.bonusMoneyBet;
			}
			else
			{
				player.setRealBalance(realBalance);
				response.bonusMoneyBet =  0;
				response.realMoneyBet = betAmount;
			}
			GameRound gRound2 =  new GameRound();
			gRound2.setAccountId(player.getAccountId());
			gRound2.setGameRoundId(roundId);
			gRound2.setGameSessionId(player.getLoginSessionId());
			
			GameTransaction trans1 = new GameTransaction();
			trans1.setAmount(betAmount);
			trans1.setBonusbet(response.bonusMoneyBet);
			trans1.setRealbet(response.realMoneyBet);
			trans1.setTransactionId(transId);
			trans1.setTransactionType(TransactionType.wager);
			gRound2.addTransaction(trans1);
			gRound2.setGameStatus("pending");
			transactionService.save(gRound2);
			playerService.save(player);
			
		}
		
		response.realBalance = player.getRealBalance();
		response.bonusBalance = player.getBonusBalance();

		return response;
	}	

	
	private ResultResponse getResultResponse(ogs.wapi.mock.dao.entities.Player player, 
			double wonAmount, Long roundId, Long transId)
	{
		ResultResponse response = new ResultResponse();
		response.rc = 0;
		response.apiVersion="1.5";
		response.request = "result";
		response.currency = player.getCurrency();
		response.totalAmount = wonAmount;
		GameRound gRound = transactionService.getGameRoundByRoundId(roundId);
		if(gRound != null)
		{
			if(gRound.getGameStatus() != null && gRound.getGameStatus().equalsIgnoreCase("completed") == true
					&& gRound.getCloseTransactionType() != TransactionType.result)
			{
				OGSException ex = new OGSException();
				ex.setMsg("Operation not allowed");
				ex.setRc(110);
				ex.setRequest("result");
				throw ex;
			
			}
			Iterator<GameTransaction> iterator = gRound.getTransactions().iterator();
			GameTransaction trans = null;
			boolean transFound = false;
			while(iterator.hasNext() && (trans = (GameTransaction) iterator.next())!=null)
			{
				if(trans.getTransactionId().longValue() == transId.longValue() && trans.getTransactionType() == TransactionType.result)
				{
					transFound = true;
					break;
				}
			}
			
			if(!transFound)
			{
				trans =  new GameTransaction();
				trans.setAmount(wonAmount);
				trans.setTransactionId(transId);
				trans.setTransactionType(TransactionType.result);
				gRound.addTransaction(trans);
				gRound.setGameStatus("completed");
				gRound.setCloseTransactionType(TransactionType.result);
				transactionService.save(gRound);
				
				player.setRealBalance(player.getRealBalance()+wonAmount);
				playerService.save(player);
				
			}
		
		}
		else
		{
			OGSException ex = new OGSException();
			ex.setMsg("Wager not found");
			ex.setRc(102);
			ex.setRequest("result");
			throw ex;
			
		}
		
		response.realBalance = player.getRealBalance();
		response.bonusBalance = player.getBonusBalance();

		return response;
	}	

	
	private RollbackResponse getRollbackResponse(ogs.wapi.mock.dao.entities.Player player,
			double rollbackAmount, Long roundId, Long transId)
	{
		RollbackResponse response = new RollbackResponse();
		response.rc = 0;
		response.apiVersion="1.5";
		response.request = "rollback";
		response.currency = player.getCurrency();
		GameRound gRound = transactionService.getGameRoundByRoundId(roundId);
		if(gRound != null)
		{
			if(gRound.getGameStatus() != null && gRound.getGameStatus().equalsIgnoreCase("completed") == true
					&& gRound.getCloseTransactionType() != TransactionType.rollback)
			{
				OGSException ex = new OGSException();
				ex.setMsg("Operation not allowed");
				ex.setRc(110);
				ex.setRequest("result");
				throw ex;
			
			}
			Iterator<GameTransaction> iterator = gRound.getTransactions().iterator();
			GameTransaction trans = null;
			boolean transFound = false;
			while(iterator.hasNext() && (trans = (GameTransaction) iterator.next())!=null)
			{
				if(trans.getTransactionId().longValue() == transId.longValue() && trans.getTransactionType() == TransactionType.result)
				{
					transFound = true;
					break;
				}
			}
			
			if(!transFound)
			{
				trans =  new GameTransaction();
				trans.setAmount(rollbackAmount);
				trans.setTransactionId(transId);
				trans.setTransactionType(TransactionType.rollback);
				gRound.addTransaction(trans);
				gRound.setCloseTransactionType(TransactionType.rollback);
				gRound.setGameStatus("completed");
				
				transactionService.save(gRound);
				
				player.setRealBalance(player.getRealBalance()+rollbackAmount);
				playerService.save(player);
				
			}
		
		}
		else
		{
			OGSException ex = new OGSException();
			ex.setMsg("Wager not found");
			ex.setRc(102);
			ex.setRequest("result");
			throw ex;
			
		}
		
		response.realBalance = player.getRealBalance();
		response.bonusBalance = player.getBonusBalance();
		return response;
	}	

	private OGSError getErrorResponse(Integer rc, String message, String request)
	{
		OGSError response = new OGSError();
		response.rc = rc;
		response.apiVersion="1.5";
		response.request = request;
		response.msg = message;
		return response;
	}		

}
