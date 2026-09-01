import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getPlayers, createGame } from '../api';
import Avatar from '../components/Avatar';
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
  const [selected, setSelected] = useState([]);
  const [winningTeam, setWinningTeam] = useState('liberal');
  const [winningCondition, setWinningCondition] = useState('policies_enacted');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => { getPlayers().then(setPlayers); }, []);

  // reset condition when team changes
  useEffect(() => {
    setWinningCondition(WIN_CONDITIONS[winningTeam][0].value);
  }, [winningTeam]);

  function togglePlayer(id) {
    setSelected(sel => {
      if (sel.find(s => s.player_id === id)) return sel.filter(s => s.player_id !== id);
      return [...sel, { player_id: id, role: 'liberal', died: false }];
    });
  }

  function setRole(id, role) {
    setSelected(sel => sel.map(s => s.player_id === id ? { ...s, role } : s));
  }

  function setDied(id, died) {
    setSelected(sel => sel.map(s => s.player_id === id ? { ...s, died } : s));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    if (selected.length < 5) { setError('Select at least 5 players.'); return; }
    const hitlers = selected.filter(s => s.role === 'hitler');
    if (hitlers.length !== 1) { setError('Exactly one Hitler required.'); return; }
    setSaving(true);
    setError('');
    try {
      await createGame({ players: selected, winning_team: winningTeam, winning_condition: winningCondition });
      navigate('/history');
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className={styles.page}>
      <h1>Add Game Results</h1>
      <form onSubmit={handleSubmit}>
        <section className={styles.section}>
          <h2>Players &amp; Roles</h2>
          {players.length === 0 && <p style={{ color: 'var(--text-dim)' }}>Add players first.</p>}
          <div className={styles.playerGrid}>
            {players.map(p => {
              const entry = selected.find(s => s.player_id === p.id);
              const active = !!entry;
              return (
                <div key={p.id} className={`${styles.playerCard} ${active ? styles.active : ''}`}>
                  <div className={styles.playerHeader} onClick={() => togglePlayer(p.id)}>
                    <Avatar path={p.avatar_path} name={p.name} size={36} />
                    <span>{p.name}</span>
                    <input type="checkbox" checked={active} readOnly />
                  </div>
                  {active && (
                    <div className={styles.playerControls}>
                      <select value={entry.role} onChange={e => setRole(p.id, e.target.value)}>
                        {ROLES.map(r => <option key={r} value={r}>{r}</option>)}
                      </select>
                      <label className={styles.diedLabel}>
                        <input type="checkbox" checked={entry.died} onChange={e => setDied(p.id, e.target.checked)} />
                        Died
                      </label>
                    </div>
                  )}
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
    </div>
  );
}
