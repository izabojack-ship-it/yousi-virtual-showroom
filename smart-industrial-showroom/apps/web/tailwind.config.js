/** @type {import('tailwindcss').Config} */
import { industry40Theme } from './src/theme/theme.config.ts';

export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        carbon: industry40Theme.colors.background.primary,
        cyber: industry40Theme.colors.background.secondary,
        elevated: industry40Theme.colors.background.elevated,
        'cyber-blue': industry40Theme.colors.accent.cyberBlue,
        'neon-green': industry40Theme.colors.accent.neonGreen,
        alert: industry40Theme.colors.accent.alert,
        'glass-surface': industry40Theme.colors.glass.surface,
        'glass-border': industry40Theme.colors.glass.border,
      },
      fontFamily: {
        mono: industry40Theme.typography.mono.split(',').map((f) => f.trim().replace(/'/g, '')),
        display: industry40Theme.typography.display.split(',').map((f) => f.trim().replace(/'/g, '')),
        body: industry40Theme.typography.body.split(',').map((f) => f.trim().replace(/'/g, '')),
      },
      borderRadius: {
        panel: industry40Theme.radius.panel,
      },
      boxShadow: {
        cyber: industry40Theme.shadow.cyber,
        neon: industry40Theme.shadow.neonGreen,
        panel: industry40Theme.shadow.panel,
      },
      backdropBlur: {
        glass: industry40Theme.blur.glass,
      },
      animation: {
        float: `float ${industry40Theme.animation.floatDuration} ease-in-out infinite`,
        'pulse-neon': `pulseNeon ${industry40Theme.animation.pulseDuration} ease-in-out infinite`,
        scanline: 'scanline 4s linear infinite',
      },
      keyframes: {
        float: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: `translateY(-${industry40Theme.animation.floatDistance})` },
        },
        pulseNeon: {
          '0%, 100%': { opacity: '1', boxShadow: '0 0 8px rgba(57, 255, 20, 0.6)' },
          '50%': { opacity: '0.85', boxShadow: '0 0 20px rgba(57, 255, 20, 0.3)' },
        },
        scanline: {
          '0%': { backgroundPosition: '0 0' },
          '100%': { backgroundPosition: '0 100%' },
        },
      },
    },
  },
  plugins: [],
};
