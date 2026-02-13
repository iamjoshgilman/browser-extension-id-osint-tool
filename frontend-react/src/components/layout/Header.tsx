import styles from './Header.module.css'
import { Logo } from './Logo'

export function Header() {
  return (
    <header className={styles.header}>
      <div className={styles.container}>
        <div className={styles.branding}>
          <Logo size={40} className={styles.logo} />
          <div className={styles.titleGroup}>
            <h1 className={styles.title}>
              <span className={styles.titleExtension}>Extension</span>
              {' '}
              <span className={styles.titleIntel}>Intel</span>
            </h1>
            <p className={styles.subtitle}>
              Browser Extension OSINT Tool
            </p>
          </div>
        </div>
      </div>
      <div className={styles.accentLine} />
    </header>
  )
}
