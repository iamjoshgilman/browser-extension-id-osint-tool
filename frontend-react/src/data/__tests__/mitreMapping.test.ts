import { describe, it, expect } from 'vitest'
import { getMitreTechniquesForPermissions } from '../mitreMapping'

describe('getMitreTechniquesForPermissions', () => {
  it('returns empty array for no permissions', () => {
    expect(getMitreTechniquesForPermissions([])).toEqual([])
  })

  it('returns empty array for permissions with no MITRE mapping', () => {
    expect(getMitreTechniquesForPermissions(['activeTab', 'storage'])).toEqual([])
  })

  it('maps cookies to T1539', () => {
    const result = getMitreTechniquesForPermissions(['cookies'])
    expect(result).toHaveLength(1)
    expect(result[0].id).toBe('T1539')
    expect(result[0].tactic).toBe('Credential Access')
  })

  it('maps <all_urls> to T1185', () => {
    const result = getMitreTechniquesForPermissions(['<all_urls>'])
    expect(result).toHaveLength(1)
    expect(result[0].id).toBe('T1185')
  })

  it('deduplicates techniques when multiple permissions map to same technique', () => {
    // Both tabs and <all_urls> map to T1185
    const result = getMitreTechniquesForPermissions(['tabs', '<all_urls>'])
    const t1185 = result.filter((t) => t.id === 'T1185')
    expect(t1185).toHaveLength(1)
  })

  it('returns multiple techniques for multiple mapped permissions', () => {
    const result = getMitreTechniquesForPermissions(['cookies', 'history', 'downloads'])
    expect(result.length).toBe(3)
    const ids = result.map((t) => t.id)
    expect(ids).toContain('T1539')
    expect(ids).toContain('T1217')
    expect(ids).toContain('T1105')
  })

  it('each technique has required fields', () => {
    const result = getMitreTechniquesForPermissions(['cookies'])
    const technique = result[0]
    expect(technique.id).toBeTruthy()
    expect(technique.name).toBeTruthy()
    expect(technique.tactic).toBeTruthy()
    expect(technique.url).toContain('attack.mitre.org')
    expect(technique.description).toBeTruthy()
  })
})
