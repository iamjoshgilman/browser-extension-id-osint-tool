import { useState, useCallback } from 'react'
import { AppShell } from './components/layout/AppShell'
import { SearchPanel } from './components/search/SearchPanel'
import { BulkProgress } from './components/search/BulkProgress'
import { ResultsContainer } from './components/results/ResultsContainer'
import { useSearch } from './hooks/useSearch'
import { useBulkSearch } from './hooks/useBulkSearch'
import { useBulkSearchAsync } from './hooks/useBulkSearchAsync'

const ASYNC_BULK_THRESHOLD = 5

export default function App() {
  const single = useSearch()
  const bulk = useBulkSearch()
  const asyncBulk = useBulkSearchAsync()

  const [lastQuery, setLastQuery] = useState('')
  const [lastStores, setLastStores] = useState<string[]>([])
  const [mode, setMode] = useState<'single' | 'bulk' | 'async-bulk' | null>(null)

  const handleSingleSearch = useCallback(
    (extensionId: string, stores: string[], includePermissions: boolean) => {
      setMode('single')
      setLastQuery(extensionId)
      setLastStores(stores)
      bulk.clearResults()
      asyncBulk.clearResults()
      single.search(extensionId, stores, includePermissions)
    },
    [single, bulk, asyncBulk]
  )

  const handleBulkSearch = useCallback(
    (extensionIds: string[], stores: string[], includePermissions: boolean) => {
      setLastQuery(extensionIds.join(', '))
      setLastStores(stores)
      single.clearResults()

      if (extensionIds.length > ASYNC_BULK_THRESHOLD) {
        setMode('async-bulk')
        bulk.clearResults()
        asyncBulk.startBulkSearch(extensionIds, stores, includePermissions)
      } else {
        setMode('bulk')
        asyncBulk.clearResults()
        bulk.search(extensionIds, stores, includePermissions)
      }
    },
    [single, bulk, asyncBulk]
  )

  const loading = single.loading || bulk.loading || asyncBulk.loading
  const results =
    mode === 'async-bulk'
      ? asyncBulk.results
      : mode === 'bulk'
        ? bulk.results
        : single.results
  const error =
    mode === 'async-bulk'
      ? asyncBulk.error
      : mode === 'bulk'
        ? bulk.error
        : single.error

  return (
    <AppShell>
      <SearchPanel
        onSingleSearch={handleSingleSearch}
        onBulkSearch={handleBulkSearch}
        loading={loading}
      />

      {mode === 'async-bulk' && (asyncBulk.loading || asyncBulk.status) && (
        <BulkProgress
          completed={asyncBulk.progress.completed}
          total={asyncBulk.progress.total}
          pct={asyncBulk.progress.pct}
          status={asyncBulk.status}
          onCancel={asyncBulk.cancelSearch}
        />
      )}

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
