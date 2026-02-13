import styles from './Footer.module.css'

export function Footer() {
  const currentYear = new Date().getFullYear()
  const version = '1.0.0'

  return (
    <footer className={styles.footer}>
      <div className={styles.container}>
        <div className={styles.brand}>
          <span className={styles.name}>Extension Intel</span>
          <span className={styles.copyright}>© {currentYear}</span>
        </div>
        <div className={styles.meta}>
          <span className={styles.version}>v{version}</span>
          <span className={styles.divider}>•</span>
          <span className={styles.tagline}>Search responsibly</span>
        </div>
      </div>
    </footer>
  )
}
