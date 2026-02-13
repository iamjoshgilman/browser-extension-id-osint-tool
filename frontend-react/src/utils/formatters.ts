export function formatUserCount(count: string): string {
  if (!count) return 'N/A'
  return count
}

export function formatRating(rating: string): string {
  if (!rating) return 'N/A'
  const num = parseFloat(rating)
  if (isNaN(num)) return rating
  return num.toFixed(1)
}

export function truncate(text: string, maxLen: number): string {
  if (!text || text.length <= maxLen) return text
  return text.slice(0, maxLen) + '...'
}

export function storeName(store: string): string {
  const names: Record<string, string> = {
    chrome: 'Chrome Web Store',
    firefox: 'Firefox Add-ons',
    edge: 'Edge Add-ons',
  }
  return names[store] || store
}
