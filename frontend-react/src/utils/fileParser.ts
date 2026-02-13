/**
 * Parse uploaded files (CSV or plain text) to extract extension IDs.
 * Auto-detects: one-ID-per-line text, CSV with headers, various delimiters.
 */
export function parseFile(content: string): string[] {
  const lines = content.trim().split(/\r?\n/).filter(l => l.trim())
  if (lines.length === 0) return []

  // Try CSV with header row
  const firstLine = lines[0].toLowerCase()
  const idColumnNames = ['extension_id', 'extensionid', 'id', 'ext_id', 'extid']
  const delimiters = [',', '\t', '|', ';']

  for (const delim of delimiters) {
    const headers = firstLine.split(delim).map(h => h.trim().replace(/^"|"$/g, ''))
    const idIndex = headers.findIndex(h => idColumnNames.includes(h))

    if (idIndex !== -1) {
      // CSV with recognized header
      return lines.slice(1)
        .map(line => {
          const cols = parseCsvLine(line, delim)
          return cols[idIndex]?.trim().replace(/^"|"$/g, '') || ''
        })
        .filter(id => id.length > 0)
    }
  }

  // No header detected: try first column of delimited data
  for (const delim of delimiters) {
    if (lines[0].includes(delim)) {
      return lines
        .map(line => {
          const cols = parseCsvLine(line, delim)
          return cols[0]?.trim().replace(/^"|"$/g, '') || ''
        })
        .filter(id => id.length > 0)
    }
  }

  // Plain text: one ID per line
  return lines.map(l => l.trim()).filter(l => l.length > 0)
}

function parseCsvLine(line: string, delim: string): string[] {
  const result: string[] = []
  let current = ''
  let inQuotes = false

  for (let i = 0; i < line.length; i++) {
    const ch = line[i]
    if (inQuotes) {
      if (ch === '"' && line[i + 1] === '"') {
        current += '"'
        i++
      } else if (ch === '"') {
        inQuotes = false
      } else {
        current += ch
      }
    } else {
      if (ch === '"') {
        inQuotes = true
      } else if (ch === delim) {
        result.push(current)
        current = ''
      } else {
        current += ch
      }
    }
  }
  result.push(current)
  return result
}
