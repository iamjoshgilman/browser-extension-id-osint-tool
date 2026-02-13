import type { ExtensionData } from '../../types/extension'
import { formatUserCount, formatRating } from '../../utils/formatters'
import styles from './ResultMeta.module.css'

interface ResultMetaProps {
  extension: ExtensionData
}

export function ResultMeta({ extension }: ResultMetaProps) {
  return (
    <div className={styles.meta}>
      <span>
        <strong>Publisher:</strong>{' '}
        <span className={styles.publisher}>{extension.publisher || 'Unknown'}</span>
      </span>
      <span>
        <strong>Users:</strong> {formatUserCount(extension.user_count)}
      </span>
      <span>
        <strong>Rating:</strong> {extension.rating ? `${formatRating(extension.rating)}` : 'N/A'}
      </span>
      <span>
        <strong>Version:</strong> {extension.version || 'N/A'}
      </span>
    </div>
  )
}
