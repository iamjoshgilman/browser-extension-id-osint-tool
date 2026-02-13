import { useState } from 'react'
import { SearchModeToggle, type SearchMode } from './SearchModeToggle'
import { SingleSearchInput } from './SingleSearchInput'
import { BulkSearchInput } from './BulkSearchInput'
import { StoreSelector } from './StoreSelector'
import styles from './SearchPanel.module.css'

interface SearchPanelProps {
  onSingleSearch: (extensionId: string, stores: string[]) => void
  onBulkSearch: (extensionIds: string[], stores: string[]) => void
  loading: boolean
}

export function SearchPanel({ onSingleSearch, onBulkSearch, loading }: SearchPanelProps) {
  const [mode, setMode] = useState<SearchMode>('single')
  const [singleId, setSingleId] = useState('')
  const [bulkIds, setBulkIds] = useState('')
  const [stores, setStores] = useState(['chrome', 'firefox', 'edge'])

  const handleSearch = () => {
    if (stores.length === 0) return

    if (mode === 'single') {
      const id = singleId.trim()
      if (id) onSingleSearch(id, stores)
    } else {
      const ids = bulkIds
        .split('\n')
        .map(id => id.trim())
        .filter(id => id.length > 0)
      if (ids.length > 0) onBulkSearch(ids, stores)
    }
  }

  return (
    <div className={styles.section}>
      <SearchModeToggle mode={mode} onChange={setMode} />

      {mode === 'single' ? (
        <SingleSearchInput
          value={singleId}
          onChange={setSingleId}
          onSubmit={handleSearch}
          disabled={loading}
        />
      ) : (
        <BulkSearchInput
          value={bulkIds}
          onChange={setBulkIds}
          disabled={loading}
        />
      )}

      <StoreSelector selected={stores} onChange={setStores} />

      <button
        className={styles.searchBtn}
        onClick={handleSearch}
        disabled={loading || stores.length === 0}
      >
        {loading
          ? 'Searching...'
          : mode === 'single'
            ? 'Search Extension'
            : 'Search Extensions'}
      </button>
    </div>
  )
}
