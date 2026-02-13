import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { SearchPanel } from '../search/SearchPanel'

describe('SearchPanel', () => {
  const defaultProps = {
    onSingleSearch: vi.fn(),
    onBulkSearch: vi.fn(),
    loading: false,
  }

  it('renders single search mode by default', () => {
    render(<SearchPanel {...defaultProps} />)
    expect(screen.getByPlaceholderText('Enter extension ID')).toBeInTheDocument()
    expect(screen.getByText('Search Extension')).toBeInTheDocument()
  })

  it('switches to bulk search mode', () => {
    render(<SearchPanel {...defaultProps} />)
    fireEvent.click(screen.getByText('Bulk Search'))
    expect(screen.getByPlaceholderText(/Enter extension IDs/)).toBeInTheDocument()
    expect(screen.getByText('Search Extensions')).toBeInTheDocument()
  })

  it('shows all three store checkboxes', () => {
    render(<SearchPanel {...defaultProps} />)
    expect(screen.getByText('Chrome Web Store')).toBeInTheDocument()
    expect(screen.getByText('Firefox Add-ons')).toBeInTheDocument()
    expect(screen.getByText('Edge Add-ons')).toBeInTheDocument()
  })

  it('disables search button when loading', () => {
    render(<SearchPanel {...defaultProps} loading={true} />)
    expect(screen.getByText('Searching...')).toBeDisabled()
  })

  it('calls onSingleSearch when searching single ID', () => {
    render(<SearchPanel {...defaultProps} />)
    const input = screen.getByPlaceholderText('Enter extension ID')
    fireEvent.change(input, { target: { value: 'testid123' } })
    fireEvent.click(screen.getByText('Search Extension'))
    expect(defaultProps.onSingleSearch).toHaveBeenCalledWith(
      'testid123',
      ['chrome', 'firefox', 'edge']
    )
  })
})
