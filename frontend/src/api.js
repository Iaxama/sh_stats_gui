const BASE = '/api';

async function req(method, path, body) {
  const opts = { method, headers: {} };
  if (body instanceof FormData) {
    opts.body = body;
  } else if (body !== undefined) {
    opts.headers['Content-Type'] = 'application/json';
    opts.body = JSON.stringify(body);
  }
  const res = await fetch(BASE + path, opts);
  if (res.status === 204) return null;
  const json = await res.json();
  if (!res.ok) throw new Error(json.error || res.statusText);
  return json;
}

export const getPlayers = () => req('GET', '/players');
export const createPlayer = (data) => req('POST', '/players', data);
export const updatePlayer = (id, data) => req('PUT', `/players/${id}`, data);
export const deletePlayer = (id) => req('DELETE', `/players/${id}`);
export const uploadAvatar = (id, file) => {
  const fd = new FormData();
  fd.append('avatar', file);
  return req('POST', `/players/${id}/avatar`, fd);
};

export const getGames = () => req('GET', '/games');
export const createGame = (data) => req('POST', '/games', data);
export const deleteGame = (id) => req('DELETE', `/games/${id}`);
