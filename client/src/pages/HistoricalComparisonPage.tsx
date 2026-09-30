import { useState } from "react";
import type { Page } from "../App";
import { runHistoricalAnalysis } from "../services/api";

const AVAILABLE_YEARS = [1990, 1995, 2000, 2005, 2010, 2015, 2020, 2023];

export default function HistoricalComparisonPage({
  onNavigate,
}: {
  onNavigate: (p: Page) => void;
}) {
  const [lat, setLat] = useState(() => localStorage.getItem("pickedLat") || "28.6139");
  const [lon, setLon] = useState(() => localStorage.getItem("pickedLon") || "77.2090");
  const [bufferKm, setBufferKm] = useState(5);
  const [selectedYears, setSelectedYears] = useState<Set<number>>(new Set([2000, 2010, 2020]));
  
  const [isBusy, setIsBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [results, setResults] = useState<any | null>(null);

  const toggleYear = (yr: number) => {
    setSelectedYears(prev => {
      const next = new Set(prev);
      if (next.has(yr)) next.delete(yr);
      else next.add(yr);
      return next;
    });
  };

  const handleRun = async () => {
    if (selectedYears.size === 0) {
      setError("Please select at least one year.");
      return;
    }
    const latN = parseFloat(lat);
    const lonN = parseFloat(lon);
    
    setIsBusy(true);
    setError(null);
    setResults(null);
    
    try {
      const result = await runHistoricalAnalysis(1, {
        latitude: latN,
        longitude: lonN,
        buffer_km: bufferKm,
        years: Array.from(selectedYears).sort(),
      });
      
      // Since it's a background task, in a real app we'd poll checkJobStatus.
      // For the hackathon frontend, if it finishes synchronously or we just want to pretend it's done:
      // Actually, our API returns job_id. We must poll it.
      import("../services/api").then(api => {
        const poll = setInterval(async () => {
          try {
            const status = await api.checkTaskStatus(result.job_id);
            if (status.status === "completed") {
              clearInterval(poll);
              setResults(status.result || status); // Depending on how backend serializes it
              setIsBusy(false);
            } else if (status.status === "failed") {
              clearInterval(poll);
              setError("Historical analysis failed.");
              setIsBusy(false);
            }
          } catch (e) {
            clearInterval(poll);
            setIsBusy(false);
          }
        }, 3000);
      });
      
    } catch (e: any) {
      setError(e?.message || "Failed to start analysis");
      setIsBusy(false);
    }
  };

  return (
    <div className="h-screen bg-navy-950 text-white flex flex-col font-sans relative overflow-hidden">
      {/* Navbar */}
      <header className="flex items-center justify-between px-6 py-4 border-b border-navy-800 bg-navy-900/50 backdrop-blur-md z-10">
        <div className="flex items-center gap-3">
          <button 
            onClick={() => onNavigate("dashboard")}
            className="p-2 hover:bg-navy-800 rounded-lg transition-colors text-slate-400 hover:text-white"
          >
            ← Back
          </button>
          <h1 className="text-xl font-bold bg-gradient-to-r from-emerald-400 to-cyan-400 bg-clip-text text-transparent">
            Historical Comparison
          </h1>
        </div>
      </header>

      <main className="flex-1 overflow-auto p-4 sm:p-6 z-10 relative">
        <div className="max-w-6xl mx-auto space-y-6">
          <div className="bg-navy-900/80 border border-navy-700 rounded-xl p-6 shadow-2xl">
            <h2 className="text-lg font-bold text-white mb-4">Analysis Parameters</h2>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
              <div>
                <label className="text-xs text-slate-400 mb-1 block">Latitude</label>
                <input 
                  type="number" value={lat} onChange={(e) => setLat(e.target.value)}
                  className="w-full bg-navy-800 border border-navy-600 rounded px-3 py-2 text-sm"
                />
              </div>
              <div>
                <label className="text-xs text-slate-400 mb-1 block">Longitude</label>
                <input 
                  type="number" value={lon} onChange={(e) => setLon(e.target.value)}
                  className="w-full bg-navy-800 border border-navy-600 rounded px-3 py-2 text-sm"
                />
              </div>
              <div>
                <label className="text-xs text-slate-400 mb-1 block">Buffer (km)</label>
                <input 
                  type="number" value={bufferKm} onChange={(e) => setBufferKm(+e.target.value)}
                  className="w-full bg-navy-800 border border-navy-600 rounded px-3 py-2 text-sm"
                />
              </div>
            </div>

            <div className="mb-6">
              <label className="text-xs text-slate-400 mb-2 block">Target Years (Landsat Multi-decadal)</label>
              <div className="flex flex-wrap gap-2">
                {AVAILABLE_YEARS.map(yr => (
                  <label 
                    key={yr} 
                    className={`flex items-center gap-2 px-4 py-2 rounded-lg cursor-pointer border transition-colors ${
                      selectedYears.has(yr) 
                        ? "bg-emerald-500/20 border-emerald-500/50 text-emerald-300"
                        : "bg-navy-800 border-navy-600 text-slate-400 hover:border-slate-500"
                    }`}
                  >
                    <input 
                      type="checkbox" className="hidden" 
                      checked={selectedYears.has(yr)} onChange={() => toggleYear(yr)} 
                    />
                    <span>{yr}</span>
                  </label>
                ))}
              </div>
            </div>

            {error && (
              <div className="text-red-400 text-sm mb-4 p-3 bg-red-500/10 border border-red-500/30 rounded">
                {error}
              </div>
            )}

            <button 
              onClick={handleRun}
              disabled={isBusy}
              className="w-full md:w-auto px-8 py-3 bg-gradient-to-r from-emerald-600 to-cyan-600 hover:from-emerald-500 hover:to-cyan-500 text-white font-bold rounded-lg shadow-lg disabled:opacity-50"
            >
              {isBusy ? "Analyzing (Fetching Landsat)..." : "Run Historical Analysis"}
            </button>
          </div>

          {/* Results Area */}
          {results && results.results && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {results.results.map((r: any) => (
                <div key={r.year} className="bg-navy-900/60 border border-navy-700/50 rounded-xl overflow-hidden shadow-lg">
                  <div className="p-3 bg-navy-800/80 flex justify-between items-center border-b border-navy-700">
                    <h3 className="font-bold text-lg text-white">{r.year}</h3>
                    <span className="text-xs px-2 py-1 bg-navy-950 rounded text-slate-300">{r.mission}</span>
                  </div>
                  
                  {r.error ? (
                    <div className="p-6 text-center text-amber-400/80 text-sm">
                      {r.error}
                    </div>
                  ) : (
                    <>
                      {r.thumbnail ? (
                        <div className="aspect-square bg-navy-950 relative border-b border-navy-800">
                           <img 
                             src={`http://localhost:8000/api/v1/map/1/outputs/${r.thumbnail.split('/').pop()}/thumbnail`} 
                             alt={`NDVI ${r.year}`}
                             className="w-full h-full object-cover"
                           />
                        </div>
                      ) : (
                        <div className="aspect-square bg-navy-950 flex items-center justify-center text-slate-500 text-sm border-b border-navy-800">
                          No Preview Available
                        </div>
                      )}
                      
                      <div className="p-4 space-y-2 text-sm">
                        <div className="flex justify-between">
                          <span className="text-slate-400">Mean NDVI</span>
                          <span className="text-cyan-400 font-medium">{r.ndvi_mean?.toFixed(3) || "—"}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-slate-400">Median NDVI</span>
                          <span className="text-cyan-400 font-medium">{r.ndvi_median?.toFixed(3) || "—"}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-slate-400">Valid Pixels</span>
                          <span className="text-emerald-400 font-medium">{r.valid_pixel_percentage?.toFixed(1) || 0}%</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-slate-400">Scenes Used</span>
                          <span className="text-slate-200">{r.scene_count}</span>
                        </div>
                        
                        {r.warnings && r.warnings.length > 0 && (
                          <div className="mt-3 text-xs text-amber-400 bg-amber-400/10 p-2 rounded">
                            {r.warnings[0]}
                          </div>
                        )}
                      </div>
                    </>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
