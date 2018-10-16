package ogs.wapi.mock.services;

import java.util.UUID;

import ogs.wapi.mock.dao.entities.Player;
import ogs.wapi.dao.repositories.PlayerRepository;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.repository.CrudRepository;
import org.springframework.stereotype.Component;
import org.springframework.stereotype.Service;

@Service
@Component
public class PlayerService implements GenericService<Player, Long>
{

	@Autowired
	private PlayerRepository playerRepository;
	
	@Override
	public Long getId(Player entity) {
		return entity.getPlayerId();
	}
	
	@Override
	public Player save(Player entity) {
		return GenericService.super.save(entity);
	}

	@Override
	public CrudRepository<Player, Long> getRepository() 
	{
		return playerRepository;
	}
	
	public Player getPlayerBySessionId(String sessionId) {
		return playerRepository.getPlayerByLoginSessionId(sessionId).iterator().next();
	}
	
	public Player getPlayerByAccountId(String accountId) {
		return playerRepository.getPlayerByAccountId(accountId).iterator().next();
	}
	
}
