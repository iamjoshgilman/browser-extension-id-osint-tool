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

/**
 * SOC-friendly detailed permission descriptions.
 * Returns a human-readable explanation of what the permission allows,
 * written for security analysts investigating suspicious extensions.
 */
const SOC_DESCRIPTIONS: Record<string, string> = {
  // Critical
  '<all_urls>': 'Can read and modify ALL websites you visit -- full access to page content, forms, and data on every site',
  'http://*/*': 'Can read and modify ALL HTTP (unencrypted) websites you visit',
  'https://*/*': 'Can read and modify ALL HTTPS websites you visit, including banking and email',
  '*://*/*': 'Can read and modify ALL websites you visit regardless of protocol',
  nativeMessaging: 'Can communicate with programs installed on your computer -- potential for local code execution',
  debugger: 'Can attach to the Chrome debugger protocol, enabling full control over browser behavior',
  proxy: 'Can control browser proxy settings, potentially redirecting all traffic through attacker infrastructure',
  webRequestBlocking: 'Can intercept, modify, and block network requests before they are sent -- can alter page content',

  // High
  tabs: 'Can see your open tabs, their URLs, titles, and favicons -- reveals browsing activity',
  history: 'Can read and delete your entire browsing history',
  cookies: 'Can read and modify browser cookies for any site -- enables session hijacking',
  webRequest: 'Can observe and analyze all network requests made by the browser',
  management: 'Can list, enable, disable, and uninstall other extensions -- can neutralize security tools',
  downloads: 'Can initiate, pause, cancel, and manage file downloads',
  browsingData: 'Can clear browsing data including history, cookies, and cache -- can cover tracks',
  privacy: 'Can control browser privacy settings such as tracking protection',
  topSites: 'Can read your most frequently visited websites',
  sessions: 'Can access recently closed tabs and windows, including their URLs',
  pageCapture: 'Can save complete web pages as MHTML files -- can exfiltrate page content',
  tabCapture: 'Can capture visible content of tabs as a media stream -- can record what you see',
  desktopCapture: 'Can capture your entire screen or application windows',
  contentSettings: 'Can control per-site content settings including cookies, JavaScript, and plugins',

  // Medium
  storage: 'Can store and retrieve data locally in the browser',
  clipboardRead: 'Can read the contents of your clipboard -- may capture passwords or sensitive data',
  clipboardWrite: 'Can write data to your clipboard -- could replace copied content',
  notifications: 'Can show desktop notifications -- potential for phishing or social engineering',
  scripting: 'Can inject and execute JavaScript code on web pages',
  declarativeNetRequest: 'Can block or redirect network requests using declarative rules',
  webNavigation: 'Can observe and track all navigation events in the browser',
  contextMenus: 'Can add items to the browser right-click context menu',
  alarms: 'Can schedule periodic background tasks -- can maintain persistent activity',
  geolocation: 'Can access your geographic location',
  unlimitedStorage: 'Can store unlimited data locally -- unusual for most extensions',

  // Low
  activeTab: 'Can access the currently active tab when the user interacts with the extension',
  bookmarks: 'Can read and modify your bookmarks',
  identity: 'Can obtain OAuth2 authentication tokens',
  idle: 'Can detect when the system is idle -- may be used to trigger background activity',
  theme: 'Can customize the browser appearance/theme',
  fontSettings: 'Can manage browser font settings',
  i18n: 'Can access internationalization/localization APIs',
  offscreen: 'Can create hidden offscreen documents for background processing',
  sidePanel: 'Can use the browser side panel API',
  action: 'Can control the extension toolbar icon and popup',
  runtime: 'Can use extension messaging APIs for inter-component communication',
  tts: 'Can use the text-to-speech engine',
}

/**
 * Get a SOC-analyst-friendly description of what a browser permission allows.
 * Returns a detailed explanation suitable for security investigation context.
 */
export function getPermissionDescription(permission: string): string {
  const normalized = permission.trim()

  if (SOC_DESCRIPTIONS[normalized]) {
    return SOC_DESCRIPTIONS[normalized]
  }

  // URL patterns
  if (/^https?:\/\//.test(normalized) || /^\*:\/\//.test(normalized)) {
    if (['<all_urls>', 'http://*/*', 'https://*/*', '*://*/*'].includes(normalized)) {
      return 'Can read and modify ALL websites you visit'
    }
    return `Can access and modify content on ${normalized}`
  }

  return `Unknown permission -- not in standard catalog, may indicate custom or suspicious capability`
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
