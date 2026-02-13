import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { BulkProgress } from '../search/BulkProgress'

describe('BulkProgress', () => {
  const defaultProps = {
    completed: 5,
    total: 10,
    pct: 50,
    status: 'running' as const,
    onCancel: vi.fn(),
  }

  it('renders progress information', () => {
    render(<BulkProgress {...defaultProps} />)
    expect(screen.getByText('5 / 10 completed (50%)')).toBeInTheDocument()
    expect(screen.getByTestId('bulk-progress')).toBeInTheDocument()
  })

  it('shows status text when running', () => {
    render(<BulkProgress {...defaultProps} />)
    expect(screen.getByText('Searching... 5 of 10 tasks')).toBeInTheDocument()
  })

  it('shows cancel button when running', () => {
    render(<BulkProgress {...defaultProps} />)
    expect(screen.getByTestId('cancel-btn')).toBeInTheDocument()
  })

  it('calls onCancel when cancel button is clicked', () => {
    const onCancel = vi.fn()
    render(<BulkProgress {...defaultProps} onCancel={onCancel} />)
    fireEvent.click(screen.getByTestId('cancel-btn'))
    expect(onCancel).toHaveBeenCalledTimes(1)
  })

  it('shows completed status text', () => {
    render(<BulkProgress {...defaultProps} status="completed" completed={10} pct={100} />)
    expect(screen.getByText('Bulk search completed')).toBeInTheDocument()
  })

  it('hides cancel button when completed', () => {
    render(<BulkProgress {...defaultProps} status="completed" />)
    expect(screen.queryByTestId('cancel-btn')).not.toBeInTheDocument()
  })

  it('shows pending status text', () => {
    render(<BulkProgress {...defaultProps} status="pending" completed={0} pct={0} />)
    expect(screen.getByText('Starting bulk search...')).toBeInTheDocument()
  })

  it('shows cancelled status text', () => {
    render(<BulkProgress {...defaultProps} status="cancelled" />)
    expect(screen.getByText('Bulk search cancelled')).toBeInTheDocument()
  })

  it('shows failed status text', () => {
    render(<BulkProgress {...defaultProps} status="failed" />)
    expect(screen.getByText('Bulk search failed')).toBeInTheDocument()
  })

  it('renders progress bar with correct width', () => {
    render(<BulkProgress {...defaultProps} />)
    const fill = screen.getByTestId('progress-fill')
    expect(fill).toHaveStyle({ width: '50%' })
  })
})
