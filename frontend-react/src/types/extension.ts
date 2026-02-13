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
}
