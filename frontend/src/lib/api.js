// src/lib/api.js
const API_PREFIX = import.meta.env.VITE_API_PREFIX || '/api'

// Safely get token from your auth store or localStorage without creating import cycles
async function getAuthToken() {
  try {
    // dynamic import avoids circular deps during app bootstrap
    const { useAuth } = await import('@/stores/auth.js')
    const auth = useAuth()
    return auth?.token || auth?.user?.token || null
  } catch {
    // fallback if store is not ready
    return localStorage.getItem('token')
  }
}

async function request(method, path, data) {
  const token = await getAuthToken()

  // Build headers
  const headers = {}
  if (data) headers['Content-Type'] = 'application/json'
  if (token) headers['Authorization'] = `Bearer ${token}`

  const res = await fetch(`${API_PREFIX}${path}`, {
    method,
    headers,
    body: data ? JSON.stringify(data) : undefined,
    credentials: 'include', // keep if you also use httpOnly cookies
  })

  // Handle auth failures early
  if (res.status === 401) {
    // Optional: clear stored token so UI updates
    try {
      const { useAuth } = await import('@/stores/auth.js')
      const auth = useAuth()
      auth?.logout?.()
    } catch {/* no-op if store is not ready */ }
    // Redirect to login (route guards will handle the rest)
    if (location.pathname !== '/login') location.replace('/login')
    throw new Error('Authentication required')
  }

  const ctype = res.headers.get('content-type') || ''
  const isJson = ctype.includes('application/json')
  const payload = isJson ? await res.json().catch(() => ({})) : await res.text()

  if (!res.ok) {
    const msg =
      (isJson && (payload.error || payload.message)) ||
      (typeof payload === 'string' && payload) ||
      res.statusText
    throw new Error(msg || 'Request failed')
  }

  return payload
}

const api = {
  get: (p) => request('GET', p),
  post: (p, d) => request('POST', p, d),
  patch: (p, d) => request('PATCH', p, d),
  delete: (p) => request('DELETE', p),
}

export const apiClient = () => api
export default api
