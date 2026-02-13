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
    `/extension/${encodeURIComponent(extensionId)}/history?store=${store}`
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
  return apiClient.request<BulkJobResponse>(`/bulk-search-async/${jobId}`)
}

export async function cancelBulkJob(jobId: string): Promise<{ job_id: string; status: string }> {
  return apiClient.request<{ job_id: string; status: string }>(`/bulk-search-async/${jobId}`, {
    method: 'DELETE',
  })
}
