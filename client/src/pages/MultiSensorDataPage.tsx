import React from 'react';

function MetricCard({ label, value, unit, color = "text-blue-electric" }: { label: string; value: string | number; unit?: string; color?: string }) {
  return (
    <div className="bg-navy-800 border border-navy-500/40 rounded-xl p-4 flex flex-col gap-2 hover:border-blue-electric/30 transition-all">
      <div className="text-[10px] font-mono text-slate-500 uppercase tracking-widest">{label}</div>
      <div className={`font-display font-700 text-2xl ${color}`}>
        {value} <span className="text-sm">{unit}</span>
      </div>
    </div>
  );
}

export default function MultiSensorDataPage({ sensorData, objectName }: { sensorData: any; objectName: string | null }) {
  if (!sensorData) {
    return (
      <div className="size-full flex flex-col p-8 relative items-center justify-center text-center">
        <h2 className="text-2xl font-display font-600 text-slate-100 mb-4">No Sensor Data Available</h2>
        <p className="text-slate-400 max-w-md">
          Go to the Dashboard and use the <strong>Fetch Latest Imagery</strong> panel to download data from a sensor. 
          The detailed statistics and metadata will appear here automatically!
        </p>
      </div>
    );
  }

  const { sensor, raw } = sensorData;

  const renderContent = () => {
    if (sensor === "sentinel-1" && raw.analysis) {
      const a = raw.analysis;
      return (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <MetricCard label="VV Mean" value={a.vv_mean?.toFixed(2)} unit="dB" color="text-amber-warn" />
          <MetricCard label="VH Mean" value={a.vh_mean?.toFixed(2)} unit="dB" color="text-emerald-signal" />
          <MetricCard label="Water Fraction" value={(a.potential_water_fraction * 100)?.toFixed(1)} unit="%" color="text-cyan-glow" />
          <MetricCard label="Est. Water Area" value={a.potential_water_area_km2?.toFixed(2)} unit="km²" color="text-blue-electric" />
          <div className="col-span-2 md:col-span-4 mt-4 bg-navy-800 border border-navy-500/40 p-4 rounded-xl">
            <h4 className="text-xs uppercase text-slate-400 tracking-widest mb-2 font-mono">Analysis Confidence</h4>
            <div className={`text-lg font-600 ${a.confidence === 'High' ? 'text-red-alert' : a.confidence === 'Medium' ? 'text-amber-warn' : 'text-slate-400'}`}>
              {a.confidence} Confidence for Flooding
            </div>
            {a.warnings && a.warnings.length > 0 && (
              <ul className="mt-2 text-sm text-slate-400 list-disc list-inside">
                {a.warnings.map((w: string, i: number) => <li key={i}>{w}</li>)}
              </ul>
            )}
          </div>
        </div>
      );
    }

    if (sensor === "copernicus-dem" && raw.stats) {
      const s = raw.stats;
      return (
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          <MetricCard label="Mean Elevation" value={s.elevation_mean?.toFixed(1) || "-"} unit="m" color="text-emerald-signal" />
          <MetricCard label="Max Elevation" value={s.elevation_max?.toFixed(1) || "-"} unit="m" color="text-slate-300" />
          <MetricCard label="Min Elevation" value={s.elevation_min?.toFixed(1) || "-"} unit="m" color="text-slate-300" />
          <MetricCard label="Steep Slopes" value={((s.steep_slope_fraction || 0) * 100).toFixed(1)} unit="%" color="text-red-alert" />
          <MetricCard label="Low-Lying Areas" value={((s.low_lying_fraction || 0) * 100).toFixed(1)} unit="%" color="text-cyan-glow" />
        </div>
      );
    }

    if (sensor === "gee-composite") {
      return (
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          <MetricCard label="Time Window" value={raw.date_range} unit="" color="text-purple-ai" />
          <MetricCard label="Scenes Combined" value={raw.scene_count} unit="scenes" color="text-blue-electric" />
          <MetricCard label="Valid (Cloud-Free)" value={raw.valid_pixel_percentage?.toFixed(1)} unit="%" color="text-emerald-signal" />
          
          <div className="col-span-2 md:col-span-3 mt-4 bg-navy-800 border border-navy-500/40 p-4 rounded-xl">
            <h4 className="text-xs uppercase text-slate-400 tracking-widest mb-2 font-mono">Bounding Box</h4>
            <div className="text-sm font-mono text-cyan-glow bg-navy-900 p-2 rounded-lg inline-block">
              {raw.bounds ? `[${raw.bounds.map((n: number) => n.toFixed(4)).join(", ")}]` : "Unknown"}
            </div>
            {raw.warnings && raw.warnings.length > 0 && (
              <ul className="mt-4 text-sm text-slate-400 list-disc list-inside">
                {raw.warnings.map((w: string, i: number) => <li key={i}>{w}</li>)}
              </ul>
            )}
          </div>
        </div>
      );
    }

    return (
      <div className="p-4 bg-navy-800 border border-navy-500/40 rounded-xl text-slate-400 font-mono text-sm">
        <pre className="whitespace-pre-wrap">{JSON.stringify(raw, null, 2)}</pre>
      </div>
    );
  };

  const getSensorName = (id: string) => {
    switch(id) {
      case "sentinel-1": return "Radar Sentinel-1 (SAR)";
      case "copernicus-dem": return "Copernicus DEM (Terrain)";
      case "gee-composite": return "Cloud-Masked Composite (GEE)";
      case "sentinel-2": return "Optical Sentinel-2 (CDSE)";
      default: return id;
    }
  };

  return (
    <div className="size-full flex flex-col p-8 relative overflow-y-auto">
      <div className="max-w-4xl w-full mx-auto space-y-8">
        
        <header className="flex flex-col gap-2 border-b border-navy-500/30 pb-6">
          <h1 className="text-4xl font-display font-700 tracking-tight text-slate-100 flex items-center gap-3">
            <span className="text-purple-ai">📡</span> Sensor Data
          </h1>
          <p className="text-slate-400 max-w-2xl">
            Raw intelligence and background statistics extracted dynamically from the fetched imagery.
          </p>
        </header>

        <div className="bg-navy-900 border-l-4 border-purple-ai/50 p-6 rounded-r-xl relative overflow-hidden">
          <div className="absolute top-0 right-0 p-4 opacity-5 pointer-events-none">
            <span className="text-8xl">🛰️</span>
          </div>
          <div className="relative z-10">
            <h3 className="text-xs uppercase font-mono tracking-widest text-slate-500 mb-1">Active Sensor</h3>
            <div className="text-2xl font-display font-600 text-slate-100">{getSensorName(sensor)}</div>
            {objectName && <div className="text-sm font-mono text-cyan-glow mt-2">File: {objectName.split('/').pop()}</div>}
          </div>
        </div>

        <section className="space-y-4">
          <h2 className="text-lg font-display font-600 text-slate-200">Extracted Metrics</h2>
          {renderContent()}
        </section>

      </div>
    </div>
  );
}
