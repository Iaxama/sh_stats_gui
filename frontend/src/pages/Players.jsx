import { useEffect, useState } from 'react';
import { getGames, getPlayers, getSeasons, createPlayer, updatePlayer, deletePlayer, startSeason } from '../api';
import Avatar from '../components/Avatar';
import AvatarCrop from '../components/AvatarCrop';
import PlayerHover from '../components/PlayerHover';
import styles from './Players.module.css';

function PlayerModal({ player, onClose, onSaved }) {
  const [name, setName] = useState(player?.name ?? '');
  const [saving, setSaving] = useState(false);
  const [cropTarget, setCropTarget] = useState(null);
  const [avatarPath, setAvatarPath] = useState(player?.avatar_path ?? null);
  const isEdit = !!player;

  async function handleSubmit(e) {
    e.preventDefault();
    if (!name.trim()) return;
    setSaving(true);
    try {
      let saved;
      if (isEdit) {
        saved = await updatePlayer(player.id, { name });
      } else {
        saved = await createPlayer({ name });
      }
      onSaved(saved);
    } finally {
      setSaving(false);
    }
  }

  function handleAvatarDone(path) {
    setAvatarPath(path);
    setCropTarget(null);
    // reflect on parent without full reload — parent will refetch
    onSaved({ ...player, avatar_path: path });
  }

  if (cropTarget) {
    return <AvatarCrop playerId={cropTarget} onDone={handleAvatarDone} onCancel={() => setCropTarget(null)} />;
  }

  return (
    <div className="modal-backdrop">
      <div className="modal">
        <h2>{isEdit ? 'Edit Player' : 'Add Player'}</h2>
        <form onSubmit={handleSubmit}>
          <div className="field">
            <label>Name</label>
            <input value={name} onChange={e => setName(e.target.value)} autoFocus required />
          </div>
          {isEdit && (
            <div className="field" style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
              <Avatar path={avatarPath} name={name} size={60} />
              <button type="button" className="btn-secondary" onClick={() => setCropTarget(player.id)}>
                {avatarPath ? 'Change Avatar' : 'Upload Avatar'}
              </button>
            </div>
          )}
          <div className="modal-actions">
            <button type="button" className="btn-secondary" onClick={onClose}>Cancel</button>
            <button type="submit" className="btn-primary" disabled={saving}>
              {saving ? 'Saving…' : 'Save'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function NewSeasonModal({ players, season, onClose, onStarted }) {
  const [retireIds, setRetireIds] = useState(() => new Set());
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  function toggle(id) {
    setRetireIds(current => {
      const next = new Set(current);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  async function confirmStart() {
    setSaving(true);
    setError('');
    try {
      await startSeason([...retireIds]);
      onStarted();
    } catch (err) {
      setError(err.message);
      setSaving(false);
    }
  }

  return (
    <div className="modal-backdrop">
      <div className="modal">
        <h2>Start a new season</h2>
        <p style={{ color: 'var(--text-dim)' }}>
          {season ? `${season.name} will end and its Hall of Fame awards will be saved. ` : ''}
          Select the players who no longer play to retire them. They stay in the all-time stats.
        </p>
        <div className={styles.retireList}>
          {players.map(p => (
            <label key={p.id} className={styles.retireItem}>
              <input type="checkbox" checked={retireIds.has(p.id)} onChange={() => toggle(p.id)} />
              <Avatar path={p.avatar_path} name={p.name} size={32} />
              <span>{p.name}</span>
            </label>
          ))}
        </div>
        {error && <p className="error-msg">{error}</p>}
        <div className="modal-actions">
          <button type="button" className="btn-secondary" onClick={onClose}>Cancel</button>
          <button type="button" className="btn-primary" onClick={confirmStart} disabled={saving}>
            {saving ? 'Starting…' : 'Start new season'}
          </button>
        </div>
      </div>
    </div>
  );
}

export default function Players() {
  const [players, setPlayers] = useState([]);
  const [games, setGames] = useState([]);
  const [modal, setModal] = useState(null); // null | 'add' | 'season' | player-obj
  const [showRetired, setShowRetired] = useState(false);
  const [seasons, setSeasons] = useState([]);

  async function load() {
    const [loadedPlayers, loadedGames, loadedSeasons] = await Promise.all([getPlayers(), getGames(), getSeasons()]);
    setSeasons(loadedSeasons);
    setPlayers(loadedPlayers);
    setGames(loadedGames);
  }

  useEffect(() => { load(); }, []);

  async function handleDelete(id) {
    if (!confirm('Delete this player?')) return;
    await deletePlayer(id);
    setPlayers(ps => ps.filter(p => p.id !== id));
  }

  async function handleRetire(player, retired) {
    if (retired && !confirm(`Retire ${player.name}? They will be excluded from the current season.`)) return;
    const saved = await updatePlayer(player.id, { retired });
    setPlayers(ps => ps.map(p => (p.id === saved.id ? saved : p)));
  }

  function handleSaved(saved) {
    setPlayers(ps => {
      const idx = ps.findIndex(p => p.id === saved.id);
      if (idx === -1) return [...ps, saved];
      const next = [...ps];
      next[idx] = saved;
      return next;
    });
    setModal(null);
    // re-fetch to sync any avatar changes
    load();
  }

  return (
    <div className={styles.page}>
      <div className={styles.header}>
        <h1>Players</h1>
        <div className={styles.headerActions}>
          {players.some(p => p.retired) && (
            <button className="btn-secondary" onClick={() => setShowRetired(v => !v)}>
              {showRetired ? 'Hide retired' : 'Show retired'}
            </button>
          )}
          <button className="btn-secondary" onClick={() => setModal('season')}>Start New Season</button>
          <button className="btn-primary" onClick={() => setModal('add')}>+ Add Player</button>
        </div>
      </div>
      <div className={styles.list}>
        {players.length === 0 && <p style={{ color: 'var(--text-dim)' }}>No players yet.</p>}
        {players.filter(p => showRetired || !p.retired).map(p => (
          <div key={p.id} className={`${styles.row} ${p.retired ? styles.retired : ''}`}>
            <PlayerHover player={p} games={games}>
              <Avatar path={p.avatar_path} name={p.name} size={150} />
              <span className={styles.name}>{p.name}{p.retired && <em className={styles.badge}>Retired</em>}</span>
            </PlayerHover>
            <div className={styles.actions}>
              <button className="btn-secondary" onClick={() => setModal(p)}>Edit</button>
              <button className="btn-secondary" onClick={() => handleRetire(p, !p.retired)}>{p.retired ? 'Unretire' : 'Retire'}</button>
              <button className="btn-danger" onClick={() => handleDelete(p.id)}>Delete</button>
            </div>
          </div>
        ))}
      </div>
      {modal === 'season' && (
        <NewSeasonModal
          players={players.filter(p => !p.retired)}
          season={seasons.find(season => season.end_date == null)}
          onClose={() => setModal(null)}
          onStarted={() => { setModal(null); load(); }}
        />
      )}
      {modal && modal !== 'season' && (
        <PlayerModal
          player={modal === 'add' ? null : modal}
          onClose={() => setModal(null)}
          onSaved={handleSaved}
        />
      )}
    </div>
  );
}
