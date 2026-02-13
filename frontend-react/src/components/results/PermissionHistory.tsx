import { useState } from 'react'
import type { ExtensionHistoryResponse } from '../../types/extension'
import { PermissionDiff } from './PermissionDiff'
import styles from './PermissionHistory.module.css'

interface PermissionHistoryProps {
  history: ExtensionHistoryResponse
}

export function PermissionHistory({ history }: PermissionHistoryProps) {
  const [expandedIndexes, setExpandedIndexes] = useState<Set<number>>(new Set())

  const toggleExpand = (index: number) => {
    setExpandedIndexes((prev) => {
      const next = new Set(prev)
      if (next.has(index)) {
        next.delete(index)
      } else {
        next.add(index)
      }
      return next
    })
  }

  if (history.total_snapshots === 0) {
    return (
      <div className={styles.container}>
        <div className={styles.emptyMessage}>No history available yet</div>
      </div>
    )
  }

  if (!history.has_permission_changes) {
    return (
      <div className={styles.container}>
        <div className={styles.noChangesMessage}>No permission changes detected</div>
      </div>
    )
  }

  return (
    <div className={styles.container}>
      <div className={styles.timeline}>
        {history.snapshots.map((snapshot, index) => {
          const isExpanded = expandedIndexes.has(index)
          const hasDiff = snapshot.diff !== null
          const hasChanges = hasDiff && snapshot.diff && (
            (snapshot.diff.added.length > 0) ||
            (snapshot.diff.removed.length > 0) ||
            snapshot.diff.version_changed ||
            snapshot.diff.name_changed
          )

          return (
            <div key={index} className={styles.timelineItem}>
              <div className={styles.timelineMarker}>
                <div className={`${styles.dot} ${hasChanges ? styles.dotChanged : styles.dotNormal}`} />
                {index < history.snapshots.length - 1 && <div className={styles.line} />}
              </div>

              <div className={styles.timelineContent}>
                <div
                  className={`${styles.snapshotCard} ${hasDiff ? styles.clickable : ''}`}
                  onClick={() => hasDiff && toggleExpand(index)}
                >
                  <div className={styles.snapshotHeader}>
                    <div className={styles.versionBadge}>v{snapshot.version}</div>
                    <div className={styles.timestamp}>
                      {new Date(snapshot.scraped_at).toLocaleString()}
                    </div>
                  </div>

                  <div className={styles.snapshotMeta}>
                    <span className={styles.permissionCount}>
                      {snapshot.permissions.length} permission{snapshot.permissions.length !== 1 ? 's' : ''}
                    </span>
                    {hasChanges && snapshot.diff && (
                      <span className={styles.changesIndicator}>
                        {snapshot.diff.added.length > 0 && (
                          <span className={styles.added}>+{snapshot.diff.added.length}</span>
                        )}
                        {snapshot.diff.removed.length > 0 && (
                          <span className={styles.removed}>-{snapshot.diff.removed.length}</span>
                        )}
                      </span>
                    )}
                  </div>

                  {hasDiff && isExpanded && snapshot.diff && <PermissionDiff diff={snapshot.diff} />}
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
