export interface MitreTechnique {
  id: string
  name: string
  tactic: string
  url: string
  description: string
}

interface MitreMapping {
  permissions: string[]
  technique: MitreTechnique
}

const MITRE_MAPPINGS: MitreMapping[] = [
  {
    permissions: ['cookies'],
    technique: {
      id: 'T1539',
      name: 'Steal Web Session Cookie',
      tactic: 'Credential Access',
      url: 'https://attack.mitre.org/techniques/T1539/',
      description:
        'Adversaries may steal web session cookies to gain access to authenticated sessions',
    },
  },
  {
    permissions: ['<all_urls>', 'http://*/*', 'https://*/*', '*://*/*'],
    technique: {
      id: 'T1185',
      name: 'Browser Session Hijacking',
      tactic: 'Collection',
      url: 'https://attack.mitre.org/techniques/T1185/',
      description:
        'Adversaries may exploit browser sessions to access information or take actions',
    },
  },
  {
    permissions: ['nativeMessaging'],
    technique: {
      id: 'T1559',
      name: 'Inter-Process Communication',
      tactic: 'Execution',
      url: 'https://attack.mitre.org/techniques/T1559/',
      description:
        'Adversaries may use IPC mechanisms for local code execution or privilege escalation',
    },
  },
  {
    permissions: ['downloads'],
    technique: {
      id: 'T1105',
      name: 'Ingress Tool Transfer',
      tactic: 'Command and Control',
      url: 'https://attack.mitre.org/techniques/T1105/',
      description:
        'Adversaries may transfer tools or files from external systems into a compromised ' +
        'environment',
    },
  },
  {
    permissions: ['history'],
    technique: {
      id: 'T1217',
      name: 'Browser Information Discovery',
      tactic: 'Discovery',
      url: 'https://attack.mitre.org/techniques/T1217/',
      description: 'Adversaries may discover information about browsers to identify targets',
    },
  },
  {
    permissions: ['webRequest', 'webRequestBlocking'],
    technique: {
      id: 'T1557',
      name: 'Adversary-in-the-Middle',
      tactic: 'Credential Access',
      url: 'https://attack.mitre.org/techniques/T1557/',
      description:
        'Adversaries may intercept or modify communications between browser and servers',
    },
  },
  {
    permissions: ['tabs'],
    technique: {
      id: 'T1185',
      name: 'Browser Session Hijacking',
      tactic: 'Collection',
      url: 'https://attack.mitre.org/techniques/T1185/',
      description:
        'Adversaries may exploit browser sessions to access information or take actions',
    },
  },
  {
    permissions: ['clipboardRead', 'clipboardWrite'],
    technique: {
      id: 'T1115',
      name: 'Clipboard Data',
      tactic: 'Collection',
      url: 'https://attack.mitre.org/techniques/T1115/',
      description:
        'Adversaries may collect data stored in the clipboard to capture sensitive information',
    },
  },
  {
    permissions: ['proxy'],
    technique: {
      id: 'T1090',
      name: 'Proxy',
      tactic: 'Command and Control',
      url: 'https://attack.mitre.org/techniques/T1090/',
      description: 'Adversaries may use proxies to direct network traffic between systems',
    },
  },
  {
    permissions: ['debugger'],
    technique: {
      id: 'T1055',
      name: 'Process Injection',
      tactic: 'Defense Evasion',
      url: 'https://attack.mitre.org/techniques/T1055/',
      description:
        'Adversaries may inject code into processes to evade defenses or escalate privileges',
    },
  },
  {
    permissions: ['management'],
    technique: {
      id: 'T1176',
      name: 'Browser Extensions',
      tactic: 'Persistence',
      url: 'https://attack.mitre.org/techniques/T1176/',
      description:
        'Adversaries may install browser extensions for persistence or data collection',
    },
  },
  {
    permissions: ['pageCapture', 'tabCapture', 'desktopCapture'],
    technique: {
      id: 'T1113',
      name: 'Screen Capture',
      tactic: 'Collection',
      url: 'https://attack.mitre.org/techniques/T1113/',
      description: 'Adversaries may capture screen contents to collect information',
    },
  },
  {
    permissions: ['browsingData'],
    technique: {
      id: 'T1070',
      name: 'Indicator Removal',
      tactic: 'Defense Evasion',
      url: 'https://attack.mitre.org/techniques/T1070/',
      description: 'Adversaries may remove indicators of compromise to cover their tracks',
    },
  },
  {
    permissions: ['privacy'],
    technique: {
      id: 'T1562',
      name: 'Impair Defenses',
      tactic: 'Defense Evasion',
      url: 'https://attack.mitre.org/techniques/T1562/',
      description: 'Adversaries may modify security tools or disable protective features',
    },
  },
  {
    permissions: ['scripting'],
    technique: {
      id: 'T1059',
      name: 'Command and Scripting Interpreter',
      tactic: 'Execution',
      url: 'https://attack.mitre.org/techniques/T1059/',
      description: 'Adversaries may abuse scripting interpreters to execute commands',
    },
  },
]

export function getMitreTechniquesForPermissions(permissions: string[]): MitreTechnique[] {
  const seen = new Set<string>()
  const techniques: MitreTechnique[] = []

  for (const mapping of MITRE_MAPPINGS) {
    if (seen.has(mapping.technique.id)) continue

    const hasMatch = mapping.permissions.some((p) => permissions.includes(p))
    if (hasMatch) {
      seen.add(mapping.technique.id)
      techniques.push(mapping.technique)
    }
  }

  return techniques
}
