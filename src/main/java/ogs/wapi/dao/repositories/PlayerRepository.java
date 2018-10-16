package ogs.wapi.dao.repositories;

import ogs.wapi.mock.dao.entities.Player;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.transaction.annotation.Transactional;

@Transactional
public interface PlayerRepository extends JpaRepository<Player, Long> 
{
	public Iterable<Player> getPlayerByPlayerId(final String playerId);
	public Iterable<Player> getPlayerByAccountId(final String accountId);
	public Iterable<Player> getPlayerByLoginSessionId(final String sessionId);
}
