import { describe, it, expect, vi, beforeEach } from 'vitest'
import { exportCsv, exportJson } from '../export'
import type { ExtensionData } from '../../types/extension'

const mockExtension: ExtensionData = {
  extension_id: 'test123',
  name: 'Test Extension',
  store_source: 'firefox',
  publisher: 'Test Publisher',
  description: 'A test extension',
  version: '1.0.0',
  user_count: '1000',
  category: 'security',
  rating: '4.5',
  rating_count: '100',
  last_updated: '2024-01-01',
  store_url: 'https://addons.mozilla.org/test',
  icon_url: '',
  homepage_url: '',
  privacy_policy_url: '',
  permissions: ['tabs', 'storage'],
  found: true,
  cached: false,
  scraped_at: null,
}

describe('export utilities', () => {
  let createObjectURLMock: ReturnType<typeof vi.fn>
  let revokeObjectURLMock: ReturnType<typeof vi.fn>

  beforeEach(() => {
    createObjectURLMock = vi.fn(() => 'blob:mock-url')
    revokeObjectURLMock = vi.fn()
    global.URL.createObjectURL = createObjectURLMock
    global.URL.revokeObjectURL = revokeObjectURLMock

    // Mock DOM for download
    const clickMock = vi.fn()
    vi.spyOn(document, 'createElement').mockReturnValue({
      href: '',
      download: '',
      click: clickMock,
      style: {},
    } as unknown as HTMLElement)
    vi.spyOn(document.body, 'appendChild').mockImplementation(n => n)
    vi.spyOn(document.body, 'removeChild').mockImplementation(n => n)
  })

  it('exportCsv creates a blob with CSV content', () => {
    exportCsv([mockExtension], 'test-query')
    expect(createObjectURLMock).toHaveBeenCalled()
    const blob = createObjectURLMock.mock.calls[0][0] as Blob
    expect(blob.type).toBe('text/csv;charset=utf-8')
  })

  it('exportJson creates a blob with JSON content', () => {
    exportJson([mockExtension], 'test-query', ['firefox'])
    expect(createObjectURLMock).toHaveBeenCalled()
    const blob = createObjectURLMock.mock.calls[0][0] as Blob
    expect(blob.type).toBe('application/json')
  })
})
