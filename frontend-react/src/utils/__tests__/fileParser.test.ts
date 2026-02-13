import { describe, it, expect } from 'vitest'
import { parseFile } from '../fileParser'

describe('parseFile', () => {
  it('parses plain text with one ID per line', () => {
    const content = `cjpalhdlnbpafiamejdnhcphjbkeiagm
uBlock0@raymondhill.net
odfafepnkmbhccpbejgmiehpchacaeak`
    expect(parseFile(content)).toEqual([
      'cjpalhdlnbpafiamejdnhcphjbkeiagm',
      'uBlock0@raymondhill.net',
      'odfafepnkmbhccpbejgmiehpchacaeak',
    ])
  })

  it('handles empty input', () => {
    expect(parseFile('')).toEqual([])
    expect(parseFile('   \n  \n  ')).toEqual([])
  })

  it('parses CSV with header row', () => {
    const content = `extension_id,name,store
cjpalhdlnbpafiamejdnhcphjbkeiagm,uBlock Origin,chrome
uBlock0@raymondhill.net,uBlock Origin,firefox`
    expect(parseFile(content)).toEqual([
      'cjpalhdlnbpafiamejdnhcphjbkeiagm',
      'uBlock0@raymondhill.net',
    ])
  })

  it('parses CSV with "id" header', () => {
    const content = `id,description
abc123,some extension`
    expect(parseFile(content)).toEqual(['abc123'])
  })

  it('parses tab-delimited with header', () => {
    const content = `extension_id\tname\ncjpalhdlnbpafiamejdnhcphjbkeiagm\tuBlock`
    expect(parseFile(content)).toEqual(['cjpalhdlnbpafiamejdnhcphjbkeiagm'])
  })

  it('falls back to first column for delimited data without headers', () => {
    const content = `cjpalhdlnbpafiamejdnhcphjbkeiagm,uBlock Origin
odfafepnkmbhccpbejgmiehpchacaeak,Some Extension`
    expect(parseFile(content)).toEqual([
      'cjpalhdlnbpafiamejdnhcphjbkeiagm',
      'odfafepnkmbhccpbejgmiehpchacaeak',
    ])
  })

  it('strips whitespace and blank lines', () => {
    const content = `  cjpalhdlnbpafiamejdnhcphjbkeiagm

  odfafepnkmbhccpbejgmiehpchacaeak  `
    expect(parseFile(content)).toEqual([
      'cjpalhdlnbpafiamejdnhcphjbkeiagm',
      'odfafepnkmbhccpbejgmiehpchacaeak',
    ])
  })

  it('handles Windows-style line endings', () => {
    const content = "id1\r\nid2\r\nid3"
    expect(parseFile(content)).toEqual(['id1', 'id2', 'id3'])
  })
})
