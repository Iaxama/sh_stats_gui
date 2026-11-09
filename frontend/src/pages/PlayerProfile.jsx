import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { getGames, getPlayers } from '../api';
import Avatar from '../components/Avatar';
import { getPlayerStats } from '../components/PlayerHover';
import { calculateGamePercentage } from '../utils/statistics';
import styles from './PlayerProfile.module.css';

function avatarUrl(path) {
  return `/avatars/${path.split('/').pop()}`;
}

export default function PlayerProfile() {
  const { playerId } = useParams();
  const [player, setPlayer] = useState(null);
  const [games, setGames] = useState([]);
  const [imageOpen, setImageOpen] = useState(false);

  useEffect(() => {
    Promise.all([getPlayers(), getGames()]).then(([players, loadedGames]) => {
      setPlayer(players.find(candidate => candidate.id === playerId) ?? null);
      setGames(loadedGames);
    });
  }, [playerId]);

  if (!player) {
    return <div className={styles.page}><p>Loading player...</p></div>;
  }

  const stats = getPlayerStats(player.id, games);
  const formatCount = count => `${count} (${calculateGamePercentage(count, stats.played)}%)`;
  const profileRows = [
    ['Games played', stats.played],
    ['Wins', formatCount(stats.wins)],
    ['Losses', formatCount(stats.losses)],
    ['Deaths', formatCount(stats.deaths)],
    ['Sniper', formatCount(stats.snipers)],
    ['Dumbo', formatCount(stats.dumbo)],
    ['Dictator', formatCount(stats.dictator)],
    ['As Liberal', formatCount(stats.liberal)],
    ['Liberal wins', formatCount(stats.liberalWins)],
    ['As Fascist', formatCount(stats.fascist)],
    ['Fascist wins', formatCount(stats.fascistWins)],
    ['As Hitler', formatCount(stats.hitler)],
    ['Hitler wins', formatCount(stats.hitlerWins)],
    ['Win rate', `${stats.winRate}%`],
  ];

  return (
    <div className={styles.page}>
      <Link className={styles.back} to="/players">Back to Players</Link>
      <section className={styles.profile}>
        <button className={styles.avatarButton} type="button" onClick={() => player.avatar_path && setImageOpen(true)} disabled={!player.avatar_path}>
          <Avatar path={player.avatar_path} name={player.name} size={150} />
        </button>
        <h1>{player.name}</h1>
        <div className={styles.stats}>
          {profileRows.map(([label, value]) => (
            <div key={label} className={styles.stat}><strong>{value}</strong><span>{label}</span></div>
          ))}
        </div>
      </section>
      {imageOpen && (
        <div className={styles.lightbox} role="dialog" aria-modal="true" onClick={() => setImageOpen(false)}>
          <img src={avatarUrl(player.avatar_full_path || player.avatar_path)} alt={`${player.name}'s profile`} onClick={event => event.stopPropagation()} />
        </div>
      )}
    </div>
  );
}
