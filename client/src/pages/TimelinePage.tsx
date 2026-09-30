import { useState, useEffect } from 'react';
import { getSpectralIndices } from '../services/api';

interface SpectralRecord {
  id: number;
  observation_id: number;
  ndvi_mean: number | null;
  ndvi_health_class: string | null;
  ndwi_mean: number | null;
  ndwi_water_class: string | null;
  band_mapping_warning: string | null;
  created_at: string | null;
}

const PROJECT_ID = 1;

function Sparkline({ values, color = '#3b8fe8' }: { values: (number | null)[]; color?: string }) {
  const valid = values.filter((v): v is number => v !== null);
  if (valid.length < 2) return <div className="h-8 flex items-center text-[10px] font-mono text-slate-600">No data</div>;
  const mn = Math.min(...valid);
  const mx = Math.max(...valid);
  const rng = mx - mn || 0.001;
  const w = 120; const h = 32;
  const pts = valid.map((v, i) => `${(i / (valid.length - 1)) * w},${h - ((v - mn) / rng) * (h - 4)}`).join(' ');
  return (
    <svg viewBox={`0 0 ${w} ${h}`} className="w-32 h-8">
      <polyline points={pts} fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

export default function TimelinePage() {
  const [records, setRecords] = useState<SpectralRecord[]>([]);
  const [selected, setSelected] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    getSpectralIndices(PROJECT_ID)
      .then((data) => {
        setRecords(data);
        if (data.length > 0) setSelected(data[0].id);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const ndviValues = records.map((r) => r.ndvi_mean);
  const ndwiValues = records.map((r) => r.ndwi_mean);
  const selectedRecord = records.find((r) => r.id === selected) || null;

  return (
    <div className="h-full overflow-y-auto bg-navy-900">
      <div className="max-w-5xl mx-auto p-4 sm:p-6 space-y-4 sm:space-y-6">
        <div>
          <div className="text-[10px] font-mono text-blue-electric uppercase tracking-widest mb-1">
            Temporal Intelligence
          </div>
          <h1 className="font-display font-700 text-2xl text-white">Observation Timeline</h1>
          <p className="text-sm text-slate-400 mt-1">Historical spectral index records per analysis run.</p>
        </div>

        {loading && (
          <div className="flex items-center justify-center py-12">
            <span className="w-6 h-6 border-2 border-blue-electric/30 border-t-blue-electric rounded-full animate-spin" />
            <span className="ml-3 text-sm text-slate-400">Loading timeline...</span>
          </div>
        )}

        {!loading && records.length === 0 && (
          <div className="text-center py-20 border border-dashed border-navy-500/40 rounded-xl">
            <div className="font-display font-600 text-white text-lg mb-2">No Timeline Data</div>
            <p className="text-sm text-slate-400">
              Run Intelligence Analysis from the Intelligence page to populate the timeline.
            </p>
          </div>
        )}

        {!loading && records.length > 0 && (
          <>
            <div className="grid md:grid-cols-2 gap-4">
              <div className="bg-navy-800 border border-navy-500/40 rounded-xl p-4">
                <div className="text-[10px] font-mono text-slate-500 uppercase tracking-widest mb-2">NDVI Trend</div>
                <Sparkline values={ndviValues} color="#10d98b" />
                <div className="text-[10px] font-mono text-slate-500 mt-1">{records.length} observations</div>
              </div>
              <div className="bg-navy-800 border border-navy-500/40 rounded-xl p-4">
                <div className="text-[10px] font-mono text-slate-500 uppercase tracking-widest mb-2">NDWI Trend</div>
                <Sparkline values={ndwiValues} color="#06c8d5" />
                <div className="text-[10px] font-mono text-slate-500 mt-1">
                  {records.filter((r) => r.ndwi_mean !== null).length} with NDWI
                </div>
              </div>
            </div>

            <div className="space-y-2">
              {records.map((r) => {
                const isSelected = r.id === selected;
                const date = r.created_at ? new Date(r.created_at) : null;
                return (
                  <button
                    key={r.id}
                    onClick={() => setSelected(r.id)}
                    className={`w-full flex items-start gap-4 p-4 rounded-xl border text-left transition-all ${
                      isSelected ? 'bg-blue-electric/10 border-blue-electric/40' : 'bg-navy-800 border-navy-500/40 hover:border-blue-electric/20'
                    }`}
                  >
                    <div className={`w-3 h-3 rounded-full border-2 mt-1 shrink-0 ${isSelected ? 'bg-blue-electric border-blue-electric' : 'bg-navy-600 border-navy-500'}`} />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between gap-2 flex-wrap">
                        <span className="text-xs font-mono text-slate-300">
                          {date ? date.toLocaleString() : 'Unknown date'}
                        </span>
                        <span className="text-[10px] font-mono text-slate-500">Obs #{r.observation_id}</span>
                      </div>
                      <div className="flex items-center gap-4 mt-1 flex-wrap">
                        {r.ndvi_mean !== null && (
                          <span className="text-[11px] font-mono text-emerald-signal">
                            NDVI {r.ndvi_mean.toFixed(3)} - {r.ndvi_health_class}
                          </span>
                        )}
                        {r.ndwi_mean !== null && (
                          <span className="text-[11px] font-mono text-cyan-glow">
                            NDWI {r.ndwi_mean.toFixed(3)}
                          </span>
                        )}
                      </div>
                      {r.band_mapping_warning && (
                        <div className="text-[10px] font-mono text-amber-warn/70 mt-1 truncate">
                          Warning: {r.band_mapping_warning}
                        </div>
                      )}
                    </div>
                  </button>
                );
              })}
            </div>

            {selectedRecord && (
              <div className="bg-navy-800 border border-blue-electric/30 rounded-xl p-5">
                <div className="text-[10px] font-mono text-blue-electric uppercase tracking-widest mb-4">
                  Selected Observation Detail
                </div>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm font-mono">
                  {([
                    { label: 'NDVI Mean', value: selectedRecord.ndvi_mean?.toFixed(4), color: 'text-emerald-signal' },
                    { label: 'NDWI Mean', value: selectedRecord.ndwi_mean?.toFixed(4), color: 'text-cyan-glow' },
                    { label: 'Veg. Class', value: selectedRecord.ndvi_health_class || '-', color: 'text-slate-300' },
                    { label: 'Water Class', value: selectedRecord.ndwi_water_class || '-', color: 'text-slate-300' },
                  ] as const).map((item) => (
                    <div key={item.label}>
                      <div className="text-[10px] text-slate-500 uppercase tracking-widest mb-1">{item.label}</div>
                      <div className={item.color}>{item.value || '-'}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
