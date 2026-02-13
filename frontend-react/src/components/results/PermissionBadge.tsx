import type { RiskLevel } from '../../types/permissions'
import { Badge } from '../common/Badge'
import { riskColors } from '../../theme/tokens'
import { riskLabels } from '../../utils/permissions'

interface PermissionBadgeProps {
  risk: RiskLevel
  label?: string
}

export function PermissionBadge({ risk, label }: PermissionBadgeProps) {
  return (
    <Badge color={riskColors[risk]}>
      {label || riskLabels[risk]}
    </Badge>
  )
}
