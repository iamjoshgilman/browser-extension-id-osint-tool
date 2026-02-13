export interface ExtensionData {
  extension_id: string
  name: string
  store_source: string
  publisher: string
  description: string
  version: string
  user_count: string
  category: string
  rating: string
  rating_count: string
  last_updated: string
  store_url: string
  icon_url: string
  homepage_url: string
  privacy_policy_url: string
  permissions: string[]
  found: boolean
  cached: boolean
  scraped_at: string | null
  delisted?: boolean

  // SOC-relevant fields
  content_rating?: string
  file_size?: string
  languages?: string
  release_date?: string
  update_frequency?: string
  price?: string
  developer_website?: string
  developer_email?: string
  support_url?: string
}

export interface PermissionDiff {
  added: string[]
  removed: string[]
  version_changed: boolean
  previous_version: string | null
  name_changed: boolean
  previous_name: string | null
}

export interface ExtensionSnapshot {
  version: string
  name: string
  permissions: string[]
  scraped_at: string
  diff: PermissionDiff | null
}

export interface ExtensionHistoryResponse {
  extension_id: string
  store: string
  snapshots: ExtensionSnapshot[]
  total_snapshots: number
  has_permission_changes: boolean
}
