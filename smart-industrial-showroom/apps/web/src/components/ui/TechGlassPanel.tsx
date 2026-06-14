import type { ReactNode } from 'react';
import { industry40Theme } from '@/theme/theme.config';

/** Single telemetry row inside a glass panel */
export interface TelemetryRow {
  label: string;
  value: string;
  /** Highlight value as live / OK status */
  status?: 'running' | 'warning' | 'neutral';
}

export interface TechGlassPanelProps {
  /** Panel header — e.g. "CNC Milling #01" */
  title: string;
  /** Optional subtitle or device ID */
  subtitle?: string;
  /** Structured data rows (preferred for dashboards) */
  rows?: TelemetryRow[];
  /** Free-form children for custom AR content */
  children?: ReactNode;
  /** Accent stripe color — defaults to cyber blue */
  accentColor?: string;
  /** Enable gentle vertical bobbing (used by AR anchors) */
  floating?: boolean;
  /** Compact mode for distant 3D anchors */
  compact?: boolean;
  className?: string;
}

/**
 * TechGlassPanel — Industry 4.0 Glassmorphism UI Shell
 * -----------------------------------------------------
 * Hosts AR digital-twin overlays inside the 360° panorama. Uses semi-transparent
 * blur, electric-blue borders, and neon status indicators to mimic a SCADA/HMI panel.
 */
export function TechGlassPanel({
  title,
  subtitle,
  rows = [],
  children,
  accentColor = industry40Theme.colors.accent.cyberBlue,
  floating = false,
  compact = false,
  className = '',
}: TechGlassPanelProps) {
  const padding = compact ? 'p-3' : 'p-4';
  const minWidth = compact ? 'min-w-[180px]' : 'min-w-[240px]';

  return (
    <div
      className={[
        'relative overflow-hidden rounded-panel border backdrop-blur-glass',
        padding,
        minWidth,
        'select-none pointer-events-auto',
        floating ? 'animate-float' : '',
        className,
      ].join(' ')}
      style={{
        background: industry40Theme.colors.glass.surface,
        borderColor: industry40Theme.colors.glass.border,
        boxShadow: industry40Theme.shadow.cyber,
        fontFamily: industry40Theme.typography.body,
      }}
      role="region"
      aria-label={title}
    >
      {/* Accent top stripe — factory "live data" indicator */}
      <div
        className="absolute inset-x-0 top-0 h-[2px]"
        style={{
          background: `linear-gradient(90deg, transparent, ${accentColor}, transparent)`,
          boxShadow: `0 0 12px ${accentColor}`,
        }}
      />

      {/* Subtle scanline overlay for control-room aesthetic */}
      <div
        className="pointer-events-none absolute inset-0 opacity-[0.04] animate-scanline"
        style={{
          backgroundImage:
            'repeating-linear-gradient(0deg, #00ffff 0px, transparent 2px, transparent 4px)',
          backgroundSize: '100% 8px',
        }}
      />

      {/* Header */}
      <div className="relative mb-3 border-b border-glass-border pb-2">
        <h3
          className="font-display text-sm font-bold tracking-wide text-slate-100"
          style={{ fontFamily: industry40Theme.typography.display }}
        >
          {title}
        </h3>
        {subtitle && (
          <p
            className="mt-0.5 font-mono text-[10px] uppercase tracking-widest text-cyber-blue/80"
            style={{ fontFamily: industry40Theme.typography.mono }}
          >
            {subtitle}
          </p>
        )}
      </div>

      {/* Telemetry rows */}
      {rows.length > 0 && (
        <dl className="relative space-y-2">
          {rows.map((row) => (
            <div key={row.label} className="flex items-center justify-between gap-4">
              <dt
                className="font-mono text-[10px] uppercase tracking-wider text-slate-400"
                style={{ fontFamily: industry40Theme.typography.mono }}
              >
                {row.label}
              </dt>
              <dd
                className={[
                  'font-mono text-xs font-semibold tabular-nums',
                  row.status === 'running'
                    ? 'text-neon-green animate-pulse-neon rounded px-1.5 py-0.5'
                    : row.status === 'warning'
                      ? 'text-alert'
                      : 'text-slate-200',
                ].join(' ')}
                style={{ fontFamily: industry40Theme.typography.mono }}
              >
                {row.value}
              </dd>
            </div>
          ))}
        </dl>
      )}

      {children && <div className="relative mt-2 text-xs text-slate-300">{children}</div>}

      {/* Corner bracket decorations — HUD framing */}
      <span
        className="pointer-events-none absolute left-1 top-1 h-3 w-3 border-l-2 border-t-2"
        style={{ borderColor: accentColor }}
      />
      <span
        className="pointer-events-none absolute bottom-1 right-1 h-3 w-3 border-b-2 border-r-2"
        style={{ borderColor: accentColor }}
      />
    </div>
  );
}

export default TechGlassPanel;
