import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { BlocklistBanner } from '../results/BlocklistBanner'

describe('BlocklistBanner', () => {
  it('renders nothing when matches is empty', () => {
    const { container } = render(<BlocklistBanner matches={[]} />)
    expect(container.firstChild).toBeNull()
  })

  it('renders singular text for 1 match', () => {
    const matches = [{ source: 'TestList', url: 'https://example.com' }]
    render(<BlocklistBanner matches={matches} />)
    expect(screen.getByText(/1/)).toBeInTheDocument()
    expect(screen.getByText(/blocklist(?!s)/)).toBeInTheDocument()
  })

  it('renders plural text for multiple matches', () => {
    const matches = [
      { source: 'List A', url: 'https://a.com' },
      { source: 'List B', url: 'https://b.com' },
    ]
    render(<BlocklistBanner matches={matches} />)
    expect(screen.getByText(/2/)).toBeInTheDocument()
    expect(screen.getByText(/blocklists/)).toBeInTheDocument()
  })

  it('renders threat intel links with resource name from URL', () => {
    const matches = [
      { source: 'TestList', url: 'https://www.thehackernews.com/2026/02/article.html' },
    ]
    render(<BlocklistBanner matches={matches} />)

    const link = screen.getByRole('link', { name: /threat intel - thehackernews/i })
    expect(link).toHaveAttribute('href', 'https://www.thehackernews.com/2026/02/article.html')
    expect(link).toHaveAttribute('target', '_blank')
    expect(link).toHaveAttribute('rel', 'noopener noreferrer')
  })

  it('displays warning text', () => {
    const matches = [{ source: 'TestList', url: 'https://example.com' }]
    render(<BlocklistBanner matches={matches} />)
    expect(screen.getByText(/WARNING/)).toBeInTheDocument()
  })
})
