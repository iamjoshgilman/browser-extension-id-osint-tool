import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { EnrichmentLinks } from '../results/EnrichmentLinks'

describe('EnrichmentLinks', () => {
  it('renders VirusTotal link for all stores', () => {
    const extensionId = 'test-extension-123'

    // Test Chrome
    const { rerender } = render(
      <EnrichmentLinks extensionId={extensionId} store="chrome" />
    )
    let vtLink = screen.getByRole('link', { name: /virustotal/i })
    expect(vtLink).toBeInTheDocument()
    expect(vtLink).toHaveAttribute(
      'href',
      `https://www.virustotal.com/gui/search/${extensionId}`
    )
    expect(vtLink).toHaveAttribute('target', '_blank')
    expect(vtLink).toHaveAttribute('rel', 'noopener noreferrer')

    // Test Firefox
    rerender(<EnrichmentLinks extensionId={extensionId} store="firefox" />)
    vtLink = screen.getByRole('link', { name: /virustotal/i })
    expect(vtLink).toBeInTheDocument()
    expect(vtLink).toHaveAttribute(
      'href',
      `https://www.virustotal.com/gui/search/${extensionId}`
    )

    // Test Edge
    rerender(<EnrichmentLinks extensionId={extensionId} store="edge" />)
    vtLink = screen.getByRole('link', { name: /virustotal/i })
    expect(vtLink).toBeInTheDocument()
    expect(vtLink).toHaveAttribute(
      'href',
      `https://www.virustotal.com/gui/search/${extensionId}`
    )
  })

  it('renders Chrome-Stats link only for chrome store', () => {
    const extensionId = 'chromeextensionid123456789012'

    // Chrome should have Chrome-Stats link
    const { rerender } = render(
      <EnrichmentLinks extensionId={extensionId} store="chrome" />
    )
    const chromeStatsLink = screen.getByRole('link', { name: /chrome-stats/i })
    expect(chromeStatsLink).toBeInTheDocument()
    expect(chromeStatsLink).toHaveAttribute(
      'href',
      `https://chrome-stats.com/d/${extensionId}`
    )
    expect(chromeStatsLink).toHaveAttribute('target', '_blank')
    expect(chromeStatsLink).toHaveAttribute('rel', 'noopener noreferrer')

    // Firefox should NOT have Chrome-Stats link
    rerender(<EnrichmentLinks extensionId={extensionId} store="firefox" />)
    expect(screen.queryByRole('link', { name: /chrome-stats/i })).not.toBeInTheDocument()

    // Edge should NOT have Chrome-Stats link
    rerender(<EnrichmentLinks extensionId={extensionId} store="edge" />)
    expect(screen.queryByRole('link', { name: /chrome-stats/i })).not.toBeInTheDocument()
  })

  it('renders Firefox-specific links only for firefox store', () => {
    const extensionId = 'some-firefox-addon'

    // Firefox should have Source Viewer and Reviews links
    const { rerender } = render(
      <EnrichmentLinks extensionId={extensionId} store="firefox" />
    )

    const sourceLink = screen.getByRole('link', { name: /source viewer/i })
    expect(sourceLink).toBeInTheDocument()
    expect(sourceLink).toHaveAttribute(
      'href',
      `https://addons.mozilla.org/en-US/firefox/addon/${extensionId}/versions/`
    )
    expect(sourceLink).toHaveAttribute('target', '_blank')
    expect(sourceLink).toHaveAttribute('rel', 'noopener noreferrer')

    const reviewsLink = screen.getByRole('link', { name: /reviews/i })
    expect(reviewsLink).toBeInTheDocument()
    expect(reviewsLink).toHaveAttribute(
      'href',
      `https://addons.mozilla.org/en-US/firefox/addon/${extensionId}/reviews/`
    )
    expect(reviewsLink).toHaveAttribute('target', '_blank')
    expect(reviewsLink).toHaveAttribute('rel', 'noopener noreferrer')

    // Chrome should NOT have these links
    rerender(<EnrichmentLinks extensionId={extensionId} store="chrome" />)
    expect(screen.queryByRole('link', { name: /source viewer/i })).not.toBeInTheDocument()
    expect(screen.queryByRole('link', { name: /reviews/i })).not.toBeInTheDocument()

    // Edge should NOT have these links
    rerender(<EnrichmentLinks extensionId={extensionId} store="edge" />)
    expect(screen.queryByRole('link', { name: /source viewer/i })).not.toBeInTheDocument()
    expect(screen.queryByRole('link', { name: /reviews/i })).not.toBeInTheDocument()
  })

  it('renders only VirusTotal for edge store', () => {
    const extensionId = 'edgeextension12345'

    render(<EnrichmentLinks extensionId={extensionId} store="edge" />)

    // Should have VirusTotal
    const vtLink = screen.getByRole('link', { name: /virustotal/i })
    expect(vtLink).toBeInTheDocument()

    // Should NOT have Chrome-Stats
    expect(screen.queryByRole('link', { name: /chrome-stats/i })).not.toBeInTheDocument()

    // Should NOT have Firefox links
    expect(screen.queryByRole('link', { name: /source viewer/i })).not.toBeInTheDocument()
    expect(screen.queryByRole('link', { name: /reviews/i })).not.toBeInTheDocument()

    // Should only have 1 link total
    const allLinks = screen.getAllByRole('link')
    expect(allLinks).toHaveLength(1)
  })

  it('renders heading with correct text', () => {
    render(<EnrichmentLinks extensionId="test-id" store="chrome" />)

    expect(screen.getByText(/osint analysis links/i)).toBeInTheDocument()
  })

  it('renders correct number of links per store', () => {
    const extensionId = 'test-id'

    // Chrome: VirusTotal + Chrome-Stats = 2 links
    const { rerender } = render(
      <EnrichmentLinks extensionId={extensionId} store="chrome" />
    )
    let allLinks = screen.getAllByRole('link')
    expect(allLinks).toHaveLength(2)

    // Firefox: VirusTotal + Source Viewer + Reviews = 3 links
    rerender(<EnrichmentLinks extensionId={extensionId} store="firefox" />)
    allLinks = screen.getAllByRole('link')
    expect(allLinks).toHaveLength(3)

    // Edge: VirusTotal only = 1 link
    rerender(<EnrichmentLinks extensionId={extensionId} store="edge" />)
    allLinks = screen.getAllByRole('link')
    expect(allLinks).toHaveLength(1)
  })
})
