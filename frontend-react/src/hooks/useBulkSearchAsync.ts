import { useState, useCallback, useRef } from 'react'
import { submitBulkSearchAsync, cancelBulkJob, getBulkJobStatus } from '../api/endpoints'
import type { ExtensionData } from '../types/extension'

interface BulkProgress {
  completed: number
  total: number
  pct: number
}

interface UseBulkSearchAsyncReturn {
  results: ExtensionData[]
  loading: boolean
  error: string | null
  progress: BulkProgress
  jobId: string | null
  status: string | null
  startBulkSearch: (ids: string[], stores: string[], includePermissions: boolean) => Promise<void>
  cancelSearch: () => Promise<void>
  clearResults: () => void
}

export function useBulkSearchAsync(): UseBulkSearchAsyncReturn {
  const [results, setResults] = useState<ExtensionData[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [progress, setProgress] = useState<BulkProgress>({ completed: 0, total: 0, pct: 0 })
  const [jobId, setJobId] = useState<string | null>(null)
  const [status, setStatus] = useState<string | null>(null)

  const eventSourceRef = useRef<EventSource | null>(null)
  const pollIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const cleanup = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close()
      eventSourceRef.current = null
    }
    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current)
      pollIntervalRef.current = null
    }
  }, [])

  const collectResults = useCallback((jobResults: Record<string, any[]>): ExtensionData[] => {
    const allFound: ExtensionData[] = []
    for (const storeResults of Object.values(jobResults)) {
      if (typeof storeResults === 'object' && !Array.isArray(storeResults)) {
        // Results are keyed by store: { chrome: {...}, firefox: {...} }
        for (const result of Object.values(storeResults)) {
          if (result && typeof result === 'object' && (result as any).found !== false) {
            allFound.push(result as ExtensionData)
          }
        }
      } else if (Array.isArray(storeResults)) {
        allFound.push(...storeResults.filter((r: any) => r.found !== false))
      }
    }
    return allFound
  }, [])

  const startBulkSearch = useCallback(
    async (ids: string[], stores: string[], includePermissions: boolean) => {
      cleanup()
      setLoading(true)
      setError(null)
      setResults([])
      setProgress({ completed: 0, total: 0, pct: 0 })
      setStatus('pending')

      try {
        const response = await submitBulkSearchAsync(ids, stores, includePermissions)
        const currentJobId = response.job_id
        setJobId(currentJobId)
        setProgress({
          completed: 0,
          total: response.total_tasks,
          pct: 0,
        })

        // Try SSE first, fall back to polling
        const streamUrl = `/api/bulk-search-async/${currentJobId}/stream`
        const es = new EventSource(streamUrl)
        eventSourceRef.current = es

        es.addEventListener('progress', (event: MessageEvent) => {
          try {
            const data = JSON.parse(event.data)
            setProgress({
              completed: data.completed || 0,
              total: data.total || response.total_tasks,
              pct: data.total > 0 ? Math.round((data.completed / data.total) * 100) : 0,
            })
            setStatus('running')
          } catch {
            // ignore parse errors
          }
        })

        es.addEventListener('error', (event: MessageEvent) => {
          try {
            const data = JSON.parse(event.data)
            if (data.error) {
              setError(data.error)
            }
          } catch {
            // ignore parse errors
          }
        })

        es.addEventListener('complete', async (event: MessageEvent) => {
          try {
            const data = JSON.parse(event.data)
            setStatus(data.status || 'completed')
          } catch {
            setStatus('completed')
          }

          es.close()
          eventSourceRef.current = null

          // Fetch final results
          try {
            const finalJob = await getBulkJobStatus(currentJobId)
            setProgress({
              completed: finalJob.completed_tasks,
              total: finalJob.total_tasks,
              pct: finalJob.progress_pct,
            })
            if (finalJob.results) {
              const collected = collectResults(finalJob.results)
              setResults(collected)
              if (collected.length === 0) {
                setError('No extensions found in selected stores.')
              }
            }
            setStatus(finalJob.status)
          } catch {
            setError('Failed to fetch final results')
          }
          setLoading(false)
        })

        es.onerror = () => {
          // SSE connection failed, fall back to polling
          es.close()
          eventSourceRef.current = null

          let pollAttempts = 0
          const MAX_POLL_ATTEMPTS = 150 // 5 minutes at 2s intervals

          pollIntervalRef.current = setInterval(async () => {
            pollAttempts++
            if (pollAttempts > MAX_POLL_ATTEMPTS) {
              clearInterval(pollIntervalRef.current!)
              pollIntervalRef.current = null
              setError('Bulk search timed out')
              setLoading(false)
              return
            }

            try {
              const job = await getBulkJobStatus(currentJobId)
              setProgress({
                completed: job.completed_tasks,
                total: job.total_tasks,
                pct: job.progress_pct,
              })
              setStatus(job.status)

              if (['completed', 'failed', 'cancelled'].includes(job.status)) {
                if (pollIntervalRef.current) {
                  clearInterval(pollIntervalRef.current)
                  pollIntervalRef.current = null
                }
                if (job.results) {
                  const collected = collectResults(job.results)
                  setResults(collected)
                  if (collected.length === 0) {
                    setError('No extensions found in selected stores.')
                  }
                }
                if (job.status === 'failed') {
                  setError('Bulk search job failed')
                }
                setLoading(false)
              }
            } catch {
              // ignore polling errors
            }
          }, 2000)
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to start bulk search')
        setLoading(false)
        setStatus('failed')
      }
    },
    [cleanup, collectResults]
  )

  const cancelSearch = useCallback(async () => {
    cleanup()
    if (jobId) {
      try {
        await cancelBulkJob(jobId)
        setStatus('cancelled')
      } catch {
        // ignore cancel errors
      }
    }
    setLoading(false)
  }, [jobId, cleanup])

  const clearResults = useCallback(() => {
    cleanup()
    setResults([])
    setError(null)
    setProgress({ completed: 0, total: 0, pct: 0 })
    setJobId(null)
    setStatus(null)
  }, [cleanup])

  return {
    results,
    loading,
    error,
    progress,
    jobId,
    status,
    startBulkSearch,
    cancelSearch,
    clearResults,
  }
}
