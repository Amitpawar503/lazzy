package ogs.wapi.mock.controllers;



import ogs.wapi.mock.dto.Player;
import ogs.wapi.mock.services.PlayerService;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/player")
public class PlayerController 
{
	@Autowired
	PlayerService playerService;
	
	

	
	@GetMapping("/ping")
	public String Ping() 
	{
		return "Pong";
	}
	
	@GetMapping("/getPlayerBySessionId/{sessionId}")
	public Player getPlayerBySessionId(@PathVariable String sessionId) 
	{
		ogs.wapi.mock.dao.entities.Player playerEntity = playerService.getPlayerBySessionId(sessionId);
		Player response = new Player();
		response.setCountry(playerEntity.getCountry());
		response.setCurrency(playerEntity.getCurrency());
		response.setJurisdiction(playerEntity.getJurisdiction());
		response.setLoginSessionId(playerEntity.getLoginSessionId());
		response.setPlayerId(playerEntity.getPlayerId());
		response.setAccountId(playerEntity.getAccountId());
		response.setRealBalance(playerEntity.getRealBalance());
		response.setBonusBalance(playerEntity.getBonusBalance());
		return response;
	}
	
	@GetMapping("/getPlayerByAccountId/{accountId}")
	public Player getPlayerByAccountId(@PathVariable String accountId) 
	{
		ogs.wapi.mock.dao.entities.Player playerEntity = playerService.getPlayerByAccountId(accountId);
		Player response = new Player();
		response.setCountry(playerEntity.getCountry());
		response.setCurrency(playerEntity.getCurrency());
		response.setJurisdiction(playerEntity.getJurisdiction());
		response.setLoginSessionId(playerEntity.getLoginSessionId());
		response.setPlayerId(playerEntity.getPlayerId());
		response.setAccountId(playerEntity.getAccountId());
		response.setRealBalance(playerEntity.getRealBalance());
		response.setBonusBalance(playerEntity.getBonusBalance());
		return response;
	}
	
	@PostMapping("/addPlayer")
	public boolean addPlayer(@RequestBody Player player) 
	{   
		ogs.wapi.mock.dao.entities.Player playerEntity = new ogs.wapi.mock.dao.entities.Player();
		playerEntity.setCountry(player.getCountry());
		playerEntity.setCurrency(player.getCurrency());
		playerEntity.setJurisdiction(player.getJurisdiction());
		playerEntity.setLoginSessionId(player.getLoginSessionId());
		playerEntity.setAccountId(player.getAccountId());
		playerEntity.setRealBalance(player.getRealBalance());
		playerEntity.setBonusBalance(player.getBonusBalance());
		playerService.save(playerEntity);
		return true;
	}
	
	@PutMapping("/updatePlayer")
	public boolean updatePlayer(@RequestBody Player player) 
	{
		ogs.wapi.mock.dao.entities.Player playerEntity = new ogs.wapi.mock.dao.entities.Player();
		playerEntity.setCountry(player.getCountry());
		playerEntity.setCurrency(player.getCurrency());
		playerEntity.setJurisdiction(player.getJurisdiction());
		playerEntity.setLoginSessionId(player.getLoginSessionId());
		playerEntity.setAccountId(player.getAccountId());
		playerEntity.setRealBalance(player.getRealBalance());
		playerEntity.setBonusBalance(player.getBonusBalance());
		playerService.save(playerEntity);
		return true;
	}
	
}
