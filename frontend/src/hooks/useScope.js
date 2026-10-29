import { useCallback, useEffect, useMemo, useState } from 'react';
import { getSeasons } from '../api';

const SCOPE_KEY = 'sh-stats-scope';
const RETIRED_KEY = 'sh-stats-show-retired';

export function currentSeasonOf(seasons) {
  return seasons.find(season => season.end_date == null) ?? seasons[seasons.length - 1] ?? null;
}

export function applyScope(scope, games, players, currentSeason, showRetired = false) {
  if (scope === 'all') return { games, players };
  return {
    games: currentSeason ? games.filter(game => game.season_id === currentSeason.id) : games,
    players: showRetired ? players : players.filter(player => !player.retired),
  };
}

export default function useScope() {
  const [seasons, setSeasons] = useState([]);
  const [scope, setScopeState] = useState(() => localStorage.getItem(SCOPE_KEY) || 'season');
  const [showRetired, setShowRetiredState] = useState(() => localStorage.getItem(RETIRED_KEY) === '1');

  useEffect(() => {
    getSeasons().then(setSeasons).catch(() => setSeasons([]));
  }, []);

  const setScope = useCallback(value => {
    localStorage.setItem(SCOPE_KEY, value);
    setScopeState(value);
  }, []);
  const setShowRetired = useCallback(value => {
    localStorage.setItem(RETIRED_KEY, value ? '1' : '0');
    setShowRetiredState(value);
  }, []);

  const currentSeason = useMemo(() => currentSeasonOf(seasons), [seasons]);

  return { seasons, currentSeason, scope, setScope, showRetired, setShowRetired };
}
