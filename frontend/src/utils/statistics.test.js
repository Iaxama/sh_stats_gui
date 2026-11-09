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
  calculateGamePercentage,
  computeStats,
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

test('calculateGamePercentage uses total games and safely handles zero games', () => {
  assert.equal(calculateGamePercentage(2, 3), 67);
  assert.equal(calculateGamePercentage(0, 0), 0);
});

test('buildCumulativeWins retains every game and accumulates both teams', () => {
  const points = buildCumulativeWins(games);
  assert.deepEqual(points.map(({ liberal, fascist }) => [liberal, fascist]), [[0, 1], [1, 1], [1, 2]]);
});

test('Election Pool uses cumulative results after five games in chronological order', () => {
  const moreGames = [
    game('fifth', '2026-01-05T12:00:00Z', 'liberal', []),
    game('fourth', '2026-01-04T12:00:00Z', 'fascist', []),
    game('sixth', '2026-01-06T12:00:00Z', 'liberal', []),
    ...games,
  ];
  const points = buildPlotData(moreGames, players).electionPoll;

  assert.deepEqual(points.map(point => point.gameId), ['fifth', 'sixth']);
  assert.deepEqual(points.map(point => point.gameNumber), [5, 6]);
  assert.deepEqual(points.map(point => [point.liberal, point.fascist]), [
    [40, 60],
    [50, 50],
  ]);
  for (const point of points) {
    assert.ok(Math.abs(point.liberal + point.fascist - 100) < 1e-10);
  }
  assert.equal(points[0].date, '2026-01-05T12:00:00Z');
  assert.equal(points[0].time, Date.parse(points[0].date));
});

test('Election Pool waits for five games and excludes unrecognized winners from cumulative results', () => {
  const fourGames = [...games, game('fourth', '2026-01-04', 'liberal', [])];
  assert.deepEqual(buildPlotData(fourGames, players).electionPoll, []);
  const invalid = game('invalid', '2026-01-03T12:00:00Z', 'unknown', []);
  const laterGames = [
    game('1', '2026-01-04', 'fascist', []),
    game('2', '2026-01-05', 'fascist', []),
    game('3', '2026-01-06', 'fascist', []),
  ];
  const points = buildPlotData([...games, invalid, ...laterGames], players).electionPoll;
  assert.equal(points.length, 3);
  assert.deepEqual(points.map(point => point.gameNumber), [5, 6, 7]);
  assert.deepEqual([points[0].liberal, points[0].fascist], [25, 75]);
  assert.deepEqual([points[1].liberal, points[1].fascist], [20, 80]);
  assert.deepEqual([points[2].liberal, points[2].fascist], [100 / 6, 500 / 6]);
  assert.ok(points.every(point => point.hasInvalidResults));
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

  assert.equal(ada.totalGames, 2);
  assert.deepEqual(ada.liberal, { games: 1, wins: 1 });
  assert.deepEqual(ada.fascist, { games: 1, wins: 1 });
  assert.deepEqual(bruno.hitler, { games: 1, wins: 0 });
  assert.deepEqual(carla.hitler, { games: 1, wins: 1 });
});

test('role statistics put players with the most games first and break ties by name', () => {
  const rows = buildRoleStats(games, players);

  assert.deepEqual(
    rows.map(row => [row.playerName, row.totalGames]),
    [['Bruno', 3], ['Ada', 2], ['Carla', 1]],
  );
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
    electionPoll: [],
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

test('counts Dumbo and Dictator from the Hitler chooser role', () => {
  const players = ['a', 'b', 'c', 'd', 'e'].map(id => ({ id, name: id }));
  const roles = ['liberal', 'liberal', 'liberal', 'fascist', 'hitler'];
  const make = chooser => ({
    id: chooser, date: '2026-01-01', winning_team: 'fascist', winning_condition: 'hitler_elected',
    hitler_chooser_id: chooser,
    players: players.map((p, i) => ({ player_id: p.id, role: roles[i], died: false })),
  });
  const { perPlayer } = computeStats([make('a'), make('d')], players);
  const byId = Object.fromEntries(perPlayer.map(row => [row.player.id, row]));
  assert.equal(byId.a.dumbo, 1);
  assert.equal(byId.d.dictator, 1);
  assert.equal(byId.a.dictator, 0);
});
