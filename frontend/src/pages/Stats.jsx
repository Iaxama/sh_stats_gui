import { useEffect, useState } from 'react';
import { getGames, getPlayers } from '../api';
import Avatar from '../components/Avatar';
import PlayerHover from '../components/PlayerHover';
import styles from './Stats.module.css';

const ELO_WEIGHT = 5;

function computeStats(games, players) {
  const totals = { total: games.length, liberal: 0, fascist: 0, policies: 0, elected: 0, executed: 0 };
  const perPlayer = {};

  for (const p of players) {
    perPlayer[p.id] = { player: p, games: 0, wins: 0, deaths: 0, byRole: { liberal: { g: 0, w: 0 }, fascist: { g: 0, w: 0 }, hitler: { g: 0, w: 0 } } };
  }

  for (const g of games) {
    if (g.winning_team === 'liberal') totals.liberal++;
    else totals.fascist++;
    if (g.winning_condition === 'policies_enacted') totals.policies++;
    else if (g.winning_condition === 'hitler_elected') totals.elected++;
    else totals.executed++;

    for (const pr of g.players) {
      const row = perPlayer[pr.player_id];
      if (!row) continue;
      row.games++;
      const won = (g.winning_team === 'liberal' && pr.role === 'liberal') ||
                  (g.winning_team === 'fascist' && (pr.role === 'fascist' || pr.role === 'hitler'));
      if (won) row.wins++;
      if (pr.died) row.deaths++;
      const rb = row.byRole[pr.role];
      rb.g++;
      if (won) rb.w++;
    }
  }

  return { totals, perPlayer: Object.values(perPlayer) };
}

function calculateElo(wins, games, averageWinRate) {
  return (wins + ELO_WEIGHT * averageWinRate) / (games + ELO_WEIGHT) * 100;
}

const COLS = [
  { key: 'name', label: 'Player' },
  { key: 'games', label: 'Games' },
  { key: 'wins', label: 'Wins' },
  { key: 'winPct', label: 'Win %' },
  { key: 'elo', label: 'ELO' },
  { key: 'deaths', label: 'Deaths' },
  { key: 'libGames', label: 'Lib G' },
  { key: 'libWins', label: 'Lib W' },
  { key: 'fasGames', label: 'Fas G' },
  { key: 'fasWins', label: 'Fas W' },
  { key: 'hitGames', label: 'Hit G' },
  { key: 'hitWins', label: 'Hit W' },
];

export default function Stats() {
  const [games, setGames] = useState([]);
  const [players, setPlayers] = useState([]);
  const [sortKey, setSortKey] = useState('games');
  const [sortDir, setSortDir] = useState(-1);

  useEffect(() => {
    Promise.all([getGames(), getPlayers()]).then(([g, p]) => { setGames(g); setPlayers(p); });
  }, []);

  const { totals, perPlayer } = computeStats(games, players);
  const allPlayerGames = perPlayer.reduce((sum, player) => sum + player.games, 0);
  const allPlayerWins = perPlayer.reduce((sum, player) => sum + player.wins, 0);
  const averageWinRate = allPlayerGames ? allPlayerWins / allPlayerGames : 0;

  const rows = perPlayer.map(r => ({
    ...r,
    winPct: r.games ? Math.round(r.wins / r.games * 100) : 0,
    elo: calculateElo(r.wins, r.games, averageWinRate),
    libGames: r.byRole.liberal.g, libWins: r.byRole.liberal.w,
    fasGames: r.byRole.fascist.g, fasWins: r.byRole.fascist.w,
    hitGames: r.byRole.hitler.g,  hitWins: r.byRole.hitler.w,
  })).sort((a, b) => {
    const av = sortKey === 'name' ? a.player.name : a[sortKey];
    const bv = sortKey === 'name' ? b.player.name : b[sortKey];
    return typeof av === 'string' ? av.localeCompare(bv) * sortDir : (av - bv) * sortDir;
  });

  function handleSort(key) {
    if (sortKey === key) setSortDir(d => -d);
    else { setSortKey(key); setSortDir(-1); }
  }

  return (
    <div className={styles.page}>
      <h1>Statistics</h1>

      <div className={styles.overallGrid}>
        {[
          ['Total Games', totals.total],
          ['Liberal Wins', totals.liberal],
          ['Fascist Wins', totals.fascist],
          ['By Policies', totals.policies],
          ['Hitler Elected', totals.elected],
          ['Hitler Executed', totals.executed],
        ].map(([label, val]) => (
          <div key={label} className={styles.statBox}>
            <span className={styles.statVal}>{val}</span>
            <span className={styles.statLabel}>{label}</span>
          </div>
        ))}
      </div>

      <div className={styles.tableWrap}>
        <table className={styles.table}>
          <thead>
            <tr>
              {COLS.map(c => (
                <th key={c.key} onClick={() => handleSort(c.key)} className={sortKey === c.key ? styles.sorted : ''}>
                  {c.label} {sortKey === c.key ? (sortDir === -1 ? '▼' : '▲') : ''}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map(r => (
              <tr key={r.player.id}>
                <td>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <PlayerHover player={r.player} games={games}>
                      <Avatar path={r.player.avatar_path} name={r.player.name} size={100} />
                      {r.player.name}
                    </PlayerHover>
                  </div>
                </td>
                <td>{r.games}</td>
                <td>{r.wins}</td>
                <td>{r.winPct}%</td>
                <td>{Math.round(r.elo)}%</td>
                <td>{r.deaths}</td>
                <td>{r.libGames}</td><td>{r.libWins}</td>
                <td>{r.fasGames}</td><td>{r.fasWins}</td>
                <td>{r.hitGames}</td><td>{r.hitWins}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
