import type { ExtensionData } from '../../types/extension'
import { formatUserCount, formatRating } from '../../utils/formatters'
import { sanitizeUrl } from '../../utils/sanitizeUrl'
import styles from './ResultMeta.module.css'

interface ResultMetaProps {
  extension: ExtensionData
}

interface MetaItem {
  label: string
  value: string
  isLink?: boolean
  href?: string
}

export function ResultMeta({ extension }: ResultMetaProps) {
  const items: MetaItem[] = []

  // Publisher / Developer
  const publisherDisplay = extension.publisher || 'Unknown'
  const safeDeveloperWebsite = sanitizeUrl(extension.developer_website)
  if (safeDeveloperWebsite) {
    items.push({
      label: 'Publisher',
      value: publisherDisplay,
      isLink: true,
      href: safeDeveloperWebsite,
    })
  } else {
    items.push({ label: 'Publisher', value: publisherDisplay })
  }

  // Version + last updated
  const versionStr = extension.version || 'N/A'
  const updatedStr = extension.last_updated
    ? ` (updated ${extension.last_updated})`
    : ''
  items.push({ label: 'Version', value: `${versionStr}${updatedStr}` })

  // User count
  items.push({ label: 'Users', value: formatUserCount(extension.user_count) })

  // Rating with count
  if (extension.rating) {
    const ratingStr = formatRating(extension.rating)
    const countStr = extension.rating_count ? ` (${extension.rating_count} ratings)` : ''
    items.push({ label: 'Rating', value: `${ratingStr}/5${countStr}` })
  } else {
    items.push({ label: 'Rating', value: 'N/A' })
  }

  // Category
  if (extension.category) {
    items.push({ label: 'Category', value: extension.category })
  }

  // Content rating (Safari)
  if (extension.content_rating) {
    items.push({ label: 'Content Rating', value: extension.content_rating })
  }

  // File size
  if (extension.file_size) {
    items.push({ label: 'File Size', value: extension.file_size })
  }

  // Release date
  if (extension.release_date) {
    items.push({ label: 'Release Date', value: extension.release_date })
  }

  // Price
  if (extension.price) {
    items.push({ label: 'Price', value: extension.price })
  }

  // Update frequency / trust signal
  if (extension.update_frequency) {
    items.push({ label: 'Trust Signal', value: extension.update_frequency })
  }

  // Languages
  if (extension.languages) {
    items.push({ label: 'Languages', value: extension.languages })
  }

  // Support URL
  const safeSupportUrl = sanitizeUrl(extension.support_url)
  if (safeSupportUrl) {
    items.push({
      label: 'Support',
      value: 'Support Page',
      isLink: true,
      href: safeSupportUrl,
    })
  }

  // Privacy policy
  const safePrivacyPolicyUrl = sanitizeUrl(extension.privacy_policy_url)
  if (safePrivacyPolicyUrl) {
    items.push({
      label: 'Privacy Policy',
      value: 'View Policy',
      isLink: true,
      href: safePrivacyPolicyUrl,
    })
  }

  return (
    <div className={styles.meta}>
      {items.map((item, i) => (
        <span key={i} className={styles.metaItem}>
          <strong>{item.label}:</strong>{' '}
          {item.isLink && item.href ? (
            <a
              href={item.href}
              target="_blank"
              rel="noopener noreferrer"
              className={styles.link}
            >
              {item.value}
            </a>
          ) : (
            <span className={item.label === 'Publisher' ? styles.publisher : undefined}>
              {item.value}
            </span>
          )}
        </span>
      ))}
    </div>
  )
}
