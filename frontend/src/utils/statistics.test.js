import assert from 'node:assert/strict';
import { existsSync, readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import test from 'node:test';

import {
  buildCumulativeWins,
  buildEloHistory,
  buildGameSizeStats,
  buildPlotData,
  buildRoleStats,
  calculateEloRatings,
  calculateExpectedScore,
  INITIAL_ELO,
  sortGamesChronologically,
} from './statistics.js';

const players = [
  { id: 'a', name: 'Ada' },
  { id: 'b', name: 'Bruno' },
  { id: 'c', name: 'Carla' },
];

function game(id, date, winningTeam, results) {
  return {
    id,
    date,
    winning_team: winningTeam,
    winning_condition: 'policies_enacted',
    sniper_id: null,
    players: results,
  };
}

const games = [
  game('later', '2026-01-02T12:00:00Z', 'fascist', [
    { player_id: 'a', role: 'fascist', died: false },
    { player_id: 'b', role: 'liberal', died: false },
  ]),
  game('b-tie', '2026-01-01T12:00:00Z', 'liberal', [
    { player_id: 'a', role: 'liberal', died: false },
    { player_id: 'b', role: 'hitler', died: true },
    { player_id: 'unknown', role: 'fascist', died: false },
  ]),
  game('a-tie', '2026-01-01T12:00:00Z', 'fascist', [
    { player_id: 'c', role: 'hitler', died: false },
    { player_id: 'b', role: 'liberal', died: false },
  ]),
];

test('sortGamesChronologically sorts by time and breaks timestamp ties by id', () => {
  assert.deepEqual(sortGamesChronologically(games).map(item => item.id), ['a-tie', 'b-tie', 'later']);
});

test('buildCumulativeWins retains every game and accumulates both teams', () => {
  const points = buildCumulativeWins(games);
  assert.deepEqual(points.map(({ liberal, fascist }) => [liberal, fascist]), [[0, 1], [1, 1], [1, 2]]);
});

test('ELO history starts at 1500, uses team strength, and conserves rating points', () => {
  const history = buildEloHistory(games, players);
  assert.equal(history[0].a, undefined);
  assert.equal(history[0].c, 1516);
  assert.equal(history[0].b, 1484);

  const finalPoint = history.at(-1);
  const ratings = calculateEloRatings(games, players);
  for (const player of players) {
    assert.equal(finalPoint[player.id], ratings[player.id]);
  }
  assert.ok(Math.abs(Object.values(ratings).reduce((sum, rating) => sum + rating, 0) - INITIAL_ELO * players.length) < 1e-9);
});

test('an upset produces a larger expected-score correction than a favourite win', () => {
  const favouriteExpected = calculateExpectedScore(1700, 1300);
  const underdogExpected = calculateExpectedScore(1300, 1700);
  assert.ok(1 - underdogExpected > 1 - favouriteExpected);
  assert.ok(Math.abs(favouriteExpected + underdogExpected - 1) < 1e-12);
});

test('role statistics keep Hitler separate and ignore unknown players', () => {
  const rows = buildRoleStats(games, players);
  const ada = rows.find(row => row.playerId === 'a');
  const bruno = rows.find(row => row.playerId === 'b');
  const carla = rows.find(row => row.playerId === 'c');

  assert.deepEqual(ada.liberal, { games: 1, wins: 1 });
  assert.deepEqual(ada.fascist, { games: 1, wins: 1 });
  assert.deepEqual(bruno.hitler, { games: 1, wins: 0 });
  assert.deepEqual(carla.hitler, { games: 1, wins: 1 });
});

test('game-size buckets expose raw counts and ratios that sum to one', () => {
  const buckets = buildGameSizeStats(games);
  assert.deepEqual(buckets.map(bucket => bucket.playerCount), [2, 3]);
  for (const bucket of buckets) {
    assert.equal(bucket.liberalRatio + bucket.fascistRatio, 1);
    assert.equal(bucket.liberalGames + bucket.fascistGames, bucket.totalGames);
  }
});

test('empty inputs return empty plot datasets', () => {
  assert.deepEqual(buildPlotData([], []), {
    cumulativeWins: [],
    eloHistory: [],
    roleStats: [],
    gameSizeStats: [],
  });
});

const repoRoot = fileURLToPath(new URL('../../../', import.meta.url));
const playersPath = `${repoRoot}data/players.json`;
const gamesPath = `${repoRoot}data/games.json`;

test('local offline dataset has the expected supplied-data totals', { skip: !existsSync(playersPath) || !existsSync(gamesPath) }, () => {
  const localPlayers = JSON.parse(readFileSync(playersPath, 'utf8'));
  const localGames = JSON.parse(readFileSync(gamesPath, 'utf8'));
  const plots = buildPlotData(localGames, localPlayers);

  assert.equal(localPlayers.length, 18);
  assert.equal(localGames.length, 37);
  assert.equal(plots.cumulativeWins.at(-1).liberal, 17);
  assert.equal(plots.cumulativeWins.at(-1).fascist, 20);
  assert.deepEqual(
    plots.gameSizeStats.map(({ playerCount, totalGames }) => [playerCount, totalGames]),
    [[6, 1], [7, 10], [8, 10], [9, 11], [10, 5]],
  );

  const ratings = calculateEloRatings(localGames, localPlayers);
  const finalPoint = plots.eloHistory.at(-1);
  for (const player of localPlayers) {
    assert.equal(finalPoint[player.id], ratings[player.id]);
  }
  assert.ok(Math.abs(Object.values(ratings).reduce((sum, rating) => sum + rating, 0) - INITIAL_ELO * localPlayers.length) < 1e-9);
});
