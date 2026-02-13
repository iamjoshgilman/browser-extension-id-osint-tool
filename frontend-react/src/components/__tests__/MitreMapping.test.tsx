import { describe, it, expect } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { MitreMapping } from '../results/MitreMapping'

describe('MitreMapping', () => {
  it('returns null when no techniques match', () => {
    const { container } = render(<MitreMapping permissions={['activeTab']} />)
    expect(container.firstChild).toBeNull()
  })

  it('returns null for empty permissions', () => {
    const { container } = render(<MitreMapping permissions={[]} />)
    expect(container.firstChild).toBeNull()
  })

  it('renders toggle button with technique count', () => {
    render(<MitreMapping permissions={['cookies', 'history']} />)
    expect(screen.getByText(/MITRE ATT&CK Techniques \(2\)/)).toBeInTheDocument()
  })

  it('starts collapsed and expands on click', () => {
    render(<MitreMapping permissions={['cookies']} />)

    // Should not show technique details initially
    expect(screen.queryByText('T1539')).not.toBeInTheDocument()

    // Click to expand
    fireEvent.click(screen.getByRole('button'))

    // Should now show technique details
    expect(screen.getByText('T1539')).toBeInTheDocument()
    expect(screen.getByText('Steal Web Session Cookie')).toBeInTheDocument()
    expect(screen.getByText('Credential Access')).toBeInTheDocument()
  })

  it('technique IDs link to MITRE ATT&CK', () => {
    render(<MitreMapping permissions={['cookies']} />)
    fireEvent.click(screen.getByRole('button'))

    const link = screen.getByText('T1539')
    expect(link.tagName).toBe('A')
    expect(link).toHaveAttribute('href', 'https://attack.mitre.org/techniques/T1539/')
    expect(link).toHaveAttribute('target', '_blank')
    expect(link).toHaveAttribute('rel', 'noopener noreferrer')
  })
})
