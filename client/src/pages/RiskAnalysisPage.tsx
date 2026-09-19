import { useState, useEffect } from 'react';
import { getRiskAssessment } from '../services/api';
import type { Page } from '../App';

interface RiskData {
  score: number;
  label: string;
  confidence: number | null;
  component_scores: Record<string, number> | null;
  weighted_scores: Record<string, number> | null;
  weights: Record<string, number> | null;
  explanations: Record<string, string> | null;
  methodology_version: string | null;
  created_at: string | null;
  weather_data: any;
}

const LABEL_COLOR: Record<string, string> = {
  Low: 'text-emerald-signal', Moderate: 'text-blue-electric',
  High: 'text-amber-warn', Critical: 'text-red-alert',
};

const LABEL_BG: Record<string, string> = {
  Low: 'from-emerald-signal/20 to-emerald-signal/5 border-emerald-signal/40',
  Moderate: 'from-blue-electric/20 to-blue-electric/5 border-blue-electric/40',
  High: 'from-amber-warn/20 to-amber-warn/5 border-amber-warn/40',
  Critical: 'from-red-alert/20 to-red-alert/5 border-red-alert/40',
};

const COMPONENT_META: Record<string, { label: string; icon: string }> = {
  vegetation: { label: 'Vegetation Stress', icon: 'VEG' },
  water:      { label: 'Water Stress', icon: 'H2O' },
  change:     { label: 'Temporal Change', icon: 'CHG' },
  weather:    { label: 'Weather Anomaly', icon: 'WTH' },
  anomaly:    { label: 'Anomaly Density', icon: 'ANO' },
};

const PROJECT_ID = 1;

function GaugeArc({ score }: { score: number }) {
  const r = 80;
  const cx = 100; const cy = 120;
  const startAngle = 210;
  const sweepAngle = 240;
  const toRad = (a: number) => (a * Math.PI) / 180;
  const arcX = (a: number) => cx + r * Math.cos(toRad(a));
  const arcY = (a: number) => cy + r * Math.sin(toRad(a));
  const describeArc = (s: number, e: number) => {
    const sx = arcX(s); const sy = arcY(s);
    const ex = arcX(e); const ey = arcY(e);
    const large = e - s > 180 ? 1 : 0;
    return `M ${sx} ${sy} A ${r} ${r} 0 ${large} 1 ${ex} ${ey}`;
  };
  const endAngle = startAngle + (score / 100) * sweepAngle;
  const color = score >= 75 ? '#ef4444' : score >= 50 ? '#f59e0b' : score >= 25 ? '#3b8fe8' : '#10d98b';
  return (
    <svg viewBox="0 0 200 160" className="w-48 h-36 mx-auto">
      <path d={describeArc(startAngle, startAngle + sweepAngle)} fill="none" stroke="#1e3a5f" strokeWidth="14" strokeLinecap="round" />
      <path d={describeArc(startAngle, endAngle)} fill="none" stroke={color} strokeWidth="14" strokeLinecap="round" className="transition-all duration-700" />
      <text x={cx} y={cy - 10} textAnchor="middle" fill={color} fontSize="28" fontFamily="Exo 2, sans-serif" fontWeight="700">
        {Math.round(score)}
      </text>
    </svg>
  );
}

