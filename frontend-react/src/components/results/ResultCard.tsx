import type { ExtensionData } from '../../types/extension'
import { getAggregateRisk } from '../../utils/permissions'
import { StoreBadge } from './StoreBadge'
import { CachedBadge } from './CachedBadge'
import { PermissionBadge } from './PermissionBadge'
import { ResultMeta } from './ResultMeta'
import { PermissionsList } from './PermissionsList'
import styles from './ResultCard.module.css'

interface ResultCardProps {
  extension: ExtensionData
}

export function ResultCard({ extension }: ResultCardProps) {
  const aggregateRisk = extension.store_source !== 'chrome' && extension.permissions?.length > 0
    ? getAggregateRisk(extension.permissions)
    : null

  return (
    <div className={styles.card}>
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
    </div>
  )
}
