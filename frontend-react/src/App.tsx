import { useState, useCallback } from 'react'
import { AppShell } from './components/layout/AppShell'
import { SearchPanel } from './components/search/SearchPanel'
import { ResultsContainer } from './components/results/ResultsContainer'
import { useSearch } from './hooks/useSearch'
import { useBulkSearch } from './hooks/useBulkSearch'

export default function App() {
  const single = useSearch()
  const bulk = useBulkSearch()

  const [lastQuery, setLastQuery] = useState('')
  const [lastStores, setLastStores] = useState<string[]>([])
  const [mode, setMode] = useState<'single' | 'bulk' | null>(null)

  const handleSingleSearch = useCallback(
    (extensionId: string, stores: string[], includePermissions: boolean) => {
      setMode('single')
      setLastQuery(extensionId)
      setLastStores(stores)
      bulk.clearResults()
      single.search(extensionId, stores, includePermissions)
    },
    [single, bulk]
  )

  const handleBulkSearch = useCallback(
    (extensionIds: string[], stores: string[], includePermissions: boolean) => {
      setMode('bulk')
      setLastQuery(extensionIds.join(', '))
      setLastStores(stores)
      single.clearResults()
      bulk.search(extensionIds, stores, includePermissions)
    },
    [single, bulk]
  )

  const loading = single.loading || bulk.loading
  const results = mode === 'bulk' ? bulk.results : single.results
  const error = mode === 'bulk' ? bulk.error : single.error

  return (
    <AppShell>
      <SearchPanel
        onSingleSearch={handleSingleSearch}
        onBulkSearch={handleBulkSearch}
        loading={loading}
      />

      <ResultsContainer
        results={results}
        loading={loading}
        error={error}
        query={lastQuery}
        stores={lastStores}
        totalSearched={mode === 'bulk' ? bulk.totalSearched : undefined}
      />
    </AppShell>
  )
}
