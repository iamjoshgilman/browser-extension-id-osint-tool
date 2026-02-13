export type RiskLevel = 'critical' | 'high' | 'medium' | 'low'

export interface PermissionInfo {
  name: string
  risk: RiskLevel
  description: string
}
