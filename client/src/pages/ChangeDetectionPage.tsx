import { useState } from 'react';
import { runChangeDetection } from '../services/api';

interface ChangeResult {
  ndvi_change: number | null;
  ndwi_change: number | null;
  change_percentage: number | null;
  change_type: string | null;
  change_categories: Array<{ type: string; label: string; magnitude: number }> | null;
  confidence: number | null;
  hotspots: Array<{ ndvi_change: number; severity: string }> | null;
  summary: string | null;
}

const PROJECT_ID = 1;

function StatBox({ label, value, unit, color = 'text-slate-200' }: {
  label: string; value: string | number | null; unit?: string; color?: string;
}) {
  return (
    <div className="bg-navy-700 border border-navy-500/40 rounded-xl p-4 text-center">
      <div className="text-[10px] font-mono text-slate-500 uppercase tracking-widest mb-1">{label}</div>
      <div className={`font-display font-700 text-xl ${color}`}>
        {value !== null && value !== undefined ? (
          <>{typeof value === 'number' ? value.toFixed(3) : value}<span className="text-xs ml-1">{unit}</span></>
        ) : '-'}
      </div>
    </div>
  );
}

export default function ChangeDetectionPage() {
  const [beforeName, setBeforeName] = useState('');
  const [afterName, setAfterName] = useState('');
  const [result, setResult] = useState<ChangeResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleCompare = async () => {
    if (!beforeName.trim() || !afterName.trim()) {
      setError('Enter both MinIO object names (e.g. projects/1/inputs/filename.tif).');
      return;
    }
    setLoading(true); setError(null);
    try {
      const data = await runChangeDetection(PROJECT_ID, beforeName.trim(), afterName.trim());
      setResult(data);
    } catch (e: any) {
      setError(e?.response?.data?.detail || 'Change detection failed.');
    } finally { setLoading(false); }
  };

  const ndviChange = result?.ndvi_change ?? null;
  const changeDir = ndviChange === null ? null : ndviChange < -0.05 ? 'decrease' : ndviChange > 0.05 ? 'increase' : 'stable';

  return (
    <div className="h-full overflow-y-auto bg-navy-900">
      <div className="max-w-5xl mx-auto p-4 sm:p-6 space-y-4 sm:space-y-6">
        <div>
          <div className="text-[10px] font-mono text-cyan-glow uppercase tracking-widest mb-1">
            Temporal Intelligence
          </div>
          <h1 className="font-display font-700 text-2xl text-white">Change Detection</h1>
          <p className="text-sm text-slate-400 mt-1">
            Compare two satellite observations to detect spectral change.
            Uses original Sentinel-2 data, not SRCNN output.
          </p>
        </div>

        <div className="grid md:grid-cols-2 gap-4">
          <div className="bg-navy-800 border border-navy-500/40 rounded-xl p-5 space-y-3">
            <div className="text-sm font-display font-600 text-slate-300">Observation A (Earlier)</div>
            <label className="block text-[10px] font-mono text-slate-500 uppercase tracking-widest">
              MinIO Object Name
            </label>
            <input
              value={beforeName}
              onChange={(e) => setBeforeName(e.target.value)}
              placeholder="projects/1/inputs/before.tif"
              className="w-full bg-navy-700 border border-navy-500/40 rounded-lg px-3 py-2.5 text-sm text-slate-200 placeholder-slate-600 focus:outline-none focus:border-blue-electric/50"
            />
          </div>
          <div className="bg-navy-800 border border-blue-electric/30 rounded-xl p-5 space-y-3">
            <div className="text-sm font-display font-600 text-slate-300">Observation B (Later)</div>
            <label className="block text-[10px] font-mono text-slate-500 uppercase tracking-widest">
              MinIO Object Name
            </label>
            <input
              value={afterName}
              onChange={(e) => setAfterName(e.target.value)}
              placeholder="projects/1/inputs/after.tif"
              className="w-full bg-navy-700 border border-navy-500/40 rounded-lg px-3 py-2.5 text-sm text-slate-200 placeholder-slate-600 focus:outline-none focus:border-blue-electric/50"
            />
          </div>
        </div>

        <div className="flex items-center gap-4">
          <button
            onClick={handleCompare}
            disabled={loading}
            className="px-6 py-3 rounded-xl bg-blue-electric text-white font-display font-700 text-sm hover:bg-blue-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? (
              <span className="flex items-center gap-2">
                <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                Comparing...
              </span>
            ) : 'Compare Observations'}
          </button>
          {error && <span className="text-xs text-red-alert">{error}</span>}
        </div>

        {result && (
          <div className="space-y-5">
            <div className={`px-4 py-3 rounded-xl border text-sm ${
              changeDir === 'decrease' ? 'bg-red-alert/10 border-red-alert/30 text-red-alert'
              : changeDir === 'increase' ? 'bg-emerald-signal/10 border-emerald-signal/30 text-emerald-signal'
              : 'bg-navy-800 border-navy-500/40 text-slate-300'
            }`}>
              {result.summary || 'Analysis complete.'}
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <StatBox label="NDVI Change" value={result.ndvi_change}
                color={ndviChange === null ? 'text-slate-500' : ndviChange < -0.05 ? 'text-red-alert' : ndviChange > 0.05 ? 'text-emerald-signal' : 'text-slate-300'} />
              <StatBox label="NDWI Change" value={result.ndwi_change}
                color={result.ndwi_change !== null && result.ndwi_change < -0.05 ? 'text-amber-warn' : 'text-slate-300'} />
              <StatBox label="Area Changed"
                value={result.change_percentage !== null ? result.change_percentage.toFixed(1) : null}
                unit="%"
                color={result.change_percentage && result.change_percentage > 20 ? 'text-amber-warn' : 'text-slate-300'} />
              <StatBox label="Confidence"
                value={result.confidence !== null ? `${Math.round((result.confidence ?? 0) * 100)}` : null}
                unit="%" color="text-blue-electric" />
            </div>

            {result.change_categories && result.change_categories.length > 0 && (
              <div>
                <div className="text-[10px] font-mono text-slate-500 uppercase tracking-widest mb-2">
                  Change Categories
                </div>
                <div className="flex flex-wrap gap-2">
                  {result.change_categories.map((cat, i) => (
                    <span key={i} className="px-3 py-1.5 rounded-full text-xs font-mono border border-navy-500/40 bg-navy-800 text-slate-300">
                      {cat.label} ({cat.magnitude.toFixed(3)})
                    </span>
                  ))}
                </div>
              </div>
            )}

            {result.hotspots && result.hotspots.length > 0 && (
              <div>
                <div className="text-[10px] font-mono text-slate-500 uppercase tracking-widest mb-2">
                  Top Change Hotspots
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full text-xs font-mono">
                    <thead>
                      <tr className="border-b border-navy-500/40 text-slate-500">
                        <th className="text-left pb-2 pr-4">#</th>
                        <th className="text-left pb-2 pr-4">NDVI Change</th>
                        <th className="text-left pb-2">Severity</th>
                      </tr>
                    </thead>
                    <tbody>
                      {result.hotspots.slice(0, 8).map((h, i) => (
                        <tr key={i} className="border-b border-navy-500/20">
                          <td className="py-1.5 pr-4 text-slate-500">{i + 1}</td>
                          <td className={`py-1.5 pr-4 font-600 ${h.ndvi_change < 0 ? 'text-red-alert' : 'text-emerald-signal'}`}>
                            {h.ndvi_change > 0 ? '+' : ''}{h.ndvi_change.toFixed(3)}
                          </td>
                          <td className={`py-1.5 ${h.severity === 'high' ? 'text-amber-warn' : h.severity === 'medium' ? 'text-blue-electric' : 'text-slate-400'}`}>
                            {h.severity}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            <div className="text-[10px] font-mono text-slate-600 px-3 py-2 rounded border border-navy-500/20">
              These are prototype analytical estimates, not scientifically validated measurements.
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
