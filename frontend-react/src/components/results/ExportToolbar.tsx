import type { ExtensionData } from '../../types/extension'
import { useExport } from '../../hooks/useExport'
import styles from './ExportToolbar.module.css'

interface ExportToolbarProps {
  results: ExtensionData[]
  query: string
  stores: string[]
}

export function ExportToolbar({ results, query, stores }: ExportToolbarProps) {
  const { downloadCsv, downloadJson } = useExport()

  if (results.length === 0) return null

  return (
    <div className={styles.toolbar}>
      <button
        className={styles.btn}
        onClick={() => downloadCsv(results, query)}
      >
        Export CSV
      </button>
      <button
        className={styles.btn}
        onClick={() => downloadJson(results, query, stores)}
      >
        Export JSON
      </button>
    </div>
  )
}
