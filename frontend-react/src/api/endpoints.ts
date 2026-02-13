import { apiClient } from './client'
import type {
  SearchRequest,
  SearchResponse,
  BulkSearchRequest,
  BulkSearchResponse,
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
