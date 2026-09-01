import { Link, useLocation } from 'react-router-dom';
import styles from './Nav.module.css';

const LINKS = [
  { to: '/', label: 'Home' },
  { to: '/players', label: 'Players' },
  { to: '/add-game', label: 'Add Game' },
  { to: '/history', label: 'History' },
  { to: '/stats', label: 'Stats' },
];

export default function Nav() {
  const { pathname } = useLocation();
  return (
    <nav className={styles.nav}>
      {LINKS.map(({ to, label }) => (
        <Link key={to} to={to} className={`${styles.link} ${pathname === to ? styles.active : ''}`}>
          {label}
        </Link>
      ))}
    </nav>
  );
}
