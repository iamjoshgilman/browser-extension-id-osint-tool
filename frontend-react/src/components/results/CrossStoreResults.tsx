import type { ExtensionData } from '../../types/extension'
import { sanitizeUrl } from '../../utils/sanitizeUrl'
import { StoreBadge } from './StoreBadge'
import styles from './CrossStoreResults.module.css'

interface CrossStoreResultsProps {
  results: ExtensionData[]
  searchUrls: Record<string, string>
  loading: boolean
  error: string | null
}

export function CrossStoreResults({
  results,
  searchUrls,
  loading,
  error,
}: CrossStoreResultsProps) {
  if (loading) {
    return (
      <div className={styles.container}>
        <div className={styles.loading}>Searching other stores...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className={styles.container}>
        <div className={styles.error}>{error}</div>
      </div>
    )
  }

  const hasResults = results.length > 0
  const hasSearchUrls = Object.keys(searchUrls).length > 0

  if (!hasResults && !hasSearchUrls) {
    return (
      <div className={styles.container}>
        <div className={styles.noResults}>No matching extensions found in other stores.</div>
      </div>
    )
  }

  return (
    <div className={styles.container}>
      {hasResults && (
        <div className={styles.results}>
          <h4 className={styles.heading}>Found in other stores:</h4>
          <div className={styles.grid}>
            {results.map((ext, idx) => {
              const safeStoreUrl = sanitizeUrl(ext.store_url)
              return (
                <div key={`${ext.store_source}-${ext.extension_id}-${idx}`} className={styles.card}>
                  <div className={styles.cardHeader}>
                    <span className={styles.name}>{ext.name}</span>
                    <StoreBadge store={ext.store_source} />
                  </div>
                  <div className={styles.meta}>
                    <span className={styles.publisher}>{ext.publisher}</span>
                    {ext.user_count && ext.user_count !== 'unknown' && (
                      <span className={styles.users}>{ext.user_count} users</span>
                    )}
                  </div>
                  {safeStoreUrl && (
                    <a
                      href={safeStoreUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className={styles.link}
                    >
                      View in store &rarr;
                    </a>
                  )}
                </div>
              )
            })}
          </div>
        </div>
      )}

      {hasSearchUrls && (
        <div className={styles.searchUrls}>
          <h4 className={styles.heading}>Manual search links:</h4>
          <div className={styles.urlList}>
            {Object.entries(searchUrls).map(([store, url]) => {
              const safeUrl = sanitizeUrl(url)
              return safeUrl ? (
                <a
                  key={store}
                  href={safeUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className={styles.searchLink}
                >
                  <StoreBadge store={store} />
                  <span>Search on {store.toUpperCase()}</span>
                  <span className={styles.arrow}>&rarr;</span>
                </a>
              ) : null
            })}
          </div>
        </div>
      )}
    </div>
  )
}
