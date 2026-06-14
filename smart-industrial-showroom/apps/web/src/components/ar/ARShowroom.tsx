/**
 * ARShowroom — Immersive 360° Panorama with Digital Twin Overlays
 * ================================================================
 * Renders AI-enhanced factory imagery as an inner-sphere skybox and anchors
 * TechGlassPanel widgets in 3D space (digital twin telemetry).
 *
 * Stack: @react-three/fiber + @react-three/drei + Three.js
 * Controls:
 *   - Desktop: drag to look (OrbitControls, rotation only)
 *   - Mobile:  DeviceOrientationControls when permission granted (WebXR-adjacent)
 *
 * Data flow:
 *   Upload → imageProcessor.service.ts → imageUrl prop → PanoramaSphere
 */

import { Suspense, useEffect, useMemo, useRef, useState } from 'react';
import { Canvas, useFrame, useThree } from '@react-three/fiber';
import {
  DeviceOrientationControls,
  Html,
  OrbitControls,
  PerspectiveCamera,
  useTexture,
} from '@react-three/drei';
import * as THREE from 'three';
import { TechGlassPanel } from '@/components/ui/TechGlassPanel';
import type { TelemetryRow } from '@/components/ui/TechGlassPanel';

// ---------------------------------------------------------------------------
// Public API
// ---------------------------------------------------------------------------

export interface ARAnchorConfig {
  id: string;
  position: [number, number, number];
  title: string;
  subtitle?: string;
  rows: TelemetryRow[];
  accentColor?: string;
}

export interface ARShowroomProps {
  /** Tech-enhanced panorama URL from ImageProcessorService */
  imageUrl: string;
  /** Optional custom anchors; defaults to CNC + Environment examples */
  anchors?: ARAnchorConfig[];
  /** Enable mobile gyroscope look-around */
  enableGyroscope?: boolean;
  className?: string;
}

/** Default digital-twin anchors per spec */
const DEFAULT_ANCHORS: ARAnchorConfig[] = [
  {
    id: 'anchor-machine-status',
    position: [2, 1, -3],
    title: 'Device: CNC Milling #01',
    subtitle: 'DIGITAL TWIN · LIVE',
    rows: [
      { label: 'Status', value: 'RUNNING', status: 'running' },
      { label: 'OEE', value: '92.5%', status: 'running' },
      { label: 'Spindle', value: '12,400 RPM', status: 'neutral' },
    ],
    accentColor: '#39ff14',
  },
  {
    id: 'anchor-environment',
    position: [-2, 1.5, -4],
    title: 'Environment Telemetry',
    subtitle: 'FACTORY IoT · ZONE-A',
    rows: [
      { label: 'Temp', value: '24°C', status: 'neutral' },
      { label: 'Humidity', value: '52%', status: 'neutral' },
      { label: 'PM2.5', value: 'Safe', status: 'running' },
    ],
    accentColor: '#00ffff',
  },
];

// ---------------------------------------------------------------------------
// Panorama sphere — projects enhanced photo as inner skybox
// ---------------------------------------------------------------------------

interface PanoramaSphereProps {
  imageUrl: string;
}

function PanoramaSphere({ imageUrl }: PanoramaSphereProps) {
  const texture = useTexture(imageUrl);

  useEffect(() => {
    texture.colorSpace = THREE.SRGBColorSpace;
    texture.minFilter = THREE.LinearFilter;
    texture.magFilter = THREE.LinearFilter;
  }, [texture]);

  return (
    <mesh scale={[-1, 1, 1]}>
      {/* Inverted sphere — camera sits at origin, sees inner surface */}
      <sphereGeometry args={[500, 64, 32]} />
      <meshBasicMaterial map={texture} side={THREE.BackSide} />
    </mesh>
  );
}

// ---------------------------------------------------------------------------
// Floating AR anchor — Html panel with sine-wave bobbing
// ---------------------------------------------------------------------------

interface FloatingARAnchorProps {
  anchor: ARAnchorConfig;
}

function FloatingARAnchor({ anchor }: FloatingARAnchorProps) {
  const groupRef = useRef<THREE.Group>(null);
  const baseY = anchor.position[1];
  const phase = useMemo(() => Math.random() * Math.PI * 2, []);

  useFrame(({ clock }) => {
    if (!groupRef.current) return;
    // Gentle hover bob — Industry 4.0 "floating hologram" feel
    const t = clock.getElapsedTime();
    groupRef.current.position.y = baseY + Math.sin(t * 1.8 + phase) * 0.12;
  });

  return (
    <group ref={groupRef} position={anchor.position}>
      {/* Glow point light at anchor origin */}
      <pointLight color={anchor.accentColor ?? '#00ffff'} intensity={0.6} distance={4} />

      {/* Always face camera — billboarding via drei's Html center */}
      <Html
        center
        distanceFactor={8}
        transform
        occlude={false}
        style={{ pointerEvents: 'auto' }}
      >
        <TechGlassPanel
          title={anchor.title}
          subtitle={anchor.subtitle}
          rows={anchor.rows}
          accentColor={anchor.accentColor}
          floating
        />
      </Html>
    </group>
  );
}

