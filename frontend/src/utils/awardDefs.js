// Replace the `title` values below with the final funny names. Keys match backend/awards.py.
export const AWARD_DEFS = [
  { key: 'highest_elo', title: 'MVP', description: 'Highest ELO of the season.', unit: 'elo' },
  { key: 'lowest_elo', title: 'Best Worst Player', description: 'Lowest ELO of the season.', unit: 'elo' },
  { key: 'most_games', title: 'Workaholic', description: 'Most games played.' },
  { key: 'least_games', title: 'Title TBD', description: 'Fewest games played (among players who played).' },
  { key: 'most_wins', title: 'Title TBD', description: 'Most games won.' },
  { key: 'highest_win_pct', title: 'Title TBD', description: 'Highest win percentage (minimum 5 games).', unit: 'pct' },
  { key: 'lowest_win_pct', title: 'Title TBD', description: 'Lowest win percentage (minimum 5 games).', unit: 'pct' },
  { key: 'most_deaths', title: 'Scariest Player', description: 'Most deaths.' },
  { key: 'most_snipes', title: 'Lee Harvey Oswald', description: 'Most times killing Hitler.' },
  { key: 'most_liberal_games', title: 'Title TBD', description: 'Most games played as Liberal.' },
  { key: 'most_liberal_wins', title: 'Title TBD', description: 'Most wins as Liberal.' },
  { key: 'most_fascist_games', title: 'Title TBD', description: 'Most games played as Fascist.' },
  { key: 'most_fascist_wins', title: 'Title TBD', description: 'Most wins as Fascist.' },
  { key: 'most_hitler_games', title: 'Title TBD', description: 'Most games played as Hitler.' },
  { key: 'most_hitler_wins', title: 'Title TBD', description: 'Most wins as Hitler.' },
  { key: 'most_dumbo', title: 'Dumbo', description: 'Liberal who most often elected Hitler as Chancellor, handing the Fascists the win.' },
  { key: 'most_dictator', title: 'Dictator', description: 'Fascist who most often elected Hitler as Chancellor for the win.' },
];

export function formatAwardValue(award, def) {
  if (def.unit === 'elo') return String(Math.round(award.value));
  if (def.unit === 'pct') return `${Math.round(award.value)}%`;
  return String(award.value);
}
