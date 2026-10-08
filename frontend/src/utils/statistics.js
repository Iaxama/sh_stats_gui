export const INITIAL_ELO = 1500;
export const ELO_SCALE = 400;

// This is a team-level K factor. It is split between the two teams according
// to their sizes, so the total rating gained always equals the total lost.
export const ELO_K_FACTOR = 64;

const ROLES = ['liberal', 'fascist', 'hitler'];

export function didPlayerWin(role, winningTeam) {
  return (role === 'liberal' && winningTeam === 'liberal') ||
    ((role === 'fascist' || role === 'hitler') && winningTeam === 'fascist');
}

export function calculateExpectedScore(rating, opponentRating) {
  return 1 / (1 + 10 ** ((opponentRating - rating) / ELO_SCALE));
}

export function sortGamesChronologically(games) {
  return games
    .map((game, index) => ({ game, index, time: Date.parse(game.date) }))
    .sort((a, b) => {
      const aTime = Number.isFinite(a.time) ? a.time : Number.POSITIVE_INFINITY;
      const bTime = Number.isFinite(b.time) ? b.time : Number.POSITIVE_INFINITY;
      if (aTime !== bTime) return aTime - bTime;

      const idOrder = String(a.game.id ?? '').localeCompare(String(b.game.id ?? ''));
      return idOrder || a.index - b.index;
    })
    .map(({ game }) => game);
}

export function computeStats(games, players) {
  const totals = {
    total: games.length,
    liberal: 0,
    fascist: 0,
    policies: 0,
    elected: 0,
    executed: 0,
  };
  const perPlayer = {};

  for (const player of players) {
    perPlayer[player.id] = {
      player,
      games: 0,
      wins: 0,
      deaths: 0,
      snipers: 0,
      byRole: Object.fromEntries(ROLES.map(role => [role, { g: 0, w: 0 }])),
    };
  }

  for (const game of games) {
    if (game.winning_team === 'liberal') totals.liberal++;
    else if (game.winning_team === 'fascist') totals.fascist++;

    if (game.winning_condition === 'policies_enacted') totals.policies++;
    else if (game.winning_condition === 'hitler_elected') totals.elected++;
    else if (game.winning_condition === 'hitler_executed') totals.executed++;

    if (game.sniper_id && perPlayer[game.sniper_id]) {
      perPlayer[game.sniper_id].snipers++;
    }

    for (const result of game.players ?? []) {
      const row = perPlayer[result.player_id];
      if (!row || !row.byRole[result.role]) continue;

      const won = didPlayerWin(result.role, game.winning_team);
      row.games++;
      if (won) row.wins++;
      if (result.died) row.deaths++;
      row.byRole[result.role].g++;
      if (won) row.byRole[result.role].w++;
    }
  }

  return { totals, perPlayer: Object.values(perPlayer) };
}

export function buildCumulativeWins(games) {
  let liberal = 0;
  let fascist = 0;

  return sortGamesChronologically(games).map((game, gameIndex) => {
    if (game.winning_team === 'liberal') liberal++;
    else if (game.winning_team === 'fascist') fascist++;

    return {
      gameId: game.id,
      gameNumber: gameIndex + 1,
      date: game.date,
      time: Date.parse(game.date),
      liberal,
      fascist,
    };
  });
}

