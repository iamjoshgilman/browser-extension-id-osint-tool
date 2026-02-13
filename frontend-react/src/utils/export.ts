import type { ExtensionData } from '../types/extension'
import { getAggregateRisk, riskLabels } from './permissions'

function escapeCsvField(value: string): string {
  let escaped = value
  // Prevent CSV formula injection
  if (/^[=+\-@\t\r]/.test(escaped)) {
    escaped = "'" + escaped
  }
  if (escaped.includes(',') || escaped.includes('"') || escaped.includes('\n')) {
    return `"${escaped.replace(/"/g, '""')}"`
  }
  return escaped
}

export function exportCsv(results: ExtensionData[], query: string): void {
  const BOM = '\uFEFF'
  const headers = [
    'extension_id', 'name', 'store', 'publisher', 'version',
    'user_count', 'rating', 'permissions', 'risk_level',
    'store_url', 'description',
  ]

  const rows = results.map(ext => [
    ext.extension_id,
    ext.name,
    ext.store_source,
    ext.publisher || '',
    ext.version || '',
    ext.user_count || '',
    ext.rating || '',
    (ext.permissions || []).join(';'),
    riskLabels[getAggregateRisk(ext.permissions || [])],
    ext.store_url || '',
    (ext.description || '').replace(/\n/g, ' '),
  ])

  const csv = [
    headers.map(escapeCsvField).join(','),
    ...rows.map(row => row.map(escapeCsvField).join(',')),
  ].join('\r\n')

  downloadBlob(BOM + csv, `extensions-${query || 'export'}-${dateStamp()}.csv`, 'text/csv;charset=utf-8')
}

export function exportJson(results: ExtensionData[], query: string, stores: string[]): void {
  const data = {
    metadata: {
      tool: 'Browser Extension OSINT Tool',
      exported_at: new Date().toISOString(),
      query,
      stores_searched: stores,
    },
    results: results.map(ext => ({
      ...ext,
      permission_analysis: {
        risk_level: getAggregateRisk(ext.permissions || []),
        permission_count: (ext.permissions || []).length,
      },
    })),
  }

  const json = JSON.stringify(data, null, 2)
  downloadBlob(json, `extensions-${query || 'export'}-${dateStamp()}.json`, 'application/json')
}

function downloadBlob(content: string, filename: string, type: string): void {
  const blob = new Blob([content], { type })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename.replace(/[^a-zA-Z0-9._-]/g, '_')
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

function dateStamp(): string {
  return new Date().toISOString().slice(0, 10)
}
