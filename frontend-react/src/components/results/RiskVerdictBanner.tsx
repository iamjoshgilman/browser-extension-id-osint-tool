import type { RiskVerdict, VerdictLevel } from '../../utils/riskVerdict'
import styles from './RiskVerdictBanner.module.css'

interface RiskVerdictBannerProps {
  verdict: RiskVerdict
}

const levelIcons: Record<VerdictLevel, string> = {
  critical: '\u26D4',  // no entry
  high: '\u26A0',      // warning
  medium: '\u26A0',    // warning
  low: '\u2139',       // info
}

export function RiskVerdictBanner({ verdict }: RiskVerdictBannerProps) {
  if (!verdict.level || verdict.signals.length === 0) return null

  return (
    <div className={`${styles.banner} ${styles[verdict.level]}`}>
      <div className={styles.header}>
        <span className={styles.icon}>{levelIcons[verdict.level]}</span>
        <span className={styles.message}>{verdict.message}</span>
      </div>
      <div className={styles.signals}>
        {verdict.signals.map((signal, i) => (
          <span key={i} className={`${styles.signal} ${styles[`signal_${signal.severity}`]}`}>
            {signal.label}
          </span>
        ))}
      </div>
    </div>
  )
}
