import { useEffect, useState } from 'react';
import { getGames, getPlayers, deleteGame } from '../api';
import Avatar from '../components/Avatar';
import styles from './History.module.css';

function roleClass(role) {
  return role === 'hitler' ? 'role-hitler' : role === 'fascist' ? 'role-fascist' : 'role-liberal';
}

function GameCard({ game, playerMap, onDelete }) {
  const [open, setOpen] = useState(false);
  const date = new Date(game.date).toLocaleDateString(undefined, { dateStyle: 'medium' });
  const teamLabel = game.winning_team === 'liberal' ? 'Liberal' : 'Fascist';
  const condLabel = {
    policies_enacted: 'Policies Enacted',
    hitler_elected: 'Hitler Elected',
    hitler_executed: 'Hitler Executed',
  }[game.winning_condition];

  return (
    <div className={styles.card}>
      <div className={styles.cardHeader} onClick={() => setOpen(o => !o)}>
        <span className={styles.date}>{date}</span>
        <span className={`${styles.team} ${game.winning_team === 'liberal' ? styles.liberal : styles.fascist}`}>
          {teamLabel} Win
        </span>
        <span className={styles.cond}>{condLabel}</span>
        <span className={styles.chevron}>{open ? '▲' : '▼'}</span>
      </div>
      {open && (
        <div className={styles.cardBody}>
          <div className={styles.playerList}>
            {game.players.map(pr => {
              const p = playerMap[pr.player_id];
              return (
                <div key={pr.player_id} className={styles.playerRow}>
                  <Avatar path={p?.avatar_path} name={p?.name ?? '?'} size={32} />
                  <span className={styles.pname}>{p?.name ?? 'Unknown'}</span>
                  <span className={`${styles.role} ${roleClass(pr.role)}`}>{pr.role}</span>
                  {pr.died && <span className={styles.died}>✝</span>}
                </div>
              );
            })}
          </div>
          <div className={styles.cardFooter}>
            <button className="btn-danger" onClick={() => onDelete(game.id)}>Delete</button>
          </div>
        </div>
      )}
    </div>
  );
}

export default function History() {
  const [games, setGames] = useState([]);
  const [playerMap, setPlayerMap] = useState({});

  async function load() {
    const [g, p] = await Promise.all([getGames(), getPlayers()]);
    setGames([...g].reverse());
    setPlayerMap(Object.fromEntries(p.map(pl => [pl.id, pl])));
  }

  useEffect(() => { load(); }, []);

  async function handleDelete(id) {
    if (!confirm('Delete this game?')) return;
    await deleteGame(id);
    setGames(gs => gs.filter(g => g.id !== id));
  }

  return (
    <div className={styles.page}>
      <h1>Game History</h1>
      {games.length === 0 && <p style={{ color: 'var(--text-dim)', marginTop: '1rem' }}>No games recorded yet.</p>}
      <div className={styles.list}>
        {games.map(g => (
          <GameCard key={g.id} game={g} playerMap={playerMap} onDelete={handleDelete} />
        ))}
      </div>
    </div>
  );
}
