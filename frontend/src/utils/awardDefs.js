// Keys match backend/awards.py.
export const AWARD_DEFS = [
  { key: 'most_games', title: 'Workaholic', description: 'Most games played.' },
  { key: 'most_wins', title: 'Quantity over quality', description: 'Most games won.' },
  { key: 'highest_win_pct', title: 'MVP', description: 'Highest win percentage (minimum 5 games).', unit: 'pct' },
  { key: 'lowest_win_pct', title: 'Best worst player', description: 'Lowest win percentage (minimum 5 games).', unit: 'pct' },
  { key: 'most_deaths', title: 'Scariest Player', description: 'Most deaths.' },
  { key: 'most_snipes', title: 'Lee Harvey Oswald', description: 'Most times killing Hitler.' },
  { key: 'most_liberal_games', title: 'Bernie Sanders', description: 'Most games played as Liberal.' },
  { key: 'most_liberal_wins', title: 'Zohran Mamdani', description: 'Most wins as Liberal.' },
  { key: 'most_fascist_games', title: 'Kim Jong Un', description: 'Most games played as Fascist.' },
  { key: 'most_fascist_wins', title: 'Vladimir Putin', description: 'Most wins as Fascist.' },
  { key: 'most_hitler_games', title: 'The Dictator', description: 'Most games played as Hitler.' },
  { key: 'most_hitler_wins', title: 'Super Hitler', description: 'Most wins as Hitler.' },
  { key: 'most_dumbo', title: 'Dumbo', description: 'Liberal who most often elected Hitler as Chancellor, handing the Fascists the win.' },
  { key: 'most_dictator', title: 'Heinrich Himmler', description: 'Fascist who most often elected Hitler as Chancellor for the win.' },
];

export function formatAwardValue(award, def) {
  if (def.unit === 'elo') return String(Math.round(award.value));
  if (def.unit === 'pct') return `${Math.round(award.value)}%`;
  return String(award.value);
}
