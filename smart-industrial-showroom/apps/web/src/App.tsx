import { useCallback, useState } from 'react';
import { ARShowroom } from '@/components/ar/ARShowroom';
import { themeClasses } from '@/theme/theme.config';
import './index.css';

const DEMO_IMAGE =
  'https://pannellum.org/images/alma.jpg';

const PROCESSOR_URL = '/api/v1/process/url';

function App() {
  const [imageUrl, setImageUrl] = useState(DEMO_IMAGE);
  const [sourceUrl, setSourceUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleProcess = useCallback(async () => {
    if (!sourceUrl.trim()) {
      setError('Paste a factory photo URL first');
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(PROCESSOR_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ imageUrl: sourceUrl.trim(), provider: 'mock' }),
      });
      const json = (await res.json()) as {
        success: boolean;
        enhancedImageUrl?: string;
        error?: string;
      };
      if (!json.success || !json.enhancedImageUrl) {
        throw new Error(json.error ?? 'Processing failed');
      }
      setImageUrl(json.enhancedImageUrl);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  }, [sourceUrl]);

  return (
    <div className={`${themeClasses.page} ${themeClasses.gridOverlay}`}>
      <header className="border-b border-glass-border bg-cyber/60 px-6 py-4 backdrop-blur-glass">
        <h1 className="font-display text-xl font-bold text-cyber-blue">
          智慧工業雲端展間系統
        </h1>
        <p className="mt-1 font-mono text-xs text-slate-400">
          Upload → AI Tech-ify → 360° AR Panorama + Digital Twin Overlays
        </p>
      </header>

      <main className="mx-auto max-w-6xl space-y-6 p-6">
        <section className={`${themeClasses.glassPanel} p-4`}>
          <label className="font-mono text-xs uppercase tracking-widest text-cyber-blue">
            Factory photo URL
          </label>
          <div className="mt-2 flex flex-col gap-3 sm:flex-row">
            <input
              type="url"
              value={sourceUrl}
              onChange={(e) => setSourceUrl(e.target.value)}
              placeholder="https://your-cdn.com/factory/raw.jpg"
              className="flex-1 rounded border border-glass-border bg-carbon px-3 py-2 font-mono text-sm text-slate-200 outline-none focus:border-cyber-blue"
            />
            <button
              type="button"
              onClick={handleProcess}
              disabled={loading}
              className="rounded border border-cyber-blue bg-cyber-blue/10 px-4 py-2 font-mono text-sm text-cyber-blue hover:bg-cyber-blue/20 disabled:opacity-50"
            >
              {loading ? 'Processing…' : 'AI Tech-ify'}
            </button>
          </div>
          {error && <p className="mt-2 font-mono text-xs text-alert">{error}</p>}
        </section>

        <ARShowroom imageUrl={imageUrl} enableGyroscope />
      </main>
    </div>
  );
}

export default App;
