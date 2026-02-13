import { describe, it, expect } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { PermissionHistory } from '../results/PermissionHistory'
import type { ExtensionHistoryResponse } from '../../types/extension'

describe('PermissionHistory', () => {
  it('shows "No history" message when snapshots are empty', () => {
    const history: ExtensionHistoryResponse = {
      extension_id: 'test-id',
      store: 'chrome',
      snapshots: [],
      total_snapshots: 0,
      has_permission_changes: false,
    }

    render(<PermissionHistory history={history} />)
    expect(screen.getByText('No history available yet')).toBeInTheDocument()
  })

  it('shows "No permission changes" message when no changes detected', () => {
    const history: ExtensionHistoryResponse = {
      extension_id: 'test-id',
      store: 'chrome',
      snapshots: [
        {
          version: '1.0',
          name: 'Test Extension',
          permissions: ['tabs', 'storage'],
          scraped_at: '2025-01-01T00:00:00',
          diff: null,
        },
      ],
      total_snapshots: 1,
      has_permission_changes: false,
    }

    render(<PermissionHistory history={history} />)
    expect(screen.getByText('No permission changes detected')).toBeInTheDocument()
  })

  it('renders timeline entries with snapshots', () => {
    const history: ExtensionHistoryResponse = {
      extension_id: 'test-id',
      store: 'chrome',
      snapshots: [
        {
          version: '1.0',
          name: 'Test Extension',
          permissions: ['tabs', 'storage'],
          scraped_at: '2025-01-01T00:00:00',
          diff: null,
        },
        {
          version: '1.1',
          name: 'Test Extension',
          permissions: ['tabs', 'storage', 'cookies'],
          scraped_at: '2025-02-01T00:00:00',
          diff: {
            added: ['cookies'],
            removed: [],
            version_changed: true,
            previous_version: '1.0',
            name_changed: false,
            previous_name: null,
          },
        },
      ],
      total_snapshots: 2,
      has_permission_changes: true,
    }

    render(<PermissionHistory history={history} />)
    expect(screen.getByText('v1.0')).toBeInTheDocument()
    expect(screen.getByText('v1.1')).toBeInTheDocument()
    expect(screen.getByText('2 permissions')).toBeInTheDocument()
    expect(screen.getByText('3 permissions')).toBeInTheDocument()
  })

  it('shows added/removed indicators for changes', () => {
    const history: ExtensionHistoryResponse = {
      extension_id: 'test-id',
      store: 'chrome',
      snapshots: [
        {
          version: '1.1',
          name: 'Test Extension',
          permissions: ['tabs', 'storage', 'cookies'],
          scraped_at: '2025-02-01T00:00:00',
          diff: {
            added: ['cookies'],
            removed: ['history'],
            version_changed: true,
            previous_version: '1.0',
            name_changed: false,
            previous_name: null,
          },
        },
      ],
      total_snapshots: 1,
      has_permission_changes: true,
    }

    render(<PermissionHistory history={history} />)
    expect(screen.getByText('+1')).toBeInTheDocument()
    expect(screen.getByText('-1')).toBeInTheDocument()
  })

  it('expands to show PermissionDiff when clicked', () => {
    const history: ExtensionHistoryResponse = {
      extension_id: 'test-id',
      store: 'chrome',
      snapshots: [
        {
          version: '1.1',
          name: 'Test Extension',
          permissions: ['tabs', 'storage', 'cookies'],
          scraped_at: '2025-02-01T00:00:00',
          diff: {
            added: ['cookies'],
            removed: [],
            version_changed: true,
            previous_version: '1.0',
            name_changed: false,
            previous_name: null,
          },
        },
      ],
      total_snapshots: 1,
      has_permission_changes: true,
    }

    render(<PermissionHistory history={history} />)

    // Initially collapsed, shouldn't show permission details
    expect(screen.queryByText('Added permissions:')).not.toBeInTheDocument()

    // Click to expand
    const card = screen.getByText('v1.1').closest('div')!.parentElement!
    fireEvent.click(card)

    // Now should show permission diff
    expect(screen.getByText('Added permissions:')).toBeInTheDocument()
  })
})
