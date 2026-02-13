import styles from './Header.module.css'

export function Header() {
  return (
    <header className={styles.header}>
      <div className={styles.container}>
        <h1 className={styles.title}>Extension Intel</h1>
        <p className={styles.subtitle}>
          Browser Extension OSINT Tool
        </p>
      </div>
    </header>
  )
}
