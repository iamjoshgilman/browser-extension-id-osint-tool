import styles from './Header.module.css'

export function Header() {
  return (
    <header className={styles.header}>
      <div className={styles.container}>
        <h1 className={styles.title}>Browser Extension OSINT Tool</h1>
        <p className={styles.subtitle}>
          Search and analyze browser extensions across Chrome, Firefox, and Edge stores
        </p>
      </div>
    </header>
  )
}
