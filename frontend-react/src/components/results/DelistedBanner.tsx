import styles from './DelistedBanner.module.css'

interface DelistedBannerProps {
  store: string
  scrapedAt: string | null
}

export function DelistedBanner({ store, scrapedAt }: DelistedBannerProps) {
  const formattedDate = scrapedAt
    ? new Date(scrapedAt).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
      })
    : 'unknown date'

  return (
    <div className={styles.banner}>
      <span className={styles.icon}>⚠</span>
      <p className={styles.message}>
        This extension has been removed or delisted from the{' '}
        <strong>{store.toUpperCase()}</strong> store. The data shown below was last cached on{' '}
        <strong>{formattedDate}</strong>.
      </p>
    </div>
  )
}
