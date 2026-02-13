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

  it('renders ExtensionPedia link only for chrome store', () => {
    const extensionId = 'chromeextensionid123456789012'

    // Chrome should have ExtensionPedia
    const { rerender } = render(
      <EnrichmentLinks extensionId={extensionId} store="chrome" />
    )
    const epLink = screen.getByRole('link', { name: /extensionpedia/i })
    expect(epLink).toBeInTheDocument()
    expect(epLink).toHaveAttribute(
      'href',
      `https://layerxsecurity.com/extensions/?search=${extensionId}`
    )
    expect(epLink).toHaveAttribute('target', '_blank')
    expect(epLink).toHaveAttribute('rel', 'noopener noreferrer')

    // Firefox should NOT have ExtensionPedia
    rerender(<EnrichmentLinks extensionId={extensionId} store="firefox" />)
    expect(screen.queryByRole('link', { name: /extensionpedia/i })).not.toBeInTheDocument()

    // Edge should NOT have ExtensionPedia
    rerender(<EnrichmentLinks extensionId={extensionId} store="edge" />)
    expect(screen.queryByRole('link', { name: /extensionpedia/i })).not.toBeInTheDocument()

    // Safari should NOT have ExtensionPedia
    rerender(<EnrichmentLinks extensionId={extensionId} store="safari" />)
    expect(screen.queryByRole('link', { name: /extensionpedia/i })).not.toBeInTheDocument()
  })

  it('renders OTX AlienVault link for all stores', () => {
    const extensionId = 'test-extension-123'

    // Chrome should have OTX
    const { rerender } = render(
      <EnrichmentLinks extensionId={extensionId} store="chrome" />
    )
    let otxLink = screen.getByRole('link', { name: /otx alienvault/i })
    expect(otxLink).toBeInTheDocument()
    expect(otxLink).toHaveAttribute(
      'href',
      `https://otx.alienvault.com/browse/global/pulses?q=${extensionId}`
    )
    expect(otxLink).toHaveAttribute('target', '_blank')
    expect(otxLink).toHaveAttribute('rel', 'noopener noreferrer')

    // Firefox should have OTX
    rerender(<EnrichmentLinks extensionId={extensionId} store="firefox" />)
    otxLink = screen.getByRole('link', { name: /otx alienvault/i })
    expect(otxLink).toBeInTheDocument()
    expect(otxLink).toHaveAttribute(
      'href',
      `https://otx.alienvault.com/browse/global/pulses?q=${extensionId}`
    )

    // Edge should have OTX
    rerender(<EnrichmentLinks extensionId={extensionId} store="edge" />)
    otxLink = screen.getByRole('link', { name: /otx alienvault/i })
    expect(otxLink).toBeInTheDocument()
    expect(otxLink).toHaveAttribute(
      'href',
      `https://otx.alienvault.com/browse/global/pulses?q=${extensionId}`
    )

    // Safari should have OTX
    rerender(<EnrichmentLinks extensionId={extensionId} store="safari" />)
    otxLink = screen.getByRole('link', { name: /otx alienvault/i })
    expect(otxLink).toBeInTheDocument()
    expect(otxLink).toHaveAttribute(
      'href',
      `https://otx.alienvault.com/browse/global/pulses?q=${extensionId}`
    )
  })

  it('renders heading with correct text', () => {
    render(<EnrichmentLinks extensionId="test-id" store="chrome" />)

    expect(screen.getByText(/osint analysis links/i)).toBeInTheDocument()
  })

  it('renders correct number of links per store', () => {
    const extensionId = 'test-id'

    // Chrome: VirusTotal + Chrome-Stats + ExtensionPedia + OTX = 4 links
    const { rerender } = render(
      <EnrichmentLinks extensionId={extensionId} store="chrome" />
    )
    let allLinks = screen.getAllByRole('link')
    expect(allLinks).toHaveLength(4)

    // Firefox: VirusTotal + Source Viewer + Reviews + OTX = 4 links
    rerender(<EnrichmentLinks extensionId={extensionId} store="firefox" />)
    allLinks = screen.getAllByRole('link')
    expect(allLinks).toHaveLength(4)

    // Edge: VirusTotal + OTX = 2 links
    rerender(<EnrichmentLinks extensionId={extensionId} store="edge" />)
    allLinks = screen.getAllByRole('link')
    expect(allLinks).toHaveLength(2)

    // Safari: VirusTotal + App Store Page + OTX = 3 links
    rerender(<EnrichmentLinks extensionId={extensionId} store="safari" />)
    allLinks = screen.getAllByRole('link')
    expect(allLinks).toHaveLength(3)
  })
})
