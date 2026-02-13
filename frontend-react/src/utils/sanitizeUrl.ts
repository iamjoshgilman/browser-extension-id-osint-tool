const SAFE_PROTOCOLS = ['https:', 'http:']

export function sanitizeUrl(url: string | undefined): string | undefined {
  if (!url) return undefined
  try {
    const parsed = new URL(url)
    if (SAFE_PROTOCOLS.includes(parsed.protocol)) {
      return url
    }
  } catch {
    // Invalid URL
  }
  return undefined
}
