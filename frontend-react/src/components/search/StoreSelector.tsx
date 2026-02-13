import styles from './StoreSelector.module.css'

const STORES = [
  { id: 'chrome', label: 'Chrome Web Store' },
  { id: 'firefox', label: 'Firefox Add-ons' },
  { id: 'edge', label: 'Edge Add-ons' },
]

interface StoreSelectorProps {
  selected: string[]
  onChange: (stores: string[]) => void
}

export function StoreSelector({ selected, onChange }: StoreSelectorProps) {
  const toggle = (storeId: string) => {
    if (selected.includes(storeId)) {
      onChange(selected.filter(s => s !== storeId))
    } else {
      onChange([...selected, storeId])
    }
  }

  return (
    <div className={styles.selector}>
      {STORES.map(store => (
        <label key={store.id} className={styles.checkbox}>
          <input
            type="checkbox"
            checked={selected.includes(store.id)}
            onChange={() => toggle(store.id)}
          />
          <span>{store.label}</span>
        </label>
      ))}
    </div>
  )
}
