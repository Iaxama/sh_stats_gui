import { useEffect, useMemo, useState } from 'react';
import { getGames, getPlayers } from '../api';
import Avatar from '../components/Avatar';
import PlayerHover from '../components/PlayerHover';
import ScopeToggle from '../components/ScopeToggle';
import useScope, { applyScope } from '../hooks/useScope';
import { calculateEloRatings, calculateGamePercentage, computeStats } from '../utils/statistics';
import styles from './Stats.module.css';

const COLS = [
  { key: 'name', label: 'Player' },
  { key: 'games', label: 'Games' },
  { key: 'wins', label: 'Wins', percentageSort: true },
  { key: 'elo', label: 'ELO' },
  { key: 'deaths', label: 'Deaths', percentageSort: true },
  { key: 'snipers', label: 'Sniper', percentageSort: true },
  { key: 'dumbo', label: 'Dumbo', percentageSort: true },
  { key: 'dictator', label: 'Dictator', percentageSort: true },
  { key: 'libGames', label: 'Lib G', percentageSort: true },
  { key: 'libWins', label: 'Lib W', percentageSort: true },
  { key: 'fasGames', label: 'Fas G', percentageSort: true },
  { key: 'fasWins', label: 'Fas W', percentageSort: true },
  { key: 'hitGames', label: 'Hit G', percentageSort: true },
  { key: 'hitWins', label: 'Hit W', percentageSort: true },
];

function formatPlayerCount(count, gamesPlayed) {
  return `${count} (${calculateGamePercentage(count, gamesPlayed)}%)`;
}

