import styles from './EnrichmentLinks.module.css'

interface EnrichmentLinksProps {
  extensionId: string
  store: string
}

interface EnrichmentLink {
  label: string
  url: string
  description: string
}

export function EnrichmentLinks({ extensionId, store }: EnrichmentLinksProps) {
  const links: EnrichmentLink[] = []
  const encodedId = encodeURIComponent(extensionId)

  // VirusTotal - available for all stores
  links.push({
    label: 'VirusTotal',
    url: `https://www.virustotal.com/gui/search/${encodedId}`,
    description: 'Security analysis',
  })

  // Chrome-specific links
  if (store === 'chrome') {
    links.push({
      label: 'Chrome-Stats',
      url: `https://chrome-stats.com/d/${encodedId}`,
      description: 'Statistics and history',
    })
  }

  // Firefox-specific links
  if (store === 'firefox') {
    links.push({
      label: 'Source Viewer',
      url: `https://addons.mozilla.org/en-US/firefox/addon/${encodedId}/versions/`,
      description: 'Extension versions and source code',
    })
    links.push({
      label: 'Reviews',
      url: `https://addons.mozilla.org/en-US/firefox/addon/${encodedId}/reviews/`,
      description: 'User reviews and ratings',
    })
  }

  // Safari-specific links
  if (store === 'safari') {
    links.push({
      label: 'App Store Page',
      url: `https://apps.apple.com/app/id${encodedId}`,
      description: 'View in the App Store',
    })
  }

  // Edge has no store-specific links beyond VirusTotal

  return (
    <div className={styles.container}>
      <div className={styles.heading}>OSINT Analysis Links</div>
      <div className={styles.linkList}>
        {links.map((link) => (
          <a
            key={link.label}
            href={link.url}
            target="_blank"
            rel="noopener noreferrer"
            className={styles.link}
            title={link.description}
          >
            {link.label}
          </a>
        ))}
      </div>
    </div>
  )
}
