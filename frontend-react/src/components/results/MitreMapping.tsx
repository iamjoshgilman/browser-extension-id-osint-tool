import { useState } from 'react'
import { getMitreTechniquesForPermissions } from '../../data/mitreMapping'
import styles from './MitreMapping.module.css'

interface MitreMappingProps {
  permissions: string[]
}

export function MitreMapping({ permissions }: MitreMappingProps) {
  const [expanded, setExpanded] = useState(false)
  const techniques = getMitreTechniquesForPermissions(permissions)

  if (techniques.length === 0) {
    return null
  }

  return (
    <div className={styles.container}>
      <button className={styles.toggleBtn} onClick={() => setExpanded(!expanded)}>
        MITRE ATT&amp;CK Techniques ({techniques.length})
        <span className={`${styles.arrow} ${expanded ? styles.arrowUp : ''}`}>&#9660;</span>
      </button>

      {expanded && (
        <div className={styles.list}>
          {techniques.map((t) => (
            <div key={t.id} className={styles.item}>
              <a
                href={t.url}
                target="_blank"
                rel="noopener noreferrer"
                className={styles.techniqueId}
              >
                {t.id}
              </a>
              <span className={styles.techniqueName}>{t.name}</span>
              <span className={styles.tacticBadge}>{t.tactic}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
