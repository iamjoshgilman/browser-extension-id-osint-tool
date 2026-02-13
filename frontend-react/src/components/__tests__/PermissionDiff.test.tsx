import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { PermissionDiff } from '../results/PermissionDiff'
import type { PermissionDiff as PermissionDiffType } from '../../types/extension'

describe('PermissionDiff', () => {
  it('shows added permissions with "+" and green styling', () => {
    const diff: PermissionDiffType = {
      added: ['cookies', 'tabs'],
      removed: [],
      version_changed: false,
      previous_version: null,
      name_changed: false,
      previous_name: null,
    }

    render(<PermissionDiff diff={diff} />)
    expect(screen.getByText('Added permissions:')).toBeInTheDocument()
    expect(screen.getByText('cookies')).toBeInTheDocument()
    expect(screen.getByText('tabs')).toBeInTheDocument()

    // Check for "+" prefix (there should be 2 instances)
    const plusSigns = screen.getAllByText('+')
    expect(plusSigns).toHaveLength(2)
  })

  it('shows removed permissions with "-" and red styling', () => {
    const diff: PermissionDiffType = {
      added: [],
      removed: ['history', 'downloads'],
      version_changed: false,
      previous_version: null,
      name_changed: false,
      previous_name: null,
    }

    render(<PermissionDiff diff={diff} />)
    expect(screen.getByText('Removed permissions:')).toBeInTheDocument()
    expect(screen.getByText('history')).toBeInTheDocument()
    expect(screen.getByText('downloads')).toBeInTheDocument()

    // Check for "-" prefix (there should be 2 instances)
    const minusSigns = screen.getAllByText('-')
    expect(minusSigns).toHaveLength(2)
  })

  it('shows version change display', () => {
    const diff: PermissionDiffType = {
      added: [],
      removed: [],
      version_changed: true,
      previous_version: '1.0',
      name_changed: false,
      previous_name: null,
    }

    render(<PermissionDiff diff={diff} />)
    expect(screen.getByText('Version:')).toBeInTheDocument()
    expect(screen.getByText(/1\.0/)).toBeInTheDocument()
  })

  it('shows name change display', () => {
    const diff: PermissionDiffType = {
      added: [],
      removed: [],
      version_changed: false,
      previous_version: null,
      name_changed: true,
      previous_name: 'Old Extension Name',
    }

    render(<PermissionDiff diff={diff} />)
    expect(screen.getByText('Name changed:')).toBeInTheDocument()
    expect(screen.getByText('Old Extension Name')).toBeInTheDocument()
  })

  it('shows "No permission changes" when no changes exist', () => {
    const diff: PermissionDiffType = {
      added: [],
      removed: [],
      version_changed: false,
      previous_version: null,
      name_changed: false,
      previous_name: null,
    }

    render(<PermissionDiff diff={diff} />)
    expect(screen.getByText('No permission changes')).toBeInTheDocument()
  })

  it('shows both added and removed permissions together', () => {
    const diff: PermissionDiffType = {
      added: ['cookies'],
      removed: ['history'],
      version_changed: true,
      previous_version: '1.0',
      name_changed: false,
      previous_name: null,
    }

    render(<PermissionDiff diff={diff} />)
    expect(screen.getByText('Added permissions:')).toBeInTheDocument()
    expect(screen.getByText('Removed permissions:')).toBeInTheDocument()
    expect(screen.getByText('cookies')).toBeInTheDocument()
    expect(screen.getByText('history')).toBeInTheDocument()
    expect(screen.getByText('Version:')).toBeInTheDocument()
  })
})