function calculateEloProgression(games, players) {
  const knownPlayerIds = new Set(players.map(player => player.id));
  const ratings = new Map(players.map(player => [player.id, INITIAL_ELO]));
  const appearances = new Map(players.map(player => [player.id, 0]));

  const history = sortGamesChronologically(games).map((game, gameIndex) => {
    const liberalTeam = [];
    const fascistTeam = [];
    const includedPlayers = new Set();

    for (const result of game.players ?? []) {
      if (!knownPlayerIds.has(result.player_id) || includedPlayers.has(result.player_id)) continue;

      if (result.role === 'liberal') liberalTeam.push(result.player_id);
      else if (result.role === 'fascist' || result.role === 'hitler') fascistTeam.push(result.player_id);
      else continue;

      includedPlayers.add(result.player_id);
      appearances.set(result.player_id, appearances.get(result.player_id) + 1);
    }

    const hasValidTeams = liberalTeam.length > 0 && fascistTeam.length > 0;
    const hasValidWinner = game.winning_team === 'liberal' || game.winning_team === 'fascist';

    if (hasValidTeams && hasValidWinner) {
      const liberalRating = liberalTeam.reduce((sum, id) => sum + ratings.get(id), 0) / liberalTeam.length;
      const fascistRating = fascistTeam.reduce((sum, id) => sum + ratings.get(id), 0) / fascistTeam.length;
      const expectedLiberal = calculateExpectedScore(liberalRating, fascistRating);
      const liberalScore = game.winning_team === 'liberal' ? 1 : 0;
      const surprise = liberalScore - expectedLiberal;
      const participantCount = liberalTeam.length + fascistTeam.length;

      // Players on the smaller team receive a larger individual adjustment,
      // while the rating transfer remains zero-sum across the whole game.
      const liberalDelta = ELO_K_FACTOR * surprise * fascistTeam.length / participantCount;
      const fascistDelta = -ELO_K_FACTOR * surprise * liberalTeam.length / participantCount;

      for (const playerId of liberalTeam) {
        ratings.set(playerId, ratings.get(playerId) + liberalDelta);
      }
      for (const playerId of fascistTeam) {
        ratings.set(playerId, ratings.get(playerId) + fascistDelta);
      }
    }

    const point = {
      gameId: game.id,
      gameNumber: gameIndex + 1,
      date: game.date,
      time: Date.parse(game.date),
    };

    for (const player of players) {
      if (appearances.get(player.id) > 0) point[player.id] = ratings.get(player.id);
    }

    return point;
  });

  return { history, ratings };
}

export function buildEloHistory(games, players) {
  return calculateEloProgression(games, players).history;
}

export function calculateEloRatings(games, players) {
  return Object.fromEntries(calculateEloProgression(games, players).ratings);
}

export function buildRoleStats(games, players) {
  const { perPlayer } = computeStats(games, players);

  return perPlayer
    .map(row => ({
      playerId: row.player.id,
      playerName: row.player.name,
      liberal: { games: row.byRole.liberal.g, wins: row.byRole.liberal.w },
      fascist: { games: row.byRole.fascist.g, wins: row.byRole.fascist.w },
      hitler: { games: row.byRole.hitler.g, wins: row.byRole.hitler.w },
    }))
    .sort((a, b) => a.playerName.localeCompare(b.playerName));
}

export function buildGameSizeStats(games) {
  const buckets = new Map();

  for (const game of games) {
    const playerCount = game.players?.length ?? 0;
    if (!playerCount) continue;

    const bucket = buckets.get(playerCount) ?? {
      playerCount,
      totalGames: 0,
      liberalGames: 0,
      fascistGames: 0,
    };
    bucket.totalGames++;
    if (game.winning_team === 'liberal') bucket.liberalGames++;
    else if (game.winning_team === 'fascist') bucket.fascistGames++;
    buckets.set(playerCount, bucket);
  }

  return [...buckets.values()]
    .sort((a, b) => a.playerCount - b.playerCount)
    .map(bucket => ({
      ...bucket,
      liberalRatio: bucket.totalGames ? bucket.liberalGames / bucket.totalGames : 0,
      fascistRatio: bucket.totalGames ? bucket.fascistGames / bucket.totalGames : 0,
    }));
}

export function buildPlotData(games, players) {
  return {
    cumulativeWins: buildCumulativeWins(games),
    eloHistory: buildEloHistory(games, players),
    roleStats: buildRoleStats(games, players),
    gameSizeStats: buildGameSizeStats(games),
  };
}
