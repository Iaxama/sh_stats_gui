import { useEffect, useState } from 'react';
import { getPlayers, getSeasons } from '../api';
import Avatar from '../components/Avatar';
import { AWARD_DEFS, formatAwardValue } from '../utils/awardDefs';
import styles from './HallOfFame.module.css';

function AwardCard({ def, award, player }) {
  const valueLabel = formatAwardValue(award, def);
  return (
    <div className={styles.award} tabIndex={0}>
      <div className={styles.frame}>
        <Avatar path={player.avatar_path} name={player.name} size={110} />
      </div>
      <strong className={styles.title}>{def.title}</strong>
      <span className={styles.player}>{player.name}</span>
      <div className={styles.tip} role="tooltip">
        <strong>{def.title}</strong>
        <span>{def.description}</span>
        <em>{player.name}: {valueLabel}</em>
      </div>
    </div>
  );
}

export default function HallOfFame() {
  const [seasons, setSeasons] = useState([]);
  const [playerMap, setPlayerMap] = useState({});

  useEffect(() => {
    Promise.all([getSeasons(), getPlayers()]).then(([loadedSeasons, players]) => {
      setSeasons(loadedSeasons);
      setPlayerMap(Object.fromEntries(players.map(p => [p.id, p])));
    });
  }, []);

  const ordered = [...seasons].sort((a, b) => b.number - a.number);

  return (
    <div className={styles.page}>
      <h1>Hall of Fame</h1>
      {ordered.map(season => {
        const awardsByKey = Object.fromEntries((season.awards ?? []).map(a => [a.key, a]));
        const cards = AWARD_DEFS.flatMap(def => {
          const award = awardsByKey[def.key];
          if (!award) return [];
          return award.winners
            .filter(id => playerMap[id])
            .map(id => <AwardCard key={`${def.key}-${id}`} def={def} award={award} player={playerMap[id]} />);
        });
        return (
          <section key={season.id} className={styles.season}>
            <h2>{season.name}</h2>
            {season.end_date == null
              ? <p className={styles.note}>In progress – awards are handed out when the season ends.</p>
              : cards.length === 0 && <p className={styles.note}>No awards for this season.</p>}
            <div className={styles.grid}>{cards}</div>
          </section>
        );
      })}
    </div>
  );
}
