package ogs.wapi.mock.services;

import ogs.wapi.dao.repositories.GameroundRepository;
import ogs.wapi.mock.dao.entities.GameRound;
import ogs.wapi.mock.dao.entities.Player;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.repository.CrudRepository;
import org.springframework.stereotype.Component;
import org.springframework.stereotype.Service;

@Service
@Component
public class TransactionService  implements GenericService<GameRound, Long>
{

	@Autowired
	private GameroundRepository gameRoundRepository;
	
	@Override
	public Long getId(GameRound entity) 
	{
		return entity.getId();
	}

	@Override
	public GameRound save(GameRound entity) {
		return GenericService.super.save(entity);
	}
	
	@Override
	public CrudRepository<GameRound, Long> getRepository() 
	{
		return gameRoundRepository;
	}
	
	public GameRound getGameRoundByRoundId(Long roundId)
	{
		Iterable<GameRound> gameroundList = gameRoundRepository.getGameRoundByGameRoundId(roundId);
		GameRound gRound = null;
		if(gameroundList != null)
		{
			if(gameroundList.iterator() != null && gameroundList.iterator().hasNext() )
			{
				gRound = gameroundList.iterator().next();
			}
		}
		return gRound;
	}

}