export default function RiskAnalysisPage({ onNavigate }: { onNavigate: (p: Page) => void }) {
  const [risk, setRisk] = useState<RiskData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => { loadRisk(); }, []);

  const loadRisk = async () => {
    setLoading(true); setError(null);
    try {
      const data = await getRiskAssessment(PROJECT_ID);
      setRisk(data);
    } catch (e: any) {
      if (e?.response?.status === 404) {
        setError('No risk assessment found. Run Intelligence Analysis from the Intelligence page first.');
      } else {
        setError(e?.response?.data?.detail || 'Failed to load risk assessment.');
      }
    } finally { setLoading(false); }
  };

  return (
    <div className="h-full overflow-y-auto bg-navy-900">
      <div className="max-w-5xl mx-auto p-6 space-y-6">
        <div>
          <div className="text-[10px] font-mono text-amber-warn uppercase tracking-widest mb-1">
            Decision Intelligence Layer
          </div>
          <h1 className="font-display font-700 text-2xl text-white">GeoRisk Analysis</h1>
          <p className="text-sm text-slate-400 mt-1">
            Prototype GeoRisk Indicator - analytical estimate, not a validated risk assessment system.
          </p>
        </div>

        {loading && (
          <div className="flex items-center justify-center py-12">
            <span className="w-6 h-6 border-2 border-amber-warn/30 border-t-amber-warn rounded-full animate-spin" />
            <span className="ml-3 text-sm text-slate-400">Loading risk assessment...</span>
          </div>
        )}

        {error && (
          <div className="px-4 py-3 rounded-xl bg-amber-warn/10 border border-amber-warn/30 text-sm text-amber-warn">
            {error}
            {error.includes('Intelligence Analysis') && (
              <button onClick={() => onNavigate('intelligence')} className="ml-3 underline text-blue-electric">
                Go to Intelligence
              </button>
            )}
          </div>
        )}

        {risk && (
          <>
            <div className={`bg-gradient-to-br ${LABEL_BG[risk.label] || LABEL_BG.Moderate} border rounded-2xl p-6 flex flex-col md:flex-row items-center gap-6`}>
              <div className="text-center">
                <GaugeArc score={risk.score} />
                <div className={`font-display font-700 text-xl mt-1 ${LABEL_COLOR[risk.label] || 'text-slate-300'}`}>
                  {risk.label}
                </div>
                <div className="text-[10px] font-mono text-slate-500 mt-0.5">
                  Confidence: {risk.confidence !== null ? `${Math.round((risk.confidence ?? 0) * 100)}%` : '-'}
                </div>
              </div>
              <div className="flex-1 space-y-2">
                <div className="text-xs font-mono text-slate-400 uppercase tracking-widest mb-3">
                  GeoRisk Prototype Index: {Math.round(risk.score)} / 100
                </div>
                {risk.weights && risk.component_scores && risk.weighted_scores && (
                  Object.entries(risk.component_scores).map(([key, rawScore]) => {
                    const meta = COMPONENT_META[key] || { label: key, icon: 'N/A' };
                    const weight = (risk.weights![key] ?? 0) * 100;
                    const weighted = risk.weighted_scores![key] ?? 0;
                    return (
                      <div key={key}>
                        <div className="flex items-center justify-between text-xs mb-1">
                          <span className="font-mono text-slate-400">{meta.icon} {meta.label}</span>
                          <span className="font-mono text-slate-500">
                            {Math.round(rawScore)} raw - {weight.toFixed(0)}% weight
                            {' -> '}<span className="text-white">{weighted.toFixed(1)} pts</span>
                          </span>
                        </div>
                        <div className="h-1.5 rounded-full bg-navy-600 overflow-hidden">
                          <div className="h-full rounded-full bg-amber-warn/60 transition-all duration-700" style={{ width: `${rawScore}%` }} />
                        </div>
                      </div>
                    );
                  })
                )}
              </div>
            </div>

            {risk.explanations && (
              <div>
                <div className="text-xs font-mono text-slate-500 uppercase tracking-widest mb-3">
                  Component Explanations
                </div>
                <div className="grid md:grid-cols-2 gap-3">
                  {Object.entries(risk.explanations).map(([key, explanation]) => {
                    const meta = COMPONENT_META[key] || { label: key, icon: 'N/A' };
                    return (
                      <div key={key} className="bg-navy-800 border border-navy-500/40 rounded-xl p-4">
                        <div className="flex items-center gap-2 mb-2">
                          <span className="text-xs font-mono text-cyan-glow">{meta.icon}</span>
                          <span className="text-xs font-mono text-slate-400 uppercase tracking-wide">{meta.label}</span>
                          {risk.weighted_scores && (
                            <span className="ml-auto text-xs font-mono text-amber-warn">
                              {(risk.weighted_scores[key] ?? 0).toFixed(1)} pts
                            </span>
                          )}
                        </div>
                        <p className="text-xs text-slate-300 leading-relaxed">{explanation}</p>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {risk.weather_data?.available && risk.weather_data.factors?.length > 0 && (
              <div className="bg-navy-800 border border-navy-500/40 rounded-xl p-4">
                <div className="text-[10px] font-mono text-slate-500 uppercase tracking-widest mb-2">
                  Weather Indicators (Open-Meteo 7-day forecast)
                </div>
                <div className="flex flex-wrap gap-2">
                  {risk.weather_data.factors.map((f: string, i: number) => (
                    <span key={i} className="px-2 py-1 rounded text-xs font-mono bg-navy-700 border border-navy-500/40 text-slate-300">
                      {f}
                    </span>
                  ))}
                </div>
              </div>
            )}

            <div className="text-[10px] font-mono text-slate-600 text-center py-2">
              GeoRisk Index is a prototype indicator only. Weights: Vegetation 30% - Water 20% - Change 25% - Weather 15% - Anomaly 10%.
              {risk.created_at && ` Assessed: ${new Date(risk.created_at).toLocaleString()}`}
            </div>
          </>
        )}
      </div>
    </div>
  );
}
