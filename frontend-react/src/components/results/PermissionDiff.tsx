import type { PermissionDiff as PermissionDiffType } from '../../types/extension'
import { classifyPermission } from '../../utils/permissions'
import styles from './PermissionDiff.module.css'

interface PermissionDiffProps {
  diff: PermissionDiffType
}

export function PermissionDiff({ diff }: PermissionDiffProps) {
  return (
    <div className={styles.diffContainer}>
      {diff.version_changed && (
        <div className={styles.versionChange}>
          <span className={styles.label}>Version:</span>
          <span className={styles.versionText}>
            {diff.previous_version} &rarr; {diff.version_changed ? 'new version' : ''}
          </span>
        </div>
      )}

      {diff.name_changed && diff.previous_name && (
        <div className={styles.nameChange}>
          <span className={styles.label}>Name changed:</span>
          <span className={styles.nameText}>{diff.previous_name}</span>
        </div>
      )}

      {diff.added.length > 0 && (
        <div className={styles.section}>
          <div className={styles.sectionTitle}>Added permissions:</div>
          <div className={styles.permissionList}>
            {diff.added.map((permission, idx) => {
              const info = classifyPermission(permission)
              return (
                <div key={`added-${idx}`} className={styles.permissionItem}>
                  <span className={styles.addedPrefix}>+</span>
                  <span className={`${styles.permissionName} ${styles[info.risk]}`}>
                    {permission}
                  </span>
                </div>
              )
            })}
          </div>
        </div>
      )}

      {diff.removed.length > 0 && (
        <div className={styles.section}>
          <div className={styles.sectionTitle}>Removed permissions:</div>
          <div className={styles.permissionList}>
            {diff.removed.map((permission, idx) => {
              const info = classifyPermission(permission)
              return (
                <div key={`removed-${idx}`} className={styles.permissionItem}>
                  <span className={styles.removedPrefix}>-</span>
                  <span className={`${styles.permissionName} ${styles[info.risk]}`}>
                    {permission}
                  </span>
                </div>
              )
            })}
          </div>
        </div>
      )}

      {diff.added.length === 0 && diff.removed.length === 0 && (
        <div className={styles.noPermissionChanges}>No permission changes</div>
      )}
    </div>
  )
}
