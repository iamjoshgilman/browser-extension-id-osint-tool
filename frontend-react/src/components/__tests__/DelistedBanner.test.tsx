import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { DelistedBanner } from '../results/DelistedBanner'

describe('DelistedBanner', () => {
  it('renders with store name and date', () => {
    render(<DelistedBanner store="chrome" scrapedAt="2024-01-15T10:30:00Z" />)

    expect(screen.getByText(/removed or delisted/i)).toBeInTheDocument()
    expect(screen.getByText(/CHROME/)).toBeInTheDocument()
    expect(screen.getByText(/January 15, 2024/)).toBeInTheDocument()
  })

  it('renders with unknown date when scrapedAt is null', () => {
    render(<DelistedBanner store="firefox" scrapedAt={null} />)

    expect(screen.getByText(/removed or delisted/i)).toBeInTheDocument()
    expect(screen.getByText(/FIREFOX/)).toBeInTheDocument()
    expect(screen.getByText(/unknown date/)).toBeInTheDocument()
  })

  it('displays warning icon', () => {
    const { container } = render(<DelistedBanner store="edge" scrapedAt={null} />)

    expect(container.textContent).toContain('⚠')
  })
})
