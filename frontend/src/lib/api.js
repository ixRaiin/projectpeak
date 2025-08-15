const BASE = '/api';

async function parse(res) {
  if (res.status === 204) return { ok: true }

  const ct = res.headers.get('content-type') || ''
  const text = await res.text()

  let data = null
  if (ct.includes('application/json') && text) {
    try { data = JSON.parse(text) } catch { /* Error */ }
  }
  if (!res.ok) {
    const msg =
      (data && (data.error || data.message)) ||
      (text && !text.startsWith('<') && text) ||
      res.statusText
    throw new Error(msg || 'Request failed')
  }
  return data ?? (text ? { data: text } : {})
}

function toURL(path, params) {
  const url = new URL(BASE + path, window.location.origin);
  if (params) {
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== null && v !== '') url.searchParams.set(k, v);
    });
  }
  return url;
}

function core(path, options = {}) {
  const { method = 'GET', params, body, headers = {} } = options;
  const url = method === 'GET' ? toURL(path, params) : BASE + path;
  const init = {
    method,
    credentials: 'include',
    headers: { 'Content-Type': 'application/json', ...headers }
  };
  if (method !== 'GET' && body !== undefined) {
    init.body = typeof body === 'string' ? body : JSON.stringify(body);
  }
  return fetch(url, init).then(parse);
}
function apiFn(path, options) { return core(path, options); }

apiFn.get    = (path, params)     => core(path, { method: 'GET', params });
apiFn.post   = (path, body)       => core(path, { method: 'POST', body });
apiFn.patch  = (path, body)       => core(path, { method: 'PATCH', body });
apiFn.delete = (path)             => core(path, { method: 'DELETE' });

export default apiFn;
export const api = apiFn;
