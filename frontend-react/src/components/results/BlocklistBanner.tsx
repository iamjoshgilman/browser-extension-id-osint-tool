import styles from './BlocklistBanner.module.css'

interface BlocklistMatch {
  source: string
  url: string
  name?: string
}

interface BlocklistBannerProps {
  matches: BlocklistMatch[]
}

export function BlocklistBanner({ matches }: BlocklistBannerProps) {
  if (!matches || matches.length === 0) return null

  return (
    <div className={styles.banner}>
      <span className={styles.icon}>&#x26D4;</span>
      <div className={styles.content}>
        <p className={styles.message}>
          <strong>WARNING:</strong> This extension appears on{' '}
          <strong>{matches.length}</strong> malicious extension blocklist
          {matches.length !== 1 ? 's' : ''}.
        </p>
        <div className={styles.sources}>
          {matches.map((match, i) => (
            <a
              key={i}
              href={match.url}
              target="_blank"
              rel="noopener noreferrer"
              className={styles.sourceLink}
            >
              {match.source}
            </a>
          ))}
        </div>
      </div>
    </div>
  )
}
