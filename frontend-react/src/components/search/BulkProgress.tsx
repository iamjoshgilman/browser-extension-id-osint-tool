import styles from './BulkProgress.module.css'

interface BulkProgressProps {
  completed: number
  total: number
  pct: number
  status: string | null
  onCancel: () => void
}

export function BulkProgress({ completed, total, pct, status, onCancel }: BulkProgressProps) {
  const isRunning = status === 'pending' || status === 'running'

  const statusLabel =
    status === 'pending'
      ? 'Starting bulk search...'
      : status === 'running'
        ? `Searching... ${completed} of ${total} tasks`
        : status === 'completed'
          ? 'Bulk search completed'
          : status === 'cancelled'
            ? 'Bulk search cancelled'
            : status === 'failed'
              ? 'Bulk search failed'
              : 'Processing...'

  return (
    <div className={styles.container} data-testid="bulk-progress">
      <div className={styles.header}>
        <span className={styles.statusText}>{statusLabel}</span>
        {isRunning && (
          <button className={styles.cancelBtn} onClick={onCancel} data-testid="cancel-btn">
            Cancel
          </button>
        )}
      </div>
      <div className={styles.progressBar}>
        <div
          className={styles.progressFill}
          style={{ width: `${pct}%` }}
          data-testid="progress-fill"
        />
      </div>
      <div className={styles.details}>
        {completed} / {total} completed ({pct}%)
      </div>
    </div>
  )
}
