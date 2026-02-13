import type { ApiError } from '../types/api'

const API_BASE = '/api'

class ApiClient {
  private headers: Record<string, string> = {
    'Content-Type': 'application/json',
  }

  constructor() {
    const apiKey = localStorage.getItem('api_key')
    if (apiKey) {
      this.headers['X-API-Key'] = apiKey
    }
  }

  setApiKey(key: string | null) {
    if (key) {
      this.headers['X-API-Key'] = key
      localStorage.setItem('api_key', key)
    } else {
      delete this.headers['X-API-Key']
      localStorage.removeItem('api_key')
    }
  }

  async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${API_BASE}${endpoint}`
    const response = await fetch(url, {
      ...options,
      headers: { ...this.headers, ...options.headers as Record<string, string> },
    })

    if (!response.ok) {
      const err: ApiError = await response.json().catch(() => ({ error: `HTTP ${response.status}` }))
      throw new Error(err.error || `HTTP ${response.status}`)
    }

    return response.json()
  }
}

export const apiClient = new ApiClient()
