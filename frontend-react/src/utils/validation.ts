export function isValidExtensionId(id: string): boolean {
  if (!id || id.trim().length === 0) return false
  // Chrome: 32 lowercase letters
  // Firefox: UUID, email-style, or string
  // Edge: 32 alphanumeric
  // Accept broadly - let the backend validate per-store
  return /^[a-zA-Z0-9\-_@.{}]{1,256}$/.test(id.trim())
}
