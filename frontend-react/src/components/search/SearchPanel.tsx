import { useState } from 'react'
import { SearchModeToggle, type SearchMode } from './SearchModeToggle'
import { SingleSearchInput } from './SingleSearchInput'
import { BulkSearchInput } from './BulkSearchInput'
import { StoreSelector } from './StoreSelector'
import styles from './SearchPanel.module.css'

interface SearchPanelProps {
  onSingleSearch: (extensionId: string, stores: string[], includePermissions: boolean) => void
  onBulkSearch: (extensionIds: string[], stores: string[], includePermissions: boolean) => void
  loading: boolean
}

export function SearchPanel({ onSingleSearch, onBulkSearch, loading }: SearchPanelProps) {
  const [mode, setMode] = useState<SearchMode>('single')
  const [singleId, setSingleId] = useState('')
  const [bulkIds, setBulkIds] = useState('')
  const [stores, setStores] = useState(['chrome', 'firefox', 'edge', 'safari'])
  const [includePermissions, setIncludePermissions] = useState(false)

  const handleSearch = () => {
    if (stores.length === 0) return

    if (mode === 'single') {
      const id = singleId.trim()
      if (id) onSingleSearch(id, stores, includePermissions)
    } else {
      const ids = bulkIds
        .split('\n')
        .map(id => id.trim())
        .filter(id => id.length > 0)
      if (ids.length > 0) onBulkSearch(ids, stores, includePermissions)
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

      <div className={styles.optionsRow}>
        <label className={styles.checkboxLabel}>
          <input
            type="checkbox"
            checked={includePermissions}
            onChange={(e) => setIncludePermissions(e.target.checked)}
            className={styles.checkbox}
          />
          <span>Extract Chrome permissions (slower)</span>
        </label>
      </div>

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
