import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { ResultCard } from '../results/ResultCard'
import type { ExtensionData } from '../../types/extension'

const firefoxExtension: ExtensionData = {
  extension_id: 'uBlock0@raymondhill.net',
  name: 'uBlock Origin',
  store_source: 'firefox',
  publisher: 'Raymond Hill',
  description: 'An efficient wide-spectrum content blocker.',
  version: '1.55.0',
  user_count: '7,000,000',
  category: 'security',
  rating: '4.8',
  rating_count: '14000',
  last_updated: '2024-01-01',
  store_url: 'https://addons.mozilla.org/en-US/firefox/addon/ublock-origin/',
  icon_url: '',
  homepage_url: '',
  privacy_policy_url: '',
  permissions: ['storage', 'tabs', '<all_urls>'],
  found: true,
  cached: false,
  scraped_at: null,
}

const chromeExtension: ExtensionData = {
  ...firefoxExtension,
  store_source: 'chrome',
  permissions: [],
}

describe('ResultCard', () => {
  it('renders extension name and metadata', () => {
    render(<ResultCard extension={firefoxExtension} />)
    expect(screen.getByText('uBlock Origin')).toBeInTheDocument()
    expect(screen.getByText('Raymond Hill')).toBeInTheDocument()
    expect(screen.getByText(/1\.55\.0/)).toBeInTheDocument()
  })

  it('shows store badge', () => {
    render(<ResultCard extension={firefoxExtension} />)
    expect(screen.getByText('FIREFOX')).toBeInTheDocument()
  })

  it('shows risk badge for Firefox extensions with permissions', () => {
    render(<ResultCard extension={firefoxExtension} />)
    // <all_urls> makes this critical
    expect(screen.getByText('Risk: critical')).toBeInTheDocument()
  })

  it('shows permissions unavailable notice for Chrome', () => {
    render(<ResultCard extension={chromeExtension} />)
    expect(screen.getByText(/Permissions unavailable from Chrome Web Store/)).toBeInTheDocument()
  })

  it('renders store link', () => {
    render(<ResultCard extension={firefoxExtension} />)
    const link = screen.getByText(/View in Store/)
    expect(link).toHaveAttribute('href', firefoxExtension.store_url)
    expect(link).toHaveAttribute('target', '_blank')
  })

  it('shows cached badge when cached', () => {
    render(<ResultCard extension={{ ...firefoxExtension, cached: true }} />)
    expect(screen.getByText('Cached')).toBeInTheDocument()
  })

  it('shows "Find in other stores" button', () => {
    render(<ResultCard extension={firefoxExtension} />)
    expect(screen.getByText('Find in other stores')).toBeInTheDocument()
  })

  it('shows delisted banner when extension is delisted', () => {
    const delistedExtension = {
      ...firefoxExtension,
      delisted: true,
      scraped_at: '2024-01-15T10:30:00Z',
    }
    render(<ResultCard extension={delistedExtension} />)

    expect(screen.getByText(/removed or delisted/i)).toBeInTheDocument()
    expect(screen.getByText(/January 15, 2024/)).toBeInTheDocument()
  })

  it('does not show delisted banner when extension is not delisted', () => {
    render(<ResultCard extension={firefoxExtension} />)
    expect(screen.queryByText(/removed or delisted/i)).not.toBeInTheDocument()
  })
})
