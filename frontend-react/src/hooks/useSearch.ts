import { useState, useCallback } from 'react'
import { searchExtension } from '../api/endpoints'
import type { ExtensionData } from '../types/extension'

interface UseSearchReturn {
  results: ExtensionData[]
  loading: boolean
  error: string | null
  search: (extensionId: string, stores: string[]) => Promise<void>
  clearResults: () => void
}

export function useSearch(): UseSearchReturn {
  const [results, setResults] = useState<ExtensionData[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const search = useCallback(async (extensionId: string, stores: string[]) => {
    setLoading(true)
    setError(null)
    try {
      const response = await searchExtension({ extension_id: extensionId, stores })
      const found = (response.results || []).filter(r => r.found !== false)
      setResults(found)
      if (found.length === 0) {
        setError(`Extension "${extensionId}" not found in selected stores.`)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Search failed')
      setResults([])
    } finally {
      setLoading(false)
    }
  }, [])

  const clearResults = useCallback(() => {
    setResults([])
    setError(null)
  }, [])

  return { results, loading, error, search, clearResults }
}