export default function Stats() {
  const [allGames, setGames] = useState([]);
  const [allPlayers, setPlayers] = useState([]);
  const scopeState = useScope();
  const { scope, currentSeason, showRetired } = scopeState;
  const [sortKey, setSortKey] = useState('games');
  const [sortDir, setSortDir] = useState(-1);
  const [minGames, setMinGames] = useState('0');

  useEffect(() => {
    Promise.all([getGames(), getPlayers()]).then(([g, p]) => { setGames(g); setPlayers(p); });
  }, []);

  const { games, players } = useMemo(
    () => applyScope(scope, allGames, allPlayers, currentSeason, showRetired),
    [scope, allGames, allPlayers, currentSeason, showRetired],
  );
  const { totals, perPlayer } = computeStats(games, players);
  const eloRatings = calculateEloRatings(games, players);

  const rows = perPlayer.map(r => ({
    ...r,
    elo: eloRatings[r.player.id],
    libGames: r.byRole.liberal.g, libWins: r.byRole.liberal.w,
    fasGames: r.byRole.fascist.g, fasWins: r.byRole.fascist.w,
    hitGames: r.byRole.hitler.g,  hitWins: r.byRole.hitler.w,
    winsPercentage: calculateGamePercentage(r.wins, r.games),
    deathsPercentage: calculateGamePercentage(r.deaths, r.games),
    snipersPercentage: calculateGamePercentage(r.snipers, r.games),
    dumboPercentage: calculateGamePercentage(r.dumbo, r.games),
    dictatorPercentage: calculateGamePercentage(r.dictator, r.games),
    libGamesPercentage: calculateGamePercentage(r.byRole.liberal.g, r.games),
    libWinsPercentage: calculateGamePercentage(r.byRole.liberal.w, r.games),
    fasGamesPercentage: calculateGamePercentage(r.byRole.fascist.g, r.games),
    fasWinsPercentage: calculateGamePercentage(r.byRole.fascist.w, r.games),
    hitGamesPercentage: calculateGamePercentage(r.byRole.hitler.g, r.games),
    hitWinsPercentage: calculateGamePercentage(r.byRole.hitler.w, r.games),
  })).sort((a, b) => {
    const av = sortKey === 'name' ? a.player.name : a[sortKey];
    const bv = sortKey === 'name' ? b.player.name : b[sortKey];
    return typeof av === 'string' ? av.localeCompare(bv) * sortDir : (av - bv) * sortDir;
  });
  const minimumGames = Math.max(0, Number.parseInt(minGames, 10) || 0);
  const visibleRows = rows.filter(row => row.games >= minimumGames);

  function handleSort(key, metric = 'count') {
    const sortField = metric === 'percentage' ? `${key}Percentage` : key;
    if (sortKey === sortField) setSortDir(d => -d);
    else { setSortKey(sortField); setSortDir(-1); }
  }

  return (
    <div className={styles.page}>
      <h1>Statistics</h1>
      <ScopeToggle {...scopeState} hasRetired={allPlayers.some(p => p.retired)} />

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

      <div className={styles.filterControls}>
        <label htmlFor="minimum-games">Minimum games played</label>
        <input
          id="minimum-games"
          type="number"
          min="0"
          step="1"
          value={minGames}
          onChange={event => setMinGames(event.target.value)}
          aria-describedby="minimum-games-help"
        />
        <span id="minimum-games-help">Players with fewer games are hidden.</span>
      </div>

      <div className={styles.tableWrap}>
        <table className={styles.table}>
          <thead>
            <tr>
              {COLS.map(c => {
                const countActive = sortKey === c.key;
                const percentageKey = `${c.key}Percentage`;
                const percentageActive = sortKey === percentageKey;
                return (
                  <th key={c.key} className={countActive || percentageActive ? styles.sorted : ''}>
                    {c.percentageSort ? (
                      <span className={styles.sortHeader}>
                        {c.label}
                        <span className={styles.sortButtons}>
                          <button
                            type="button"
                            aria-label={`Sort ${c.label} by count`}
                            aria-pressed={countActive}
                            className={countActive ? styles.activeSort : ''}
                            onClick={() => handleSort(c.key)}
                          >
                            #{countActive ? (sortDir === -1 ? ' ▼' : ' ▲') : ''}
                          </button>
                          <button
                            type="button"
                            aria-label={`Sort ${c.label} by percentage`}
                            aria-pressed={percentageActive}
                            className={percentageActive ? styles.activeSort : ''}
                            onClick={() => handleSort(c.key, 'percentage')}
                          >
                            %{percentageActive ? (sortDir === -1 ? ' ▼' : ' ▲') : ''}
                          </button>
                        </span>
                      </span>
                    ) : (
                      <button
                        type="button"
                        aria-label={`Sort by ${c.label}`}
                        className={styles.headerSort}
                        onClick={() => handleSort(c.key)}
                      >
                        {c.label} {countActive ? (sortDir === -1 ? '▼' : '▲') : ''}
                      </button>
                    )}
                  </th>
                );
              })}
            </tr>
          </thead>
          <tbody>
            {visibleRows.map(r => (
              <tr key={r.player.id}>
                <td>
                  <div className={styles.playerCell}>
                    <PlayerHover player={r.player} games={games}>
                      <Avatar path={r.player.avatar_path} name={r.player.name} size={100} />
                      {r.player.name}
                    </PlayerHover>
                  </div>
                </td>
                <td>{r.games}</td>
                <td>{formatPlayerCount(r.wins, r.games)}</td>
                <td>{Math.round(r.elo)}</td>
                <td>{formatPlayerCount(r.deaths, r.games)}</td>
                <td>{formatPlayerCount(r.snipers, r.games)}</td>
                <td>{formatPlayerCount(r.dumbo, r.games)}</td>
                <td>{formatPlayerCount(r.dictator, r.games)}</td>
                <td>{formatPlayerCount(r.libGames, r.games)}</td>
                <td>{formatPlayerCount(r.libWins, r.games)}</td>
                <td>{formatPlayerCount(r.fasGames, r.games)}</td>
                <td>{formatPlayerCount(r.fasWins, r.games)}</td>
                <td>{formatPlayerCount(r.hitGames, r.games)}</td>
                <td>{formatPlayerCount(r.hitWins, r.games)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
