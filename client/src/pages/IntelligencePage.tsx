import { useState, useEffect } from 'react';
import { analyzeIntelligence, getIntelligenceSummary, getAnomalies } from '../services/api';
import type { Page } from '../App';

interface Summary {
  ndvi_mean: number | null;
  ndvi_health_class: string | null;
  ndwi_mean: number | null;
  ndwi_water_class: string | null;
  risk_score: number | null;
  risk_label: string | null;
  anomaly_count: number;
  change_percentage: number | null;
  ndvi_change: number | null;
  band_mapping_warning: string | null;
  last_analyzed_at: string | null;
}

interface Anomaly {
  id: number;
  anomaly_type: string;
  severity: string;
  confidence: number | null;
  description: string | null;
  area_km2: number | null;
}

const SEVERITY_COLOR: Record<string, string> = {
  critical: 'text-red-alert border-red-alert/30 bg-red-alert/10',
  high: 'text-amber-warn border-amber-warn/30 bg-amber-warn/10',
  medium: 'text-blue-electric border-blue-electric/30 bg-blue-electric/10',
  low: 'text-slate-400 border-navy-500/40 bg-navy-700',
};

function MetricCard({
  label, value, unit, sub, color = 'text-blue-electric', icon,
}: {
  label: string; value: string | number | null; unit?: string;
  sub?: string; color?: string; icon: string;
}) {
  return (
    <div className="bg-navy-800 border border-navy-500/40 rounded-xl p-4 flex flex-col gap-2 hover:border-blue-electric/30 transition-all">
      <div className="flex items-center gap-2">
        <span className="text-xs font-mono text-cyan-glow/70">{icon}</span>
        <span className="text-[10px] font-mono text-slate-500 uppercase tracking-widest">{label}</span>
      </div>
      <div className={`font-display font-700 text-2xl ${color}`}>
        {value !== null && value !== undefined ? (
          <>{typeof value === 'number' ? value.toFixed(3) : value}<span className="text-sm ml-1">{unit}</span></>
        ) : (
          <span className="text-slate-600 text-base">-</span>
        )}
      </div>
      {sub && <div className="text-[10px] font-mono text-slate-500">{sub}</div>}
    </div>
  );
}

