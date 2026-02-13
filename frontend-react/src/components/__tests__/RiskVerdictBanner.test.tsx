import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { RiskVerdictBanner } from '../results/RiskVerdictBanner'
import type { RiskVerdict } from '../../utils/riskVerdict'

describe('RiskVerdictBanner', () => {
  it('returns null when level is null', () => {
    const verdict: RiskVerdict = { level: null, message: '', signals: [] }
    const { container } = render(<RiskVerdictBanner verdict={verdict} />)
    expect(container.firstChild).toBeNull()
  })

  it('renders critical risk banner', () => {
    const verdict: RiskVerdict = {
      level: 'critical',
      message: 'CRITICAL RISK',
      signals: [{ severity: 'critical', label: 'On malicious blocklist' }],
    }
    render(<RiskVerdictBanner verdict={verdict} />)
    expect(screen.getByText('CRITICAL RISK')).toBeInTheDocument()
    expect(screen.getByText('On malicious blocklist')).toBeInTheDocument()
  })

  it('renders high risk banner', () => {
    const verdict: RiskVerdict = {
      level: 'high',
      message: 'HIGH RISK',
      signals: [{ severity: 'high', label: 'Delisted from store' }],
    }
    render(<RiskVerdictBanner verdict={verdict} />)
    expect(screen.getByText('HIGH RISK')).toBeInTheDocument()
  })

  it('renders multiple signal badges', () => {
    const verdict: RiskVerdict = {
      level: 'critical',
      message: 'CRITICAL RISK',
      signals: [
        { severity: 'critical', label: 'On malicious blocklist' },
        { severity: 'high', label: 'Delisted from store' },
        { severity: 'low', label: 'Not updated in 2+ years' },
      ],
    }
    render(<RiskVerdictBanner verdict={verdict} />)
    expect(screen.getByText('On malicious blocklist')).toBeInTheDocument()
    expect(screen.getByText('Delisted from store')).toBeInTheDocument()
    expect(screen.getByText('Not updated in 2+ years')).toBeInTheDocument()
  })

  it('renders low risk banner', () => {
    const verdict: RiskVerdict = {
      level: 'low',
      message: 'Low Risk',
      signals: [{ severity: 'low', label: 'Not updated in 2+ years' }],
    }
    render(<RiskVerdictBanner verdict={verdict} />)
    expect(screen.getByText('Low Risk')).toBeInTheDocument()
  })
})
