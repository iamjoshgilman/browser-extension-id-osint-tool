export const catppuccinFrappe = {
  base: '#303446',
  mantle: '#292c3c',
  crust: '#232634',
  surface0: '#414559',
  surface1: '#51576d',
  surface2: '#626880',
  overlay0: '#737994',
  overlay1: '#838ba7',
  overlay2: '#949cbb',
  text: '#c6d0f5',
  subtext1: '#b5bfe2',
  subtext0: '#a5adce',
  lavender: '#babbf1',
  blue: '#8caaee',
  sapphire: '#85c1dc',
  sky: '#99d1db',
  teal: '#81c8be',
  green: '#a6d189',
  yellow: '#e5c890',
  peach: '#ef9f76',
  maroon: '#ea999c',
  red: '#e78284',
  mauve: '#ca9ee6',
  pink: '#f4b8e4',
  flamingo: '#eebebe',
  rosewater: '#f2d5cf',
} as const

export const riskColors = {
  critical: catppuccinFrappe.red,
  high: catppuccinFrappe.peach,
  medium: catppuccinFrappe.yellow,
  low: catppuccinFrappe.green,
} as const

export const storeColors = {
  chrome: catppuccinFrappe.blue,
  firefox: catppuccinFrappe.peach,
  edge: catppuccinFrappe.green,
} as const
