import styles from './SearchModeToggle.module.css'

export type SearchMode = 'single' | 'bulk'

interface SearchModeToggleProps {
  mode: SearchMode
  onChange: (mode: SearchMode) => void
}

export function SearchModeToggle({ mode, onChange }: SearchModeToggleProps) {
  return (
    <div className={styles.toggle}>
      <button
        className={`${styles.button} ${mode === 'single' ? styles.active : ''}`}
        onClick={() => onChange('single')}
      >
        Single Search
      </button>
      <button
        className={`${styles.button} ${mode === 'bulk' ? styles.active : ''}`}
        onClick={() => onChange('bulk')}
      >
        Bulk Search
      </button>
    </div>
  )
}
