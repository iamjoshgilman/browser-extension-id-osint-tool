import { describe, it, expect } from 'vitest'
import { calculateRiskVerdict } from '../riskVerdict'
import type { ExtensionData } from '../../types/extension'

const baseExtension: ExtensionData = {
  extension_id: 'test123',
  name: 'Test Extension',
  store_source: 'chrome',
  publisher: 'Test Publisher',
  description: 'Test',
  version: '1.0',
  user_count: '10000',
  category: 'tools',
  rating: '4.5',
  rating_count: '100',
  last_updated: '2025-01-01',
  store_url: 'https://example.com',
  icon_url: '',
  homepage_url: '',
  privacy_policy_url: '',
  permissions: [],
  found: true,
  cached: false,
  scraped_at: null,
}

describe('calculateRiskVerdict', () => {
  it('returns null level for safe extension', () => {
    const verdict = calculateRiskVerdict(baseExtension)
    expect(verdict.level).toBeNull()
    expect(verdict.signals).toHaveLength(0)
  })

  it('returns critical for blocklisted extension', () => {
    const ext = {
      ...baseExtension,
      blocklist_matches: [{ source: 'TestList', url: 'https://example.com' }],
    }
    const verdict = calculateRiskVerdict(ext)
    expect(verdict.level).toBe('critical')
    expect(verdict.message).toBe('CRITICAL RISK')
    expect(verdict.signals.some(s => s.label === 'On malicious blocklist')).toBe(true)
  })

  it('returns critical for critical permissions', () => {
    const ext = { ...baseExtension, permissions: ['<all_urls>', 'cookies'] }
    const verdict = calculateRiskVerdict(ext)
    expect(verdict.level).toBe('critical')
    expect(verdict.signals.some(s => s.label === 'Critical permissions')).toBe(true)
  })

  it('returns high for delisted extension', () => {
    const ext = { ...baseExtension, delisted: true }
    const verdict = calculateRiskVerdict(ext)
    expect(verdict.level).toBe('high')
    expect(verdict.signals.some(s => s.label === 'Delisted from store')).toBe(true)
  })

  it('returns high for high-risk permissions', () => {
    const ext = { ...baseExtension, permissions: ['tabs', 'history'] }
    const verdict = calculateRiskVerdict(ext)
    expect(verdict.level).toBe('high')
    expect(verdict.signals.some(s => s.label === 'High-risk permissions')).toBe(true)
  })

  it('detects low users + critical perms signal', () => {
    const ext = {
      ...baseExtension,
      user_count: '500',
      permissions: ['<all_urls>'],
    }
    const verdict = calculateRiskVerdict(ext)
    expect(verdict.signals.some(s => s.label === 'Low users + critical perms')).toBe(true)
  })

  it('detects stale extension signal', () => {
    const ext = { ...baseExtension, last_updated: '2020-01-01' }
    const verdict = calculateRiskVerdict(ext)
    expect(verdict.level).toBe('low')
    expect(verdict.signals.some(s => s.label === 'Not updated in 2+ years')).toBe(true)
  })

  it('aggregates multiple signals with highest severity', () => {
    const ext = {
      ...baseExtension,
      delisted: true,
      permissions: ['<all_urls>'],
      blocklist_matches: [{ source: 'List', url: 'https://example.com' }],
      last_updated: '2020-01-01',
      user_count: '100',
    }
    const verdict = calculateRiskVerdict(ext)
    expect(verdict.level).toBe('critical')
    expect(verdict.signals.length).toBeGreaterThanOrEqual(3)
  })
})
