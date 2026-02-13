import { useState } from 'react'
import type { ExtensionData } from '../../types/extension'
import { getAggregateRisk } from '../../utils/permissions'
import { sanitizeUrl } from '../../utils/sanitizeUrl'
import { useCrossStoreSearch } from '../../hooks/useCrossStoreSearch'
import { useExtensionHistory } from '../../hooks/useExtensionHistory'
import { StoreBadge } from './StoreBadge'
import { CachedBadge } from './CachedBadge'
import { PermissionBadge } from './PermissionBadge'
import { ResultMeta } from './ResultMeta'
import { PermissionsList } from './PermissionsList'
import { DelistedBanner } from './DelistedBanner'
import { CrossStoreResults } from './CrossStoreResults'
import { PermissionHistory } from './PermissionHistory'
import { EnrichmentLinks } from './EnrichmentLinks'
import styles from './ResultCard.module.css'

interface ResultCardProps {
  extension: ExtensionData
}

export function ResultCard({ extension }: ResultCardProps) {
  const [showCrossStore, setShowCrossStore] = useState(false)
  const [showHistory, setShowHistory] = useState(false)
  const crossStore = useCrossStoreSearch()
  const extensionHistory = useExtensionHistory()

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

  const handleHistoryClick = async () => {
    if (showHistory) {
      setShowHistory(false)
      extensionHistory.clearHistory()
    } else {
      setShowHistory(true)
      if (!extensionHistory.history && !extensionHistory.loading) {
        await extensionHistory.fetchHistory(extension.extension_id, extension.store_source)
      }
    }
  }

  const hasPermissions = extension.permissions && extension.permissions.length > 0
  const safeStoreUrl = sanitizeUrl(extension.store_url)

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

      <PermissionsList permissions={extension.permissions || []} />

      {extension.description && (
        <div className={styles.description}>{extension.description}</div>
      )}

      {safeStoreUrl && (
        <a
          href={safeStoreUrl}
          target="_blank"
          rel="noopener noreferrer"
          className={styles.storeLink}
        >
          View in Store &rarr;
        </a>
      )}

      <EnrichmentLinks
        extensionId={extension.extension_id}
        store={extension.store_source}
      />

      <div className={styles.actionButtons}>
        <button onClick={handleCrossStoreClick} className={styles.actionBtn}>
          {showCrossStore ? 'Hide' : 'Find in other stores'}
        </button>

        {hasPermissions && (
          <button onClick={handleHistoryClick} className={styles.actionBtn}>
            {showHistory ? 'Hide' : 'View Permission History'}
          </button>
        )}
      </div>

      {showCrossStore && (
        <CrossStoreResults
          results={crossStore.results}
          searchUrls={crossStore.searchUrls}
          loading={crossStore.loading}
          error={crossStore.error}
        />
      )}

      {showHistory && (
        <>
          {extensionHistory.loading && (
            <div className={styles.historyLoading}>Loading permission history...</div>
          )}
          {extensionHistory.error && (
            <div className={styles.historyError}>{extensionHistory.error}</div>
          )}
          {extensionHistory.history && (
            <PermissionHistory history={extensionHistory.history} />
          )}
        </>
      )}
    </div>
  )
}
