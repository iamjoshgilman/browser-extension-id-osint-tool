import { useState } from 'react'
import type { ExtensionData } from '../../types/extension'
import { getAggregateRisk } from '../../utils/permissions'
import { useCrossStoreSearch } from '../../hooks/useCrossStoreSearch'
import { StoreBadge } from './StoreBadge'
import { CachedBadge } from './CachedBadge'
import { PermissionBadge } from './PermissionBadge'
import { ResultMeta } from './ResultMeta'
import { PermissionsList } from './PermissionsList'
import { DelistedBanner } from './DelistedBanner'
import { CrossStoreResults } from './CrossStoreResults'
import styles from './ResultCard.module.css'

interface ResultCardProps {
  extension: ExtensionData
}

export function ResultCard({ extension }: ResultCardProps) {
  const [showCrossStore, setShowCrossStore] = useState(false)
  const crossStore = useCrossStoreSearch()

  const aggregateRisk = extension.store_source !== 'chrome' && extension.permissions?.length > 0
    ? getAggregateRisk(extension.permissions)
    : null

  const handleCrossStoreClick = async () => {
    if (showCrossStore) {
      setShowCrossStore(false)
      crossStore.clearResults()
    } else {
      setShowCrossStore(true)
      if (crossStore.results.length === 0 && !crossStore.loading) {
        await crossStore.search(extension.name, extension.store_source)
      }
    }
  }

  return (
    <div className={styles.card}>
      {extension.delisted && (
        <DelistedBanner store={extension.store_source} scrapedAt={extension.scraped_at} />
      )}

      <div className={styles.header}>
        <div>
          <div className={styles.nameRow}>
            <span className={styles.name}>{extension.name}</span>
            {aggregateRisk && (
              <PermissionBadge risk={aggregateRisk} label={`Risk: ${aggregateRisk}`} />
            )}
          </div>
          <div className={styles.badges}>
            <StoreBadge store={extension.store_source} />
            {extension.cached && <CachedBadge />}
          </div>
        </div>
        <div className={styles.id}>{extension.extension_id}</div>
      </div>

      <ResultMeta extension={extension} />

      <PermissionsList
        permissions={extension.permissions || []}
        store={extension.store_source}
      />

      {extension.description && (
        <div className={styles.description}>{extension.description}</div>
      )}

      {extension.store_url && (
        <a
          href={extension.store_url}
          target="_blank"
          rel="noopener noreferrer"
          className={styles.storeLink}
        >
          View in Store &rarr;
        </a>
      )}

      <button onClick={handleCrossStoreClick} className={styles.crossStoreBtn}>
        {showCrossStore ? 'Hide' : 'Find in other stores'}
      </button>

      {showCrossStore && (
        <CrossStoreResults
          results={crossStore.results}
          searchUrls={crossStore.searchUrls}
          loading={crossStore.loading}
          error={crossStore.error}
        />
      )}
    </div>
  )
}
