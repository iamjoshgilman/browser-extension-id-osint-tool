import { Badge } from '../common/Badge'
import { storeColors } from '../../theme/tokens'

interface StoreBadgeProps {
  store: string
}

export function StoreBadge({ store }: StoreBadgeProps) {
  const color = storeColors[store as keyof typeof storeColors] || '#737994'
  return <Badge color={color}>{store.toUpperCase()}</Badge>
}
