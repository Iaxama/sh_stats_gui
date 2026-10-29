/* eslint-disable react/prop-types */
import styles from './ScopeToggle.module.css';

export default function ScopeToggle({ scope, setScope, currentSeason, showRetired, setShowRetired, hasRetired }) {
  return (
    <div className={styles.wrap}>
      <div className={styles.toggle} role="group" aria-label="Statistics scope">
        <button
          type="button"
          className={scope === 'season' ? styles.active : ''}
          onClick={() => setScope('season')}
        >
          {currentSeason?.name ?? 'Current season'}
        </button>
        <button
          type="button"
          className={scope === 'all' ? styles.active : ''}
          onClick={() => setScope('all')}
        >
          All-time
        </button>
      </div>
      {scope === 'season' && hasRetired && (
        <button type="button" className={`btn-secondary ${styles.retired}`} onClick={() => setShowRetired(!showRetired)}>
          {showRetired ? 'Hide retired players' : 'Show retired players'}
        </button>
      )}
    </div>
  );
}
