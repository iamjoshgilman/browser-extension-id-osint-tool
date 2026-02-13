import { useState, useCallback } from 'react'
import { bulkSearchExtensions } from '../api/endpoints'
import type { ExtensionData } from '../types/extension'

interface UseBulkSearchReturn {
  results: ExtensionData[]
  totalSearched: number
  loading: boolean
  error: string | null
  search: (extensionIds: string[], stores: string[], includePermissions?: boolean) => Promise<void>
  clearResults: () => void
}

export function useBulkSearch(): UseBulkSearchReturn {
  const [results, setResults] = useState<ExtensionData[]>([])
  const [totalSearched, setTotalSearched] = useState(0)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const search = useCallback(
    async (extensionIds: string[], stores: string[], includePermissions = false) => {
      setLoading(true)
      setError(null)
      setTotalSearched(extensionIds.length)
      try {
        const response = await bulkSearchExtensions({
          extension_ids: extensionIds,
          stores,
          include_permissions: includePermissions,
        })
        const allFound: ExtensionData[] = []
        for (const extResults of Object.values(response.results)) {
          allFound.push(...extResults.filter(r => r.found !== false))
        }
        setResults(allFound)
        if (allFound.length === 0) {
          setError('No extensions found in selected stores.')
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Bulk search failed')
        setResults([])
      } finally {
        setLoading(false)
      }
    },
    []
  )

  const clearResults = useCallback(() => {
    setResults([])
    setError(null)
    setTotalSearched(0)
  }, [])

  return { results, totalSearched, loading, error, search, clearResults }
}
