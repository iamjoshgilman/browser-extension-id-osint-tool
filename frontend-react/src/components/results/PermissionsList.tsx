import { useState } from 'react'
import { classifyAllPermissions, getPermissionDescription } from '../../utils/permissions'
import { PermissionBadge } from './PermissionBadge'
import styles from './PermissionsList.module.css'

interface PermissionsListProps {
  permissions: string[]
}

export function PermissionsList({ permissions }: PermissionsListProps) {
  const [expanded, setExpanded] = useState(false)

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
            <div key={i} className={styles.item} title={getPermissionDescription(p.name)}>
              <PermissionBadge risk={p.risk} />
              <code className={styles.name}>{p.name}</code>
              <span className={styles.desc}>{getPermissionDescription(p.name)}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
