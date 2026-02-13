import type { ExtensionData } from '../types/extension'
import { getAggregateRisk } from './permissions'

export type VerdictLevel = 'critical' | 'high' | 'medium' | 'low'

export interface RiskSignal {
  severity: VerdictLevel
  label: string
}

export interface RiskVerdict {
  level: VerdictLevel | null
  message: string
  signals: RiskSignal[]
}

function parseUserCount(userCount: string): number {
  if (!userCount) return 0
  // Remove commas and parse
  const cleaned = userCount.replace(/[^0-9]/g, '')
  return parseInt(cleaned, 10) || 0
}

function isStale(lastUpdated: string): boolean {
  if (!lastUpdated) return false
  const updated = new Date(lastUpdated)
  if (isNaN(updated.getTime())) return false
  const twoYearsAgo = new Date()
  twoYearsAgo.setFullYear(twoYearsAgo.getFullYear() - 2)
  return updated < twoYearsAgo
}

export function calculateRiskVerdict(extension: ExtensionData): RiskVerdict {
  const signals: RiskSignal[] = []

  // Signal: Blocklist match (Critical)
  if (extension.blocklist_matches && extension.blocklist_matches.length > 0) {
    signals.push({ severity: 'critical', label: 'On malicious blocklist' })
  }

  // Signal: Critical permissions (Critical)
  const permRisk = extension.permissions?.length > 0
    ? getAggregateRisk(extension.permissions)
    : null
  if (permRisk === 'critical') {
    signals.push({ severity: 'critical', label: 'Critical permissions' })
  }

  // Signal: Delisted from store (High)
  if (extension.delisted) {
    signals.push({ severity: 'high', label: 'Delisted from store' })
  }

  // Signal: High permissions (High)
  if (permRisk === 'high') {
    signals.push({ severity: 'high', label: 'High-risk permissions' })
  }

  // Signal: Low users + critical perms (Medium)
  const userCount = parseUserCount(extension.user_count)
  if (userCount > 0 && userCount < 1000 && permRisk === 'critical') {
    signals.push({ severity: 'medium', label: 'Low users + critical perms' })
  }

  // Signal: Stale extension (Low)
  if (isStale(extension.last_updated)) {
    signals.push({ severity: 'low', label: 'Not updated in 2+ years' })
  }

  // Determine overall level (highest severity)
  if (signals.length === 0) {
    return { level: null, message: '', signals: [] }
  }

  const severityOrder: VerdictLevel[] = ['critical', 'high', 'medium', 'low']
  let level: VerdictLevel = 'low'
  for (const s of severityOrder) {
    if (signals.some(sig => sig.severity === s)) {
      level = s
      break
    }
  }

  const messages: Record<VerdictLevel, string> = {
    critical: 'CRITICAL RISK',
    high: 'HIGH RISK',
    medium: 'MODERATE RISK',
    low: 'Low Risk',
  }

  return { level, message: messages[level], signals }
}
