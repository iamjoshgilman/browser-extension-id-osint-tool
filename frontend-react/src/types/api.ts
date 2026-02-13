import type { ExtensionData } from './extension'

export interface SearchRequest {
  extension_id: string
  stores: string[]
  include_permissions?: boolean
}

export interface BulkSearchRequest {
  extension_ids: string[]
  stores: string[]
  include_permissions?: boolean
}

export interface SearchResponse {
  extension_id: string
  results: ExtensionData[]
}

export interface BulkSearchResponse {
  results: Record<string, ExtensionData[]>
}

export interface SearchByNameRequest {
  name: string
  exclude_stores?: string[]
  limit?: number
}

export interface SearchByNameResponse {
  name: string
  results: Record<string, ExtensionData[]>
  search_urls: Record<string, string>
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
