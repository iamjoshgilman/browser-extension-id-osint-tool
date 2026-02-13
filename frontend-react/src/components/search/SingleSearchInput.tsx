import styles from './SingleSearchInput.module.css'

interface SingleSearchInputProps {
  value: string
  onChange: (value: string) => void
  onSubmit: () => void
  disabled: boolean
}

export function SingleSearchInput({ value, onChange, onSubmit, disabled }: SingleSearchInputProps) {
  return (
    <div>
      <div className={styles.inputGroup}>
        <input
          type="text"
          className={styles.input}
          value={value}
          onChange={e => onChange(e.target.value)}
          onKeyDown={e => { if (e.key === 'Enter' && !disabled) onSubmit() }}
          placeholder="Enter extension ID"
          disabled={disabled}
        />
      </div>
      <p className={styles.help}>Tip: Use the extension's ID, not its name</p>
    </div>
  )
}
