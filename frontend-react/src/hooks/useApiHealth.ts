import { useState, useEffect } from 'react'
import { healthCheck } from '../api/endpoints'

export function useApiHealth(): { healthy: boolean | null } {
  const [healthy, setHealthy] = useState<boolean | null>(null)

  useEffect(() => {
    healthCheck()
      .then(() => setHealthy(true))
      .catch(() => setHealthy(false))
  }, [])

  return { healthy }
}