export default function IntelligencePage({
  objectName, onNavigate,
}: {
  objectName: string | null;
  onNavigate: (p: Page) => void;
}) {
  const [summary, setSummary] = useState<Summary | null>(null);
  const [anomalies, setAnomalies] = useState<Anomaly[]>([]);
  const [loading, setLoading] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [analyzed, setAnalyzed] = useState(false);
  const PROJECT_ID = 1;

  useEffect(() => { loadData(); }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [s, a] = await Promise.allSettled([
        getIntelligenceSummary(PROJECT_ID),
        getAnomalies(PROJECT_ID),
      ]);
      if (s.status === 'fulfilled') setSummary(s.value);
      if (a.status === 'fulfilled') setAnomalies(a.value);
    } catch { /* no data yet */ } finally { setLoading(false); }
  };

  const handleAnalyze = async () => {
    if (!objectName) { setError('Upload a GeoTIFF first from the Dashboard.'); return; }
    setAnalyzing(true); setError(null);
    try {
      await analyzeIntelligence(PROJECT_ID, objectName);
      setAnalyzed(true);
      await loadData();
    } catch (e: any) {
      setError(e?.response?.data?.detail || 'Analysis failed. Check the backend.');
    } finally { setAnalyzing(false); }
  };

  const riskColor = summary?.risk_score == null ? 'text-slate-500'
    : summary.risk_score >= 75 ? 'text-red-alert'
    : summary.risk_score >= 50 ? 'text-amber-warn' : 'text-emerald-signal';

  const ndviChangeColor = summary?.ndvi_change == null ? 'text-slate-500'
    : summary.ndvi_change < -0.1 ? 'text-red-alert'
    : summary.ndvi_change > 0.05 ? 'text-emerald-signal' : 'text-slate-300';

  return (
    <div className="h-full overflow-y-auto bg-navy-900">
      <div className="max-w-6xl mx-auto p-6 space-y-6">
        <div className="flex items-center justify-between flex-wrap gap-3">
          <div>
            <div className="text-[10px] font-mono text-cyan-glow uppercase tracking-widest mb-1">
              Geospatial Intelligence Layer
            </div>
            <h1 className="font-display font-700 text-2xl text-white">Satellite Intelligence</h1>
            <p className="text-sm text-slate-400 mt-1">
              Prototype analytical indicators - not validated scientific measurements
            </p>
          </div>
          <div className="flex items-center gap-3">
            {summary?.last_analyzed_at && (
              <span className="text-[10px] font-mono text-slate-500">
                Last: {new Date(summary.last_analyzed_at).toLocaleString()}
              </span>
            )}
            <button
              onClick={handleAnalyze}
              disabled={analyzing || !objectName}
              className="px-4 py-2 rounded-xl bg-cyan-glow/15 border border-cyan-glow/40 text-sm text-cyan-glow font-display font-600 hover:bg-cyan-glow/25 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {analyzing ? (
                <span className="flex items-center gap-2">
                  <span className="w-3 h-3 border-2 border-cyan-glow/30 border-t-cyan-glow rounded-full animate-spin" />
                  Analyzing...
                </span>
              ) : 'Run Intelligence Analysis'}
            </button>
          </div>
        </div>

        {summary?.band_mapping_warning && (
          <div className="px-4 py-3 rounded-xl bg-amber-warn/10 border border-amber-warn/30 text-xs text-amber-warn">
            Band Mapping Warning: {summary.band_mapping_warning}
          </div>
        )}
        {error && (
          <div className="px-4 py-3 rounded-xl bg-red-alert/10 border border-red-alert/30 text-xs text-red-alert">
            Error: {error}
          </div>
        )}
        {analyzed && (
          <div className="px-4 py-3 rounded-xl bg-emerald-signal/10 border border-emerald-signal/30 text-xs text-emerald-signal">
            Intelligence analysis complete.
          </div>
        )}

        {loading && (
          <div className="flex items-center justify-center py-12">
            <span className="w-6 h-6 border-2 border-cyan-glow/30 border-t-cyan-glow rounded-full animate-spin" />
            <span className="ml-3 text-sm text-slate-400">Loading intelligence data...</span>
          </div>
        )}

        {!loading && (
          <>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
              <MetricCard label="NDVI Mean" value={summary?.ndvi_mean ?? null}
                sub={summary?.ndvi_health_class || 'Not analyzed'} color="text-emerald-signal" icon="VEG" />
              <MetricCard label="NDWI Mean" value={summary?.ndwi_mean ?? null}
                sub={summary?.ndwi_water_class || 'Not analyzed'} color="text-cyan-glow" icon="H2O" />
              <MetricCard label="GeoRisk Index"
                value={summary?.risk_score != null ? Math.round(summary.risk_score) : null}
                unit={summary?.risk_label ? `- ${summary.risk_label}` : ''}
                color={riskColor} sub="Prototype indicator" icon="RSK" />
              <MetricCard label="Anomalies" value={summary !== null ? summary.anomaly_count : null}
                sub="Detected zones" color="text-purple-ai" icon="DET" />
              <MetricCard label="NDVI Change" value={summary?.ndvi_change ?? null}
                sub={summary?.change_percentage != null
                  ? `${summary.change_percentage.toFixed(1)}% area changed` : 'No change data'}
                color={ndviChangeColor} icon="TRD" />
            </div>

            {!summary && (
              <div className="text-center py-16 border border-dashed border-navy-500/40 rounded-xl">
                <div className="font-display font-600 text-white text-lg mb-2">No Intelligence Data Yet</div>
                <p className="text-sm text-slate-400 mb-5">
                  {objectName 
                    ? "Your GeoTIFF is ready. Click below to run the intelligence analysis."
                    : "Upload a GeoTIFF from the Dashboard, then click Run Intelligence Analysis."}
                </p>
                {objectName ? (
                  <button
                    onClick={handleAnalyze}
                    disabled={analyzing}
                    className="px-5 py-2.5 rounded-xl bg-cyan-glow text-navy-900 text-sm font-display font-700 hover:bg-cyan-glow/90 transition-colors"
                  >
                    {analyzing ? "Analyzing..." : "Run Intelligence Analysis"}
                  </button>
                ) : (
                  <button
                    onClick={() => onNavigate('dashboard')}
                    className="px-5 py-2.5 rounded-xl bg-blue-electric text-white text-sm font-display font-600 hover:bg-blue-600 transition-colors"
                  >
                    Go to Dashboard
                  </button>
                )}
              </div>
            )}

            {anomalies.length > 0 && (
              <div>
                <div className="text-xs font-mono text-slate-500 uppercase tracking-widest mb-3">
                  Detected Anomaly Zones ({anomalies.length})
                </div>
                <div className="grid md:grid-cols-2 gap-3">
                  {anomalies.map((a) => (
                    <div key={a.id} className={`p-4 rounded-xl border ${SEVERITY_COLOR[a.severity] || SEVERITY_COLOR.low}`}>
                      <div className="flex items-start justify-between gap-2 mb-2">
                        <div>
                          <div className="text-xs font-mono font-600 uppercase tracking-wide">
                            {a.anomaly_type.replace(/_/g, ' ')}
                          </div>
                          <div className="text-[10px] font-mono mt-0.5">
                            Severity: {a.severity} - Confidence: {a.confidence !== null ? `${Math.round((a.confidence ?? 0) * 100)}%` : '-'}
                          </div>
                        </div>
                        {a.area_km2 !== null && (
                          <span className="text-[10px] font-mono shrink-0">~{a.area_km2.toFixed(1)} km2</span>
                        )}
                      </div>
                      {a.description && (
                        <p className="text-[11px] leading-relaxed opacity-80 mt-1">{a.description}</p>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {summary && (
              <div className="grid grid-cols-3 gap-3 pt-2">
                <button onClick={() => onNavigate('risk-analysis')}
                  className="py-3 rounded-xl bg-navy-800 border border-amber-warn/30 hover:border-amber-warn/60 text-sm font-display font-600 text-slate-300 hover:text-white transition-all">
                  Full Risk Analysis
                </button>
                <button onClick={() => onNavigate('change-detection')}
                  className="py-3 rounded-xl bg-navy-800 border border-cyan-glow/30 hover:border-cyan-glow/60 text-sm font-display font-600 text-slate-300 hover:text-white transition-all">
                  Change Detection
                </button>
                <button onClick={() => onNavigate('geoassist')}
                  className="py-3 rounded-xl bg-navy-800 border border-purple-ai/30 hover:border-purple-ai/60 text-sm font-display font-600 text-slate-300 hover:text-white transition-all">
                  Ask GeoAssist
                </button>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
