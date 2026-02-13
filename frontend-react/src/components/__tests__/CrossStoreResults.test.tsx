import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { CrossStoreResults } from '../results/CrossStoreResults'
import type { ExtensionData } from '../../types/extension'

const mockExtension: ExtensionData = {
  extension_id: 'test-id',
  name: 'Test Extension',
  store_source: 'firefox',
  publisher: 'Test Publisher',
  description: 'Test description',
  version: '1.0.0',
  user_count: '1,000',
  category: 'productivity',
  rating: '4.5',
  rating_count: '100',
  last_updated: '2024-01-01',
  store_url: 'https://example.com',
  icon_url: '',
  homepage_url: '',
  privacy_policy_url: '',
  permissions: [],
  found: true,
  cached: false,
  scraped_at: null,
}

describe('CrossStoreResults', () => {
  it('shows loading state', () => {
    render(<CrossStoreResults results={[]} searchUrls={{}} loading={true} error={null} />)

    expect(screen.getByText(/Searching other stores/i)).toBeInTheDocument()
  })

  it('shows error state', () => {
    render(
      <CrossStoreResults results={[]} searchUrls={{}} loading={false} error="Test error" />
    )

    expect(screen.getByText('Test error')).toBeInTheDocument()
  })

  it('shows no results message when empty', () => {
    render(<CrossStoreResults results={[]} searchUrls={{}} loading={false} error={null} />)

    expect(screen.getByText(/No matching extensions found/i)).toBeInTheDocument()
  })

  it('renders extension results', () => {
    render(
      <CrossStoreResults
        results={[mockExtension]}
        searchUrls={{}}
        loading={false}
        error={null}
      />
    )

    expect(screen.getByText('Test Extension')).toBeInTheDocument()
    expect(screen.getByText('Test Publisher')).toBeInTheDocument()
    expect(screen.getByText('1,000 users')).toBeInTheDocument()
    expect(screen.getByText('FIREFOX')).toBeInTheDocument()
  })

  it('renders search URLs', () => {
    const searchUrls = {
      chrome: 'https://chrome.google.com/search?q=test',
      edge: 'https://microsoftedge.microsoft.com/search?q=test',
    }

    render(<CrossStoreResults results={[]} searchUrls={searchUrls} loading={false} error={null} />)

    expect(screen.getByText(/Manual search links/i)).toBeInTheDocument()
    expect(screen.getByText(/Search on CHROME/i)).toBeInTheDocument()
    expect(screen.getByText(/Search on EDGE/i)).toBeInTheDocument()
  })

  it('renders both results and search URLs', () => {
    const searchUrls = { chrome: 'https://chrome.google.com/search?q=test' }

    render(
      <CrossStoreResults
        results={[mockExtension]}
        searchUrls={searchUrls}
        loading={false}
        error={null}
      />
    )

    expect(screen.getByText('Test Extension')).toBeInTheDocument()
    expect(screen.getByText(/Manual search links/i)).toBeInTheDocument()
  })
})
