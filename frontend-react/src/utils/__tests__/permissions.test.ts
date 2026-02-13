import { describe, it, expect } from 'vitest'
import { classifyPermission, getAggregateRisk, classifyAllPermissions } from '../permissions'

describe('classifyPermission', () => {
  it('classifies critical permissions', () => {
    expect(classifyPermission('<all_urls>').risk).toBe('critical')
    expect(classifyPermission('http://*/*').risk).toBe('critical')
    expect(classifyPermission('nativeMessaging').risk).toBe('critical')
    expect(classifyPermission('debugger').risk).toBe('critical')
  })

  it('classifies high permissions', () => {
    expect(classifyPermission('tabs').risk).toBe('high')
    expect(classifyPermission('history').risk).toBe('high')
    expect(classifyPermission('cookies').risk).toBe('high')
    expect(classifyPermission('webRequest').risk).toBe('high')
  })

  it('classifies medium permissions', () => {
    expect(classifyPermission('storage').risk).toBe('medium')
    expect(classifyPermission('clipboardRead').risk).toBe('medium')
    expect(classifyPermission('notifications').risk).toBe('medium')
  })

  it('classifies low permissions', () => {
    expect(classifyPermission('activeTab').risk).toBe('low')
    expect(classifyPermission('bookmarks').risk).toBe('low')
    expect(classifyPermission('idle').risk).toBe('low')
  })

  it('classifies URL patterns as high', () => {
    expect(classifyPermission('https://specific-site.com/*').risk).toBe('high')
    expect(classifyPermission('http://example.com/*').risk).toBe('high')
  })

  it('classifies unknown permissions as medium', () => {
    expect(classifyPermission('someUnknownPermission').risk).toBe('medium')
  })

  it('provides descriptions', () => {
    const result = classifyPermission('tabs')
    expect(result.description).toBeTruthy()
    expect(result.name).toBe('tabs')
  })
})

describe('getAggregateRisk', () => {
  it('returns low for empty permissions', () => {
    expect(getAggregateRisk([])).toBe('low')
  })

  it('returns critical when critical permissions exist', () => {
    expect(getAggregateRisk(['activeTab', '<all_urls>'])).toBe('critical')
  })

  it('returns high when high permissions exist but no critical', () => {
    expect(getAggregateRisk(['activeTab', 'tabs', 'storage'])).toBe('high')
  })

  it('returns medium for only medium permissions', () => {
    expect(getAggregateRisk(['storage', 'notifications'])).toBe('medium')
  })

  it('returns low for only low permissions', () => {
    expect(getAggregateRisk(['activeTab', 'idle'])).toBe('low')
  })
})

describe('classifyAllPermissions', () => {
  it('sorts by risk level (critical first)', () => {
    const result = classifyAllPermissions(['idle', '<all_urls>', 'storage', 'tabs'])
    expect(result[0].risk).toBe('critical')
    expect(result[1].risk).toBe('high')
    expect(result[2].risk).toBe('medium')
    expect(result[3].risk).toBe('low')
  })
})
