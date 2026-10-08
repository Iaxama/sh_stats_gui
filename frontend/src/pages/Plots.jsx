/* eslint-disable react/prop-types */
import { useEffect, useMemo, useState } from 'react';
import {
  Bar,
  BarChart,
  CartesianGrid,
  LabelList,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

import { getGames, getPlayers } from '../api';
import { buildPlotData } from '../utils/statistics';
import styles from './Plots.module.css';

const COLORS = {
  liberal: '#3b82f6',
  liberalLight: '#93c5fd',
  fascist: '#991b1b',
  fascistLight: '#ef4444',
  hitler: '#7c2d12',
  hitlerLight: '#fb923c',
  grid: '#3a3428',
  text: '#9a9080',
};

const PLAYER_COLORS = [
  '#60a5fa', '#f87171', '#34d399', '#fbbf24', '#a78bfa', '#fb7185',
  '#22d3ee', '#bef264', '#c084fc', '#f97316', '#2dd4bf', '#e879f9',
  '#93c5fd', '#fca5a5', '#86efac', '#fde047', '#818cf8', '#fdba74',
];

const ROLE_META = {
  liberal: { label: 'Liberal', light: COLORS.liberalLight, dark: COLORS.liberal },
  fascist: { label: 'Fascist', light: COLORS.fascistLight, dark: COLORS.fascist },
  hitler: { label: 'Hitler', light: COLORS.hitlerLight, dark: COLORS.hitler },
};

const shortDate = new Intl.DateTimeFormat(undefined, { month: 'short', day: 'numeric' });
const exactDate = new Intl.DateTimeFormat(undefined, {
  dateStyle: 'medium',
  timeStyle: 'short',
});

function formatShortDate(timestamp) {
  return Number.isFinite(timestamp) ? shortDate.format(new Date(timestamp)) : 'Unknown';
}

function formatExactDate(date) {
  const parsed = new Date(date);
  return Number.isNaN(parsed.getTime()) ? 'Unknown date' : exactDate.format(parsed);
}

function renderLegendLabel(value) {
  return <span className={styles.legendText}>{value}</span>;
}

function ChartTooltip({ active, payload, mode = 'number' }) {
  if (!active || !payload?.length) return null;
  const point = payload[0].payload;

  return (
    <div className={styles.tooltip}>
      <strong>{formatExactDate(point.date)}</strong>
      <span>Game {point.gameNumber}</span>
      {payload.map(entry => (
        <span key={entry.dataKey} style={{ color: entry.color }}>
          {entry.name}: {mode === 'elo' ? entry.value.toFixed(1) : entry.value}
        </span>
      ))}
    </div>
  );
}

function NestedWinBar({ x, y, width, height, payload, role }) {
  const roleData = payload?.[role] ?? { games: 0, wins: 0 };
  const meta = ROLE_META[role];
  const winHeight = roleData.games ? height * roleData.wins / roleData.games : 0;
  const inset = Math.min(3, width * 0.12);

  return (
    <g>
      <rect x={x} y={y} width={width} height={height} rx={3} fill={meta.light} />
      {winHeight > 0 && (
        <rect
          x={x + inset}
          y={y + height - winHeight}
          width={Math.max(0, width - inset * 2)}
          height={winHeight}
          rx={2}
          fill={meta.dark}
        />
      )}
    </g>
  );
}

function RoleTooltip({ active, payload }) {
  if (!active || !payload?.length) return null;
  const row = payload[0].payload;

  return (
    <div className={styles.tooltip}>
      <strong>{row.playerName}</strong>
      {Object.entries(ROLE_META).map(([role, meta]) => {
        const { games, wins } = row[role];
        const percentage = games ? Math.round(wins / games * 100) : 0;
        return (
          <span key={role} style={{ color: meta.light }}>
            {meta.label}: {wins}/{games} wins ({percentage}%)
          </span>
        );
      })}
    </div>
  );
}

function GameSizeTooltip({ active, payload }) {
  if (!active || !payload?.length) return null;
  const row = payload[0].payload;

  return (
    <div className={styles.tooltip}>
      <strong>{row.playerCount} players</strong>
      <span style={{ color: COLORS.liberalLight }}>
        Liberal: {row.liberalGames} games ({Math.round(row.liberalRatio * 100)}%)
      </span>
      <span style={{ color: COLORS.fascistLight }}>
        Fascist: {row.fascistGames} games ({Math.round(row.fascistRatio * 100)}%)
      </span>
      <span>Total: {row.totalGames} games</span>
    </div>
  );
}

function ChartCard({ title, description, children, minWidth = 0 }) {
  return (
    <section className={styles.card}>
      <div className={styles.cardHeading}>
        <h2>{title}</h2>
        <p>{description}</p>
      </div>
      <div className={styles.chartScroll}>
        <div className={styles.chart} style={{ minWidth }}>
          {children}
        </div>
      </div>
    </section>
  );
}

export default function Plots() {
  const [games, setGames] = useState([]);
  const [players, setPlayers] = useState([]);
  const [hiddenPlayers, setHiddenPlayers] = useState(() => new Set());
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let cancelled = false;

    Promise.all([getGames(), getPlayers()])
      .then(([loadedGames, loadedPlayers]) => {
        if (cancelled) return;
        setGames(loadedGames);
        setPlayers(loadedPlayers);
      })
      .catch(loadError => {
        if (!cancelled) setError(loadError.message || 'Could not load plot data.');
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => { cancelled = true; };
  }, []);

  const plotData = useMemo(() => buildPlotData(games, players), [games, players]);
  const sortedPlayers = useMemo(
    () => [...players].sort((a, b) => a.name.localeCompare(b.name)),
    [players],
  );
  const playerColors = useMemo(
    () => Object.fromEntries(sortedPlayers.map((player, index) => [
      player.id,
      PLAYER_COLORS[index % PLAYER_COLORS.length],
    ])),
    [sortedPlayers],
  );

  function togglePlayer(playerId) {
    setHiddenPlayers(current => {
      const next = new Set(current);
      if (next.has(playerId)) next.delete(playerId);
      else next.add(playerId);
      return next;
    });
  }

  if (loading) {
    return <main className={styles.state}><p>Loading plots…</p></main>;
  }

  if (error) {
    return <main className={`${styles.state} ${styles.error}`}><p>{error}</p></main>;
  }

  if (!games.length) {
    return (
      <main className={styles.state}>
        <h1>Plots</h1>
        <p>No games have been recorded yet.</p>
      </main>
    );
  }

  const roleChartWidth = Math.max(900, plotData.roleStats.length * 96);

  return (
    <main className={styles.page}>
      <header className={styles.pageHeading}>
        <h1>Plots</h1>
        <p>{games.length} games across {players.length} players</p>
      </header>

      <ChartCard
        title="Fascist vs Liberal Wins Over Time"
        description="Cumulative wins after each recorded game."
      >
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={plotData.cumulativeWins} margin={{ top: 12, right: 24, bottom: 12, left: 0 }}>
            <CartesianGrid stroke={COLORS.grid} strokeDasharray="3 3" />
            <XAxis
              dataKey="time"
              type="number"
              domain={['dataMin', 'dataMax']}
              tickFormatter={formatShortDate}
              stroke={COLORS.text}
            />
            <YAxis allowDecimals={false} stroke={COLORS.text} width={42} />
            <Tooltip content={<ChartTooltip />} />
            <Legend formatter={renderLegendLabel} />
            <Line type="stepAfter" dataKey="liberal" name="Liberal" stroke={COLORS.liberal} strokeWidth={3} dot={false} isAnimationActive={false} />
            <Line type="stepAfter" dataKey="fascist" name="Fascist" stroke={COLORS.fascistLight} strokeWidth={3} dot={false} isAnimationActive={false} />
          </LineChart>
        </ResponsiveContainer>
      </ChartCard>

      <ChartCard
        title="Individual Player ELO Over Time"
        description="Team-based ELO starting at 1500; surprising wins move ratings more."
        minWidth={900}
      >
        <div className={styles.playerControls}>
          <button type="button" onClick={() => setHiddenPlayers(new Set())}>Show all</button>
          <button type="button" onClick={() => setHiddenPlayers(new Set(players.map(player => player.id)))}>Hide all</button>
          <div className={styles.playerLegend}>
            {sortedPlayers.map(player => {
              const visible = !hiddenPlayers.has(player.id);
              return (
                <button
                  type="button"
                  key={player.id}
                  className={visible ? styles.playerActive : styles.playerHidden}
                  style={{ '--player-color': playerColors[player.id] }}
                  aria-pressed={visible}
                  onClick={() => togglePlayer(player.id)}
                >
                  {player.name}
                </button>
              );
            })}
          </div>
        </div>
        <div className={styles.eloChart}>
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={plotData.eloHistory} margin={{ top: 12, right: 24, bottom: 12, left: 0 }}>
              <CartesianGrid stroke={COLORS.grid} strokeDasharray="3 3" />
              <XAxis
                dataKey="time"
                type="number"
                domain={['dataMin', 'dataMax']}
                tickFormatter={formatShortDate}
                stroke={COLORS.text}
              />
              <YAxis
                domain={[
                  value => Math.floor((value - 10) / 25) * 25,
                  value => Math.ceil((value + 10) / 25) * 25,
                ]}
                allowDecimals={false}
                stroke={COLORS.text}
                width={48}
              />
              <Tooltip content={<ChartTooltip mode="elo" />} />
              {sortedPlayers.map(player => !hiddenPlayers.has(player.id) && (
                <Line
                  key={player.id}
                  type="linear"
                  dataKey={player.id}
                  name={player.name}
                  stroke={playerColors[player.id]}
                  strokeWidth={2}
                  dot={false}
                  connectNulls
                  isAnimationActive={false}
                />
              ))}
            </LineChart>
          </ResponsiveContainer>
        </div>
      </ChartCard>

      <ChartCard
        title="Games and Wins by Player and Role"
        description="The full light bar is games played; the darker inset is the share won."
        minWidth={roleChartWidth}
      >
        <div className={styles.roleLegend}>
          {Object.entries(ROLE_META).map(([role, meta]) => (
            <span key={role} style={{ '--role-light': meta.light, '--role-dark': meta.dark }}>
              <i /> {meta.label}
            </span>
          ))}
          <small>light = games · dark inset = wins</small>
        </div>
        <div className={styles.roleChart}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={plotData.roleStats} margin={{ top: 12, right: 24, bottom: 48, left: 0 }} barGap={2}>
              <CartesianGrid stroke={COLORS.grid} strokeDasharray="3 3" vertical={false} />
              <XAxis
                dataKey="playerName"
                angle={-35}
                textAnchor="end"
                interval={0}
                height={72}
                stroke={COLORS.text}
              />
              <YAxis allowDecimals={false} stroke={COLORS.text} width={42} />
              <Tooltip content={<RoleTooltip />} cursor={{ fill: 'rgba(255, 255, 255, 0.04)' }} />
              {Object.entries(ROLE_META).map(([role, meta]) => (
                <Bar
                  key={role}
                  dataKey={`${role}.games`}
                  name={meta.label}
                  fill={meta.light}
                  maxBarSize={28}
                  shape={props => <NestedWinBar {...props} role={role} />}
                  isAnimationActive={false}
                />
              ))}
            </BarChart>
          </ResponsiveContainer>
        </div>
      </ChartCard>

      <ChartCard
        title="Winner by Number of Players"
        description="Each bar totals 100%; labels show the number of games won by each team."
      >
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={plotData.gameSizeStats} margin={{ top: 12, right: 24, bottom: 12, left: 0 }}>
            <CartesianGrid stroke={COLORS.grid} strokeDasharray="3 3" vertical={false} />
            <XAxis dataKey="playerCount" stroke={COLORS.text} label={{ value: 'Players per game', position: 'insideBottom', offset: -6, fill: COLORS.text }} />
            <YAxis domain={[0, 1]} ticks={[0, 0.25, 0.5, 0.75, 1]} tickFormatter={value => `${value * 100}%`} stroke={COLORS.text} width={48} />
            <Tooltip content={<GameSizeTooltip />} cursor={{ fill: 'rgba(255, 255, 255, 0.04)' }} />
            <Legend formatter={renderLegendLabel} />
            <Bar dataKey="liberalRatio" name="Liberal" stackId="winner" fill={COLORS.liberal} isAnimationActive={false}>
              <LabelList dataKey="liberalGames" position="center" fill="#fff" fontWeight="bold" />
            </Bar>
            <Bar dataKey="fascistRatio" name="Fascist" stackId="winner" fill={COLORS.fascist} radius={[4, 4, 0, 0]} isAnimationActive={false}>
              <LabelList dataKey="fascistGames" position="center" fill="#fff" fontWeight="bold" />
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </ChartCard>
    </main>
  );
}
