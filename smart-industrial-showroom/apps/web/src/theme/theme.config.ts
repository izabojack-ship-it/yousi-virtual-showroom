/**
 * Industry 4.0 Design System — Smart Industrial Cloud Showroom
 * ----------------------------------------------------------------
 * Central theme tokens consumed by Tailwind (`tailwind.config.js`) and React
 * components. Maps a traditional factory aesthetic to a cyber-control-room UI.
 */

export const industry40Theme = {
  /** Deep backgrounds — control-room / carbon-fiber factory floor */
  colors: {
    background: {
      primary: '#1a1a1a',       // Deep Carbon Charcoal
      secondary: '#0a192f',     // Cyber Dark Blue
      elevated: '#112240',
      overlay: 'rgba(10, 25, 47, 0.72)',
    },
    accent: {
      cyberBlue: '#00ffff',     // Electric Cyber Blue — data lines, borders
      neonGreen: '#39ff14',     // Neon Green — status OK, live metrics
      alert: '#ff3864',
      warning: '#ffdd57',
    },
    text: {
      primary: '#e6f1ff',
      secondary: '#8892b0',
      muted: '#5a6a8a',
      inverse: '#0a192f',
    },
    glass: {
      surface: 'rgba(17, 34, 64, 0.55)',
      border: 'rgba(0, 255, 255, 0.35)',
      glow: 'rgba(0, 255, 255, 0.15)',
    },
    data: {
      line: '#00ffff',
      grid: 'rgba(0, 255, 255, 0.08)',
      pulse: '#39ff14',
    },
  },

  typography: {
    /** Dashboard / telemetry widgets */
    mono: "'Roboto Mono', 'JetBrains Mono', ui-monospace, monospace",
    /** Headlines & AR panel titles */
    display: "'Space Grotesk', 'Segoe UI', system-ui, sans-serif",
    /** Body copy in glass panels */
    body: "'Inter', 'Noto Sans TC', system-ui, sans-serif",
  },

  spacing: {
    panel: '1.25rem',
    anchor: '0.75rem',
  },

  radius: {
    panel: '0.75rem',
    chip: '9999px',
  },

  shadow: {
    /** Neon cyber glow for glass panels & AR anchors */
    cyber: '0 0 20px rgba(0, 255, 255, 0.25), 0 0 40px rgba(0, 255, 255, 0.08)',
    neonGreen: '0 0 16px rgba(57, 255, 20, 0.35)',
    panel: '0 8px 32px rgba(0, 0, 0, 0.45)',
  },

  animation: {
    /** AR anchor bobbing — synced with ARShowroom.tsx */
    floatDuration: '3.2s',
    floatDistance: '8px',
    pulseDuration: '2s',
  },

  blur: {
    glass: '16px',
    heavy: '24px',
  },
} as const;

export type Industry40Theme = typeof industry40Theme;

/** Tailwind class presets for rapid composition */
export const themeClasses = {
  page: 'min-h-screen bg-carbon text-slate-100 font-body antialiased',
  glassPanel:
    'backdrop-blur-glass bg-glass-surface border border-glass-border rounded-panel shadow-cyber',
  monoLabel: 'font-mono text-xs uppercase tracking-widest text-cyber-blue',
  statusRunning: 'text-neon-green font-mono',
  gridOverlay:
    'bg-[linear-gradient(rgba(0,255,255,0.04)_1px,transparent_1px),linear-gradient(90deg,rgba(0,255,255,0.04)_1px,transparent_1px)] bg-[size:24px_24px]',
} as const;

export default industry40Theme;
