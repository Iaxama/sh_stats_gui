import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { getSeasons } from '../api';
import { currentSeasonOf } from '../hooks/useScope';
import styles from './SeasonCountdown.module.css';

export function splitRemaining(ms) {
  const total = Math.max(0, Math.floor(ms / 1000));
  return {
    days: Math.floor(total / 86400),
    hours: Math.floor(total % 86400 / 3600),
    minutes: Math.floor(total % 3600 / 60),
    seconds: total % 60,
  };
}

export default function SeasonCountdown() {
  const [season, setSeason] = useState(null);
  const [now, setNow] = useState(() => Date.now());

  useEffect(() => {
    getSeasons().then(seasons => setSeason(currentSeasonOf(seasons))).catch(() => {});
    const timer = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(timer);
  }, []);

  if (!season) return null;

  const remaining = Date.parse(season.scheduled_end) - now;
  if (!(remaining > 0)) {
    return (
      <div className={styles.box}>
        <span className={styles.label}>{season.name} has ended</span>
        <Link to="/players" className={styles.link}>Start a new season</Link>
      </div>
    );
  }

  const parts = splitRemaining(remaining);
  return (
    <div className={styles.box}>
      <span className={styles.label}>{season.name} ends in</span>
      <div className={styles.clock}>
        {Object.entries(parts).map(([unit, value]) => (
          <div key={unit} className={styles.unit}>
            <strong>{String(value).padStart(2, '0')}</strong>
            <span>{unit}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
