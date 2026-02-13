import { useState } from 'react'
import { classifyAllPermissions } from '../../utils/permissions'
import { PermissionBadge } from './PermissionBadge'
import styles from './PermissionsList.module.css'

interface PermissionsListProps {
  permissions: string[]
  store: string
}

export function PermissionsList({ permissions, store }: PermissionsListProps) {
  const [expanded, setExpanded] = useState(false)

  if (store === 'chrome') {
    return (
      <div className={styles.unavailable}>
        <span className={styles.icon}>!</span>
        Permissions unavailable from Chrome Web Store.{' '}
        {/* CRXcavator link removed - service discontinued */}
      </div>
    )
  }

  if (!permissions || permissions.length === 0) {
    return (
      <div className={styles.none}>No permissions declared</div>
    )
  }

  const classified = classifyAllPermissions(permissions)

  return (
    <div className={styles.container}>
      <button
        className={styles.toggleBtn}
        onClick={() => setExpanded(!expanded)}
      >
        {expanded ? 'Hide' : 'Show'} {permissions.length} permission{permissions.length !== 1 ? 's' : ''}
        <span className={`${styles.arrow} ${expanded ? styles.arrowUp : ''}`}>&#9660;</span>
      </button>

      {expanded && (
        <div className={styles.list}>
          {classified.map((p, i) => (
            <div key={i} className={styles.item}>
              <PermissionBadge risk={p.risk} />
              <code className={styles.name}>{p.name}</code>
              <span className={styles.desc}>{p.description}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
