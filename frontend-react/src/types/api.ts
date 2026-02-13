import type { ExtensionData } from './extension'

export interface SearchRequest {
  extension_id: string
  stores: string[]
}

export interface BulkSearchRequest {
  extension_ids: string[]
  stores: string[]
}

export interface SearchResponse {
  extension_id: string
  results: ExtensionData[]
}

export interface BulkSearchResponse {
  results: Record<string, ExtensionData[]>
}

export interface HealthResponse {
  status: string
  version: string
  database: boolean
}

export interface StatsResponse {
  total_cached: number
  total_searches: number
  cache_hit_rate: number
}

export interface ApiError {
  error: string
  message?: string
}