// ---------------------------------------------------------------------------
// Scene controls — desktop orbit + optional device orientation
// ---------------------------------------------------------------------------

interface SceneControlsProps {
  enableGyroscope: boolean;
}

function SceneControls({ enableGyroscope }: SceneControlsProps) {
  const { gl } = useThree();

  useEffect(() => {
    // Request device orientation permission on iOS 13+
    if (!enableGyroscope) return;

    const requestPermission = async () => {
      const DOE = DeviceOrientationEvent as unknown as {
        requestPermission?: () => Promise<'granted' | 'denied'>;
      };
      if (typeof DOE.requestPermission === 'function') {
        try {
          const state = await DOE.requestPermission();
          if (state !== 'granted') {
            console.warn('[ARShowroom] Gyroscope permission denied');
          }
        } catch (err) {
          console.warn('[ARShowroom] Gyroscope unavailable', err);
        }
      }
    };

    const handleClick = () => {
      void requestPermission();
      gl.domElement.removeEventListener('click', handleClick);
    };
    gl.domElement.addEventListener('click', handleClick);
    return () => gl.domElement.removeEventListener('click', handleClick);
  }, [enableGyroscope, gl.domElement]);

  return (
    <>
      <OrbitControls
        enableZoom={false}
        enablePan={false}
        rotateSpeed={-0.35}
        minPolarAngle={0.3}
        maxPolarAngle={Math.PI - 0.3}
      />
      {enableGyroscope && <DeviceOrientationControls />}
    </>
  );
}

// ---------------------------------------------------------------------------
// Loading fallback
// ---------------------------------------------------------------------------

function PanoramaLoader() {
  return (
    <Html center>
      <div className="rounded-panel border border-glass-border bg-glass-surface px-6 py-4 font-mono text-sm text-cyber-blue backdrop-blur-glass">
        Loading AR environment…
      </div>
    </Html>
  );
}

// ---------------------------------------------------------------------------
// Root component
// ---------------------------------------------------------------------------

export function ARShowroom({
  imageUrl,
  anchors = DEFAULT_ANCHORS,
  enableGyroscope = true,
  className = '',
}: ARShowroomProps) {
  const [gyroReady, setGyroReady] = useState(!enableGyroscope);

  return (
    <div
      className={`relative h-[min(72vh,640px)] w-full overflow-hidden rounded-panel border border-glass-border bg-carbon shadow-cyber ${className}`}
    >
      {/* HUD chrome */}
      <div className="pointer-events-none absolute inset-x-0 top-0 z-10 flex items-center justify-between px-4 py-3">
        <span className="font-mono text-[10px] uppercase tracking-[0.2em] text-cyber-blue">
          Smart Industrial Cloud Showroom
        </span>
        <span className="font-mono text-[10px] text-neon-green animate-pulse-neon rounded-full border border-neon-green/40 px-2 py-0.5">
          AR LIVE
        </span>
      </div>

      {!gyroReady && enableGyroscope && (
        <button
          type="button"
          className="absolute bottom-4 left-1/2 z-20 -translate-x-1/2 rounded-full border border-cyber-blue bg-cyber/80 px-4 py-2 font-mono text-xs text-cyber-blue backdrop-blur-glass"
          onClick={() => setGyroReady(true)}
        >
          Tap to enable gyroscope look-around
        </button>
      )}

      <Canvas
        gl={{ antialias: true, alpha: false }}
        dpr={[1, 2]}
        onCreated={({ gl }) => {
          gl.setClearColor('#0a192f');
        }}
      >
        <PerspectiveCamera makeDefault fov={75} near={0.1} far={1000} position={[0, 0, 0.1]} />

        <Suspense fallback={<PanoramaLoader />}>
          <PanoramaSphere imageUrl={imageUrl} />
        </Suspense>

        {anchors.map((anchor) => (
          <FloatingARAnchor key={anchor.id} anchor={anchor} />
        ))}

        <SceneControls enableGyroscope={enableGyroscope && gyroReady} />
      </Canvas>

      {/* Interaction hint */}
      <p className="pointer-events-none absolute bottom-3 right-4 z-10 font-mono text-[10px] text-slate-500">
        Drag to look · Scroll anchors in view
      </p>
    </div>
  );
}

export default ARShowroom;
