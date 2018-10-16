package ogs.wapi.dao.repositories;

import ogs.wapi.mock.dao.entities.GameRound;
import ogs.wapi.mock.dao.entities.Player;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.transaction.annotation.Transactional;

@Transactional
public interface GameroundRepository  extends JpaRepository<GameRound, Long>
{
	public Iterable<GameRound> getGameRoundByGameRoundId(final Long gameroundId);
}
