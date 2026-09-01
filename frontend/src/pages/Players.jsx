import { useEffect, useState } from 'react';
import { getPlayers, createPlayer, updatePlayer, deletePlayer } from '../api';
import Avatar from '../components/Avatar';
import AvatarCrop from '../components/AvatarCrop';
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

export default function Players() {
  const [players, setPlayers] = useState([]);
  const [modal, setModal] = useState(null); // null | 'add' | player-obj

  async function load() {
    setPlayers(await getPlayers());
  }

  useEffect(() => { load(); }, []);

  async function handleDelete(id) {
    if (!confirm('Delete this player?')) return;
    await deletePlayer(id);
    setPlayers(ps => ps.filter(p => p.id !== id));
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
        <button className="btn-primary" onClick={() => setModal('add')}>+ Add Player</button>
      </div>
      <div className={styles.list}>
        {players.length === 0 && <p style={{ color: 'var(--text-dim)' }}>No players yet.</p>}
        {players.map(p => (
          <div key={p.id} className={styles.row}>
            <Avatar path={p.avatar_path} name={p.name} size={44} />
            <span className={styles.name}>{p.name}</span>
            <div className={styles.actions}>
              <button className="btn-secondary" onClick={() => setModal(p)}>Edit</button>
              <button className="btn-danger" onClick={() => handleDelete(p.id)}>Delete</button>
            </div>
          </div>
        ))}
      </div>
      {modal && (
        <PlayerModal
          player={modal === 'add' ? null : modal}
          onClose={() => setModal(null)}
          onSaved={handleSaved}
        />
      )}
    </div>
  );
}
