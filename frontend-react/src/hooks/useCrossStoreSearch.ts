import { useState, useCallback } from 'react'
import { searchByName } from '../api/endpoints'
import type { ExtensionData } from '../types/extension'

interface UseCrossStoreSearchReturn {
  results: ExtensionData[]
  searchUrls: Record<string, string>
  loading: boolean
  error: string | null
  search: (name: string, currentStore: string) => Promise<void>
  clearResults: () => void
}

export function useCrossStoreSearch(): UseCrossStoreSearchReturn {
  const [results, setResults] = useState<ExtensionData[]>([])
  const [searchUrls, setSearchUrls] = useState<Record<string, string>>({})
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const search = useCallback(async (name: string, currentStore: string) => {
    setLoading(true)
    setError(null)
    setResults([])
    setSearchUrls({})

    try {
      const response = await searchByName(name, [currentStore])

      // Flatten all results from all stores
      const allResults: ExtensionData[] = []
      for (const storeResults of Object.values(response.results)) {
        allResults.push(...storeResults.filter(r => r.found !== false))
      }

      setResults(allResults)
      setSearchUrls(response.search_urls || {})

      if (allResults.length === 0 && Object.keys(response.search_urls).length === 0) {
        setError('No matching extensions found in other stores.')
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Cross-store search failed')
      setResults([])
      setSearchUrls({})
    } finally {
      setLoading(false)
    }
  }, [])

  const clearResults = useCallback(() => {
    setResults([])
    setSearchUrls({})
    setError(null)
  }, [])

  return { results, searchUrls, loading, error, search, clearResults }
}
