// src/lib/api.js
const API_PREFIX = import.meta.env.VITE_API_PREFIX || '/api';

async function request(method, path, data) {
  const res = await fetch(`${API_PREFIX}${path}`, {
    method,
    headers: data ? { 'Content-Type': 'application/json' } : undefined,
    body: data ? JSON.stringify(data) : undefined,
    // include cookies just in case your backend uses httpOnly session cookies
    credentials: 'include',
  });

  const ctype = res.headers.get('content-type') || '';
  const isJson = ctype.includes('application/json');
  const payload = isJson ? await res.json().catch(() => ({})) : await res.text();

  if (!res.ok) {
    const msg =
      (isJson && (payload.error || payload.message)) ||
      (typeof payload === 'string' && payload) ||
      res.statusText;
    throw new Error(msg || 'Request failed');
  }

  return payload;
}

const api = {
  get: (p) => request('GET', p),
  post: (p, d) => request('POST', p, d),
  patch: (p, d) => request('PATCH', p, d),
  delete: (p) => request('DELETE', p),
};

// Backward-compat helper for any legacy `apiClient().get(...)` / `api().get(...)`
export const apiClient = () => api;

// Preferred import:  import api from '@/lib/api'
export default api;
