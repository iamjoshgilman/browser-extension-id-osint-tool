import { apiClient } from './client'
import type {
  SearchRequest,
  SearchResponse,
  BulkSearchRequest,
  BulkSearchResponse,
  BulkJobResponse,
  SearchByNameRequest,
  SearchByNameResponse,
  HealthResponse,
} from '../types/api'
import type { ExtensionHistoryResponse } from '../types/extension'

const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i

function validateJobId(jobId: string): string {
  if (!UUID_RE.test(jobId)) throw new Error('Invalid job ID')
  return encodeURIComponent(jobId)
}

export async function searchExtension(req: SearchRequest): Promise<SearchResponse> {
  return apiClient.request<SearchResponse>('/search', {
    method: 'POST',
    body: JSON.stringify(req),
  })
}

export async function bulkSearchExtensions(req: BulkSearchRequest): Promise<BulkSearchResponse> {
  return apiClient.request<BulkSearchResponse>('/bulk-search', {
    method: 'POST',
    body: JSON.stringify(req),
  })
}

export async function searchByName(
  name: string,
  excludeStores?: string[],
  limit?: number
): Promise<SearchByNameResponse> {
  const req: SearchByNameRequest = {
    name,
    exclude_stores: excludeStores,
    limit,
  }
  return apiClient.request<SearchByNameResponse>('/search-by-name', {
    method: 'POST',
    body: JSON.stringify(req),
  })
}

export async function healthCheck(): Promise<HealthResponse> {
  return apiClient.request<HealthResponse>('/health')
}

export async function getExtensionHistory(
  extensionId: string,
  store: string
): Promise<ExtensionHistoryResponse> {
  return apiClient.request<ExtensionHistoryResponse>(
    `/extension/${encodeURIComponent(extensionId)}/history?store=${encodeURIComponent(store)}`
  )
}

export async function submitBulkSearchAsync(
  ids: string[],
  stores: string[],
  includePermissions: boolean
): Promise<BulkJobResponse> {
  return apiClient.request<BulkJobResponse>('/bulk-search-async', {
    method: 'POST',
    body: JSON.stringify({
      extension_ids: ids,
      stores,
      include_permissions: includePermissions,
    }),
  })
}

export async function getBulkJobStatus(jobId: string): Promise<BulkJobResponse> {
  const validJobId = validateJobId(jobId)
  return apiClient.request<BulkJobResponse>(`/bulk-search-async/${validJobId}`)
}

export async function cancelBulkJob(jobId: string): Promise<{ job_id: string; status: string }> {
  const validJobId = validateJobId(jobId)
  return apiClient.request<{ job_id: string; status: string }>(`/bulk-search-async/${validJobId}`, {
    method: 'DELETE',
  })
}
