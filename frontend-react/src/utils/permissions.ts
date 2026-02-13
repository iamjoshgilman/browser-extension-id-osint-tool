import type { RiskLevel, PermissionInfo } from '../types/permissions'

const CRITICAL_PERMISSIONS: Record<string, string> = {
  '<all_urls>': 'Access to all websites',
  'http://*/*': 'Access to all HTTP websites',
  'https://*/*': 'Access to all HTTPS websites',
  '*://*/*': 'Access to all websites',
  nativeMessaging: 'Communicate with native applications',
  debugger: 'Access Chrome debugger protocol',
  proxy: 'Control browser proxy settings',
  webRequestBlocking: 'Intercept and modify network requests',
}

const HIGH_PERMISSIONS: Record<string, string> = {
  tabs: 'Read browser tab URLs and titles',
  history: 'Access browsing history',
  cookies: 'Read and modify cookies',
  webRequest: 'Observe network requests',
  management: 'Manage other extensions',
  downloads: 'Manage downloads',
  browsingData: 'Clear browsing data',
  privacy: 'Control privacy settings',
  topSites: 'Access most visited sites',
  sessions: 'Access recently closed tabs/windows',
  pageCapture: 'Save pages as MHTML',
  tabCapture: 'Capture tab content',
  desktopCapture: 'Capture screen content',
  contentSettings: 'Control content settings (cookies, JS, plugins)',
}

const MEDIUM_PERMISSIONS: Record<string, string> = {
  storage: 'Store data locally',
  clipboardRead: 'Read clipboard contents',
  clipboardWrite: 'Write to clipboard',
  notifications: 'Show desktop notifications',
  scripting: 'Inject scripts into pages',
  declarativeNetRequest: 'Block or modify network requests via rules',
  webNavigation: 'Observe navigation events',
  contextMenus: 'Add context menu items',
  alarms: 'Schedule periodic tasks',
  geolocation: 'Access location data',
  unlimitedStorage: 'Unlimited local storage',
}

const LOW_PERMISSIONS: Record<string, string> = {
  activeTab: 'Access current active tab only',
  bookmarks: 'Access bookmarks',
  identity: 'Get OAuth2 tokens',
  idle: 'Detect idle state',
  theme: 'Customize browser theme',
  fontSettings: 'Manage font settings',
  i18n: 'Internationalization',
  offscreen: 'Create offscreen documents',
  sidePanel: 'Use side panel API',
  action: 'Control toolbar icon',
  runtime: 'Extension runtime messaging',
  tts: 'Text-to-speech',
}

function isUrlPattern(permission: string): boolean {
  return /^https?:\/\//.test(permission) || /^\*:\/\//.test(permission)
}

function isBroadUrlPattern(permission: string): boolean {
  return ['<all_urls>', 'http://*/*', 'https://*/*', '*://*/*'].includes(permission)
}

export function classifyPermission(permission: string): PermissionInfo {
  const normalized = permission.trim()

  if (CRITICAL_PERMISSIONS[normalized]) {
    return { name: normalized, risk: 'critical', description: CRITICAL_PERMISSIONS[normalized] }
  }
  if (HIGH_PERMISSIONS[normalized]) {
    return { name: normalized, risk: 'high', description: HIGH_PERMISSIONS[normalized] }
  }
  if (MEDIUM_PERMISSIONS[normalized]) {
    return { name: normalized, risk: 'medium', description: MEDIUM_PERMISSIONS[normalized] }
  }
  if (LOW_PERMISSIONS[normalized]) {
    return { name: normalized, risk: 'low', description: LOW_PERMISSIONS[normalized] }
  }

  // URL patterns
  if (isUrlPattern(normalized)) {
    if (isBroadUrlPattern(normalized)) {
      return { name: normalized, risk: 'critical', description: 'Access to all websites' }
    }
    return { name: normalized, risk: 'high', description: `Access to ${normalized}` }
  }

  // Unknown = medium (suspicious for SOC)
  return { name: normalized, risk: 'medium', description: `Unknown permission: ${normalized}` }
}

export function getAggregateRisk(permissions: string[]): RiskLevel {
  if (permissions.length === 0) return 'low'
  const risks = permissions.map(p => classifyPermission(p).risk)
  if (risks.includes('critical')) return 'critical'
  if (risks.includes('high')) return 'high'
  if (risks.includes('medium')) return 'medium'
  return 'low'
}

export function classifyAllPermissions(permissions: string[]): PermissionInfo[] {
  const classified = permissions.map(classifyPermission)
  const order: RiskLevel[] = ['critical', 'high', 'medium', 'low']
  return classified.sort((a, b) => order.indexOf(a.risk) - order.indexOf(b.risk))
}

export const riskLabels: Record<RiskLevel, string> = {
  critical: 'Critical',
  high: 'High',
  medium: 'Medium',
  low: 'Low',
}
