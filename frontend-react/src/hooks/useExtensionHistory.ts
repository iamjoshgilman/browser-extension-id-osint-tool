import { useState, useCallback } from 'react'
import { getExtensionHistory } from '../api/endpoints'
import type { ExtensionHistoryResponse } from '../types/extension'

interface UseExtensionHistoryReturn {
  history: ExtensionHistoryResponse | null
  loading: boolean
  error: string | null
  fetchHistory: (extensionId: string, store: string) => Promise<void>
  clearHistory: () => void
}

export function useExtensionHistory(): UseExtensionHistoryReturn {
  const [history, setHistory] = useState<ExtensionHistoryResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchHistory = useCallback(async (extensionId: string, store: string) => {
    setLoading(true)
    setError(null)
    setHistory(null)

    try {
      const response = await getExtensionHistory(extensionId, store)
      setHistory(response)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch extension history')
      setHistory(null)
    } finally {
      setLoading(false)
    }
  }, [])

  const clearHistory = useCallback(() => {
    setHistory(null)
    setError(null)
  }, [])

  return { history, loading, error, fetchHistory, clearHistory }
}
