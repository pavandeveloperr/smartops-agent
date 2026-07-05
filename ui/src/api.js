const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'

async function requestJson(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  })

  const data = await response.json().catch(() => null)

  if (!response.ok) {
    throw new Error(data?.detail || 'Request failed.')
  }

  return data
}

export async function fetchHealth() {
  return requestJson('/health', { method: 'GET' })
}

export async function fetchBanditSnapshot() {
  return requestJson('/bandit', { method: 'GET' })
}

export async function askSupport({ query, model, top_k }) {
  const payload = { query }

  if (model && model !== 'auto') {
    payload.model = model
  }

  if (top_k && top_k !== 'auto') {
    payload.top_k = Number(top_k)
  }

  return requestJson('/query', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export async function submitFeedback(transactionId, score) {
  return requestJson('/feedback', {
    method: 'POST',
    body: JSON.stringify({ transaction_id: transactionId, score }),
  })
}

export { API_BASE_URL }
