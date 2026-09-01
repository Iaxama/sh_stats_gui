export default function Avatar({ path, name, size = 40 }) {
  if (path) {
    const url = '/avatars/' + path.split('/').pop();
    return (
      <img
        src={url}
        alt={name}
        style={{ width: size, height: size, borderRadius: '50%', objectFit: 'cover', border: '2px solid var(--border)' }}
      />
    );
  }
  return (
    <div style={{
      width: size, height: size, borderRadius: '50%',
      background: 'var(--surface2)', border: '2px solid var(--border)',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      fontSize: size * 0.45, color: 'var(--text-dim)', userSelect: 'none',
    }}>
      {name ? name[0].toUpperCase() : '?'}
    </div>
  );
}
