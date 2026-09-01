import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { getGames, getPlayers } from '../api';
import Avatar from '../components/Avatar';
import { getPlayerStats } from '../components/PlayerHover';
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
  const profileRows = [
    ['Games played', stats.played],
    ['Wins', stats.wins],
    ['Losses', stats.losses],
    ['Deaths', stats.deaths],
    ['As Liberal', `${stats.liberal} (${stats.liberalWinRate}%)`],
    ['As Fascist', `${stats.fascist} (${stats.fascistWinRate}%)`],
    ['As Hitler', `${stats.hitler} (${stats.hitlerWinRate}%)`],
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
          <img src={avatarUrl(player.avatar_path)} alt={`${player.name}'s profile`} onClick={event => event.stopPropagation()} />
        </div>
      )}
    </div>
  );
}