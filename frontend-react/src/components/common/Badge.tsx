import type { CSSProperties, ReactNode } from 'react'
import styles from './Badge.module.css'

interface BadgeProps {
  children: ReactNode
  color: string
  textColor?: string
  className?: string
}

export function Badge({ children, color, textColor = 'var(--ctp-crust)', className = '' }: BadgeProps) {
  const style: CSSProperties = {
    backgroundColor: color,
    color: textColor,
  }
  return (
    <span className={`${styles.badge} ${className}`} style={style}>
      {children}
    </span>
  )
}
