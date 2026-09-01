import { Link } from 'react-router-dom';
import styles from './Home.module.css';

const NAV = [
  { to: '/add-game', label: 'Add Game Results' },
  { to: '/players', label: 'Players' },
  { to: '/history', label: 'Game History' },
  { to: '/stats', label: 'View Statistics' },
];

export default function Home() {
  return (
    <div className={styles.page}>
      <h1 className={styles.title}>Secret Hitler Stats</h1>
      <div className={styles.grid}>
        {NAV.map(({ to, label }) => (
          <Link key={to} to={to} className={styles.card}>{label}</Link>
        ))}
      </div>
    </div>
  );
}
