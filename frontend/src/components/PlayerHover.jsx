import { useState } from 'react';
import { createPortal } from 'react-dom';
import { useNavigate } from 'react-router-dom';
import Avatar from './Avatar';
import styles from './PlayerHover.module.css';

export function getPlayerStats(playerId, games) {
  let liberal = 0;
  let fascist = 0;
  let hitler = 0;
  let wins = 0;
  let losses = 0;
  let deaths = 0;
  let played = 0;
  let liberalWins = 0;
  let fascistWins = 0;
  let hitlerWins = 0;

  for (const game of games) {
    const result = game.players.find(entry => entry.player_id === playerId);
    if (!result) continue;

    played++;
    if (result.role === 'liberal') liberal++;
    if (result.role === 'fascist') fascist++;
    if (result.role === 'hitler') hitler++;
    if (result.died) deaths++;

    const won = (result.role === 'liberal' && game.winning_team === 'liberal') ||
      ((result.role === 'fascist' || result.role === 'hitler') && game.winning_team === 'fascist');
    if (won) {
      wins++;
      if (result.role === 'liberal') liberalWins++;
      if (result.role === 'fascist') fascistWins++;
      if (result.role === 'hitler') hitlerWins++;
    } else {
      losses++;
    }
  }

  const rate = (won, total) => total ? Math.round(won / total * 100) : 0;
  return {
    played, wins, losses, deaths, liberal, fascist, hitler,
    liberalWins, fascistWins, hitlerWins,
    winRate: rate(wins, played),
    liberalWinRate: rate(liberalWins, liberal),
    fascistWinRate: rate(fascistWins, fascist),
    hitlerWinRate: rate(hitlerWins, hitler),
  };
}

export default function PlayerHover({ player, games = [], children }) {
  const navigate = useNavigate();
  const [popupPosition, setPopupPosition] = useState(null);

  function showPopup(event) {
    setPopupPosition({
      top: event.clientY + 12,
      left: Math.max(8, Math.min(event.clientX + 12, window.innerWidth - 240)),
    });
  }

  function openProfile(event) {
    event.stopPropagation();
    navigate(`/players/${player.id}`);
  }

  const stats = getPlayerStats(player.id, games);

  return (
    <>
      <div className={styles.anchor} onMouseEnter={showPopup} onMouseLeave={() => setPopupPosition(null)} onClick={openProfile}>
        {children}
      </div>
      {popupPosition && createPortal(
        <div className={styles.popup} style={popupPosition} role="tooltip">
          <Avatar path={player.avatar_path} name={player.name} size={80} />
          <strong className={styles.name}>{player.name}</strong>
          <div className={styles.stats}>
            <div><strong>{stats.liberal}</strong><span>Liberal</span></div>
            <div><strong>{stats.fascist}</strong><span>Fascist</span></div>
            <div><strong>{stats.winRate}%</strong><span>Win rate</span></div>
          </div>
        </div>,
        document.body,
      )}
    </>
  );
}