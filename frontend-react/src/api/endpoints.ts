import { apiClient } from './client'
import type {
  SearchRequest,
  SearchResponse,
  BulkSearchRequest,
  BulkSearchResponse,
  HealthResponse,
} from '../types/api'

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

export async function healthCheck(): Promise<HealthResponse> {
  return apiClient.request<HealthResponse>('/health')
}
