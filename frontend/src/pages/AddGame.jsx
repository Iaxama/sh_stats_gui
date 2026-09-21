import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getGames, getPlayers, createGame } from '../api';
import Avatar from '../components/Avatar';
import PlayerHover from '../components/PlayerHover';
import styles from './AddGame.module.css';

const ROLES = ['liberal', 'fascist', 'hitler'];
const WIN_CONDITIONS = {
  liberal: [
    { value: 'policies_enacted', label: 'Policies Enacted' },
    { value: 'hitler_executed', label: 'Hitler Executed' },
  ],
  fascist: [
    { value: 'policies_enacted', label: 'Policies Enacted' },
    { value: 'hitler_elected', label: 'Hitler Elected' },
  ],
};

export default function AddGame() {
  const navigate = useNavigate();
  const [players, setPlayers] = useState([]);
  const [games, setGames] = useState([]);
  const [selected, setSelected] = useState([]);
  const [winningTeam, setWinningTeam] = useState('liberal');
  const [winningCondition, setWinningCondition] = useState('policies_enacted');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [showSniperDialog, setShowSniperDialog] = useState(false);
  const [sniperId, setSniperId] = useState('');

  useEffect(() => {
    Promise.all([getPlayers(), getGames()]).then(([loadedPlayers, loadedGames]) => {
      setPlayers(loadedPlayers);
      setGames(loadedGames);
    });
  }, []);

  // reset condition when team changes
  useEffect(() => {
    setWinningCondition(WIN_CONDITIONS[winningTeam][0].value);
  }, [winningTeam]);

  function setRole(id, role) {
    setSelected(sel => {
      const existing = sel.find(s => s.player_id === id);
      if (existing) {
        // Player already selected, update their role
        return sel.map(s => s.player_id === id ? { ...s, role } : s);
      } else {
        // Player not selected, add them with this role
        return [...sel, { player_id: id, role, died: false }];
      }
    });
  }

  function clearRole(id) {
    // Remove player from selected when role is cleared
    setSelected(sel => sel.filter(s => s.player_id !== id));
  }

  function setDied(id, died) {
    setSelected(sel => sel.map(s => s.player_id === id ? { ...s, died } : s));
  }

  function validateGame() {
    const n = selected.length;
    if (n < 5) { setError('Select at least 5 players.'); return false; }
    const hitlers = selected.filter(s => s.role === 'hitler');
    if (hitlers.length !== 1) { setError('Exactly one Hitler required.'); return false; }
    // floor((n-1)/2) - 1 fascists (not counting Hitler)
    const expectedFascists = Math.floor((n - 1) / 2) - 1;
    const expectedLiberals = n - expectedFascists - 1;
    const fascistCount = selected.filter(s => s.role === 'fascist').length;
    const liberalCount = selected.filter(s => s.role === 'liberal').length;
    if (fascistCount !== expectedFascists) {
      setError(`With ${n} players, there must be exactly ${expectedFascists} Fascist(s) (+ Hitler). Got ${fascistCount}.`);
      return false;
    }
    if (liberalCount !== expectedLiberals) {
      setError(`With ${n} players, there must be exactly ${expectedLiberals} Liberal(s). Got ${liberalCount}.`);
      return false;
    }
    setError('');
    return true;
  }

  async function saveGame(selectedSniperId = null) {
    setSaving(true);
    setError('');
    try {
      await createGame({
        players: selected,
        winning_team: winningTeam,
        winning_condition: winningCondition,
        sniper_id: selectedSniperId,
      });
      navigate('/history');
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  }

  function handleSubmit(e) {
    e.preventDefault();
    if (!validateGame()) return;

    if (winningTeam === 'liberal' && winningCondition === 'hitler_executed') {
      const candidates = selected.filter(entry => entry.role !== 'hitler');
      setSniperId(candidates[0]?.player_id ?? '');
      setShowSniperDialog(true);
      return;
    }

    saveGame();
  }

  function confirmSniper() {
    if (!sniperId) {
      setError('Select the player who killed Hitler.');
      return;
    }
    setShowSniperDialog(false);
    saveGame(sniperId);
  }

  const gamesPlayed = games.reduce((counts, game) => {
    for (const result of game.players) {
      counts[result.player_id] = (counts[result.player_id] ?? 0) + 1;
    }
    return counts;
  }, {});
  const sortedPlayers = [...players].sort((a, b) =>
    (gamesPlayed[b.id] ?? 0) - (gamesPlayed[a.id] ?? 0)
      || a.name.localeCompare(b.name)
  );

  return (
    <div className={styles.page}>
      <h1>Add Game Results</h1>
      <form onSubmit={handleSubmit}>
        <section className={styles.section}>
          <h2>Players &amp; Roles</h2>
          {players.length === 0 && <p style={{ color: 'var(--text-dim)' }}>Add players first.</p>}
          <div className={styles.playerGrid}>
            {sortedPlayers.map(p => {
              const entry = selected.find(s => s.player_id === p.id);
              const active = !!entry;
              return (
                <div key={p.id} className={`${styles.playerCard} ${active ? styles.active : ''}`}>
                  <div className={styles.playerHeader}>
                    <PlayerHover player={p} games={games}>
                      <span>{p.name}</span>
                      <Avatar path={p.avatar_path} name={p.name} size={150} />
                    </PlayerHover>
                  </div>
                  <div className={styles.playerControls}>
                    <div className={styles.roleButtons}>
                      <button 
                        type="button"
                        className={`${styles.roleBtn} ${entry?.role === 'liberal' ? styles.roleActive : ''}`}
                        style={entry?.role === 'liberal' ? { backgroundColor: '#3b82f6', color: 'white' } : {}}
                        onClick={() => setRole(p.id, 'liberal')}
                      >
                        Liberal
                      </button>
                      <button 
                        type="button"
                        className={`${styles.roleBtn} ${entry?.role === 'fascist' ? styles.roleActive : ''}`}
                        style={entry?.role === 'fascist' ? { backgroundColor: '#ef4444', color: 'white' } : {}}
                        onClick={() => setRole(p.id, 'fascist')}
                      >
                        Fascist
                      </button>
                      <button 
                        type="button"
                        className={`${styles.roleBtn} ${entry?.role === 'hitler' ? styles.roleActive : ''}`}
                        style={entry?.role === 'hitler' ? { backgroundColor: '#8b0000', color: 'white' } : {}}
                        onClick={() => setRole(p.id, 'hitler')}
                      >
                        Hitler
                      </button>
                    </div>
                    <label className={styles.diedLabel}>
                      <input type="checkbox" checked={entry?.died || false} onChange={e => setDied(p.id, e.target.checked)} />
                      Died
                    </label>
                  </div>
                </div>
              );
            })}
          </div>
        </section>

        <section className={styles.section}>
          <h2>Result</h2>
          <div className={styles.resultRow}>
            <div className="field">
              <label>Winning Team</label>
              <select value={winningTeam} onChange={e => setWinningTeam(e.target.value)}>
                <option value="liberal">Liberal</option>
                <option value="fascist">Fascist</option>
              </select>
            </div>
            <div className="field">
              <label>Winning Condition</label>
              <select value={winningCondition} onChange={e => setWinningCondition(e.target.value)}>
                {WIN_CONDITIONS[winningTeam].map(c => (
                  <option key={c.value} value={c.value}>{c.label}</option>
                ))}
              </select>
            </div>
          </div>
        </section>

        {error && <p className="error-msg">{error}</p>}
        <div style={{ display: 'flex', gap: '0.6rem', justifyContent: 'flex-end', marginTop: '1.2rem' }}>
          <button type="button" className="btn-secondary" onClick={() => navigate('/')}>Cancel</button>
          <button type="submit" className="btn-primary" disabled={saving}>
            {saving ? 'Saving…' : 'Save Game'}
          </button>
        </div>
      </form>

      {showSniperDialog && (
        <div className={styles.modalBackdrop} role="presentation">
          <div className={styles.modal} role="dialog" aria-modal="true" aria-labelledby="sniper-dialog-title">
            <h2 id="sniper-dialog-title">Who killed Hitler?</h2>
            <p>Select the player who earned the Sniper stat.</p>
            <div className="field">
              <label htmlFor="sniper-player">Sniper</label>
              <select id="sniper-player" value={sniperId} onChange={e => setSniperId(e.target.value)} autoFocus>
                {selected.filter(entry => entry.role !== 'hitler').map(entry => {
                  const player = players.find(candidate => candidate.id === entry.player_id);
                  return <option key={entry.player_id} value={entry.player_id}>{player?.name ?? 'Unknown player'}</option>;
                })}
              </select>
            </div>
            <div className={styles.modalActions}>
              <button type="button" className="btn-secondary" onClick={() => setShowSniperDialog(false)}>Back</button>
              <button type="button" className="btn-primary" onClick={confirmSniper} disabled={saving}>Confirm &amp; Save</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
