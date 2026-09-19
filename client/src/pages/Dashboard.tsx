import { useState, useRef, useCallback, useEffect } from "react";
import ExportModal from "../components/ExportModal";
import MapViewer from "../components/MapViewer";
import FetchRealtimePanel from "../components/FetchRealtimePanel";
import type { Page } from "../App";
import {
  uploadGeoTIFF, triggerSuperResolution, checkJobStatus,
  fetchValidationMetrics, getIntelligenceSummary,
  type RealtimeFetchResult, type FetchAndProcessResult,
} from "../services/api";

const layers = [
  { id: "enhanced", label: "Enhanced Image", color: "bg-blue-electric" },
  { id: "original", label: "Original Image", color: "bg-slate-500" },
];

export default function Dashboard({ 
  onNavigate, 
  objectName, 
  setObjectName 
}: { 
  onNavigate: (p: Page) => void;
  objectName: string | null;
  setObjectName: (name: string | null) => void;
}) {
  const [activeLayers, setActiveLayers] = useState(new Set(["enhanced", "original"]));
  const [showExport, setShowExport] = useState(false);
  
  // API Integration states
  const [isUploading, setIsUploading] = useState(false);
  const [isRunning, setIsRunning] = useState(false);
  const [status, setStatus] = useState<string>("idle");
  
  // Dynamic pipeline steps
  const [pipeline, setPipeline] = useState([
    { label: "Upload GeoTIFF", done: false },
    { label: "Geo Preprocessing", done: false },
    { label: "Band Alignment", done: false },
    { label: "Super Resolution", done: false },
    { label: "Geo-Consistency Check", done: false },
    { label: "Validation", done: false },
  ]);

  // Dynamic metrics from the backend
  const [metricCards, setMetricCards] = useState([
    { label: "PSNR", value: "—", unit: "", color: "text-blue-electric", bar: 0 },
    { label: "SSIM", value: "—", unit: "", color: "text-cyan-glow", bar: 0 },
    { label: "Geo-Consistency", value: "—", unit: "", color: "text-emerald-signal", bar: 0 },
    { label: "Avg Confidence", value: "—", unit: "", color: "text-purple-ai", bar: 0 },
    { label: "Edge Accuracy", value: "—", unit: "", color: "text-amber-warn", bar: 0 },
  ]);

  // Uploaded file info
  const [uploadedFilename, setUploadedFilename] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // ─── Mode Toggle: Upload vs Fetch Realtime ─────────────────────────────────
  const [inputMode, setInputMode] = useState<"upload" | "realtime">("upload");

  // ─── Realtime Fetch State ──────────────────────────────────────────────────
  const [realtimeBounds, setRealtimeBounds] = useState<[[number, number], [number, number]] | null>(null);
  const [pickMode, setPickMode] = useState(false);
  const [pickedLat, setPickedLat] = useState<number | null>(null);
  const [pickedLon, setPickedLon] = useState<number | null>(null);
  const [acquisitionDate, setAcquisitionDate] = useState<string | null>(null);

  const handleRealtimeFetchSuccess = (result: RealtimeFetchResult) => {
    setObjectName(result.object_name);
    setUploadedFilename(result.filename);
    setAcquisitionDate(result.acquisition_date);
    if (result.bounds) {
      const [w, s, e, n] = result.bounds;
      setRealtimeBounds([[s, w], [n, e]]);
    }
  };

  const handleRealtimeProcessStarted = (result: FetchAndProcessResult) => {
    setObjectName(result.object_name);
    setUploadedFilename(result.object_name.split("/").pop() || "realtime.tif");
    setAcquisitionDate(result.acquisition_date);
    setStatus("processing");
    setIsRunning(true);
    setPipeline(prev => prev.map((s, i) => ({ ...s, done: i <= 2 })));
    const interval = setInterval(async () => {
      try {
        const js = await checkJobStatus(result.sr_job_id);
        setStatus(js.status);
        if (js.status === "completed") {
          clearInterval(interval);
          setIsRunning(false);
          setPipeline(prev => prev.map(s => ({ ...s, done: true })));
        } else if (js.status === "failed") {
          clearInterval(interval);
          setIsRunning(false);
        }
      } catch { clearInterval(interval); }
    }, 3000);
  };

  // Intelligence summary
  const [intelSummary, setIntelSummary] = useState<any>(null);

  useEffect(() => {
    getIntelligenceSummary(1).then(setIntelSummary).catch(() => {});
  }, []);

  // Load metrics when enhancement completes
  useEffect(() => {
    if (status === "completed") {
      fetchValidationMetrics(1)
        .then((m) => {
          setMetricCards([
            { label: "PSNR", value: `${m.psnr}`, unit: "dB", color: "text-blue-electric", bar: Math.round((m.psnr / 40) * 100) },
            { label: "SSIM", value: `${m.ssim}`, unit: "", color: "text-cyan-glow", bar: Math.round(m.ssim * 100) },
            { label: "Geo-Consistency", value: `${Math.round(m.geo_consistency * 100)}`, unit: "%", color: "text-emerald-signal", bar: Math.round(m.geo_consistency * 100) },
            { label: "Avg Confidence", value: `${Math.round(m.avg_confidence * 100)}`, unit: "%", color: "text-purple-ai", bar: Math.round(m.avg_confidence * 100) },
            { label: "Edge Accuracy", value: `${Math.round(m.edge_accuracy * 100)}`, unit: "%", color: "text-amber-warn", bar: Math.round(m.edge_accuracy * 100) },
          ]);
        })
        .catch(() => {});
    }
  }, [status]);

  const toggleLayer = (id: string) => {
    setActiveLayers((s) => {
      const n = new Set(s);
      n.has(id) ? n.delete(id) : n.add(id);
      return n;
    });
  };

  const handleUploadClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    
    setIsUploading(true);
    setStatus("idle");
    setUploadedFilename(file.name);

    // Update pipeline
    setPipeline(prev => prev.map((s, i) => ({ ...s, done: i === 0 })));
    
    try {
      const result = await uploadGeoTIFF(1, file);
      setObjectName(result.object_name);

      setPipeline(prev => prev.map((s, i) => ({ ...s, done: i <= 1 })));
    } catch (error) {
      console.error("Upload failed", error);
      alert("Failed to upload GeoTIFF.");
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  const handleRunEnhancement = async () => {
    if (!objectName) {
      alert("Please upload a GeoTIFF first.");
      return;
    }
    
    setIsRunning(true);
    setStatus("processing");
    
    // Mark band alignment as done
    setPipeline(prev => prev.map((s, i) => ({ ...s, done: i <= 2 })));
    
    try {
      const job = await triggerSuperResolution(1, objectName);
      console.log(`Super Resolution started! Job ID: ${job.job_id}`);
      
      const interval = setInterval(async () => {
        const jobStatus = await checkJobStatus(job.job_id);
        setStatus(jobStatus.status);
        if (jobStatus.status === "completed") {
          clearInterval(interval);
          setIsRunning(false);
          // Mark all pipeline steps as done
          setPipeline(prev => prev.map(s => ({ ...s, done: true })));
          console.log("Super Resolution Completed!");
        } else if (jobStatus.status === "failed") {
          clearInterval(interval);
          setIsRunning(false);
          setPipeline(prev => prev.map((s, i) => ({ ...s, done: i <= 2 ? true : false })));
          console.error("Super Resolution Failed");
        }
      }, 2000);
      
      } catch (error) {
      console.error("SR failed", error);
      setIsRunning(false);
      setStatus("failed");
      alert("Failed to trigger super resolution.");
    }
  };

  const [selectedBbox, setSelectedBbox] = useState<[number, number, number, number] | null>(null);
  
  const handleFetchGEE = async () => {
    if (!selectedBbox) return;
    try {
      setIsUploading(true);
      // We don't have api.ts fully typed for this yet, so we'll use raw fetch
      const res = await fetch('http://localhost:8000/api/v1/projects/1/gee-fetch', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ bbox: selectedBbox, max_cloud_cover: 20 })
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || "Failed to fetch from GEE");
      }
      alert("GEE Fetch started! The Super Resolution pipeline will trigger automatically when it finishes downloading.");
      setIsUploading(false);
      setSelectedBbox(null); // hide the button
    } catch (e: any) {
      setIsUploading(false);
      alert(e.message);
    }
  };

  return (
    <div className="flex flex-col h-full overflow-hidden bg-navy-900">
      {/* Hidden file input */}
      <input 
        type="file" 
        ref={fileInputRef} 
        onChange={handleFileChange} 
        className="hidden" 
        accept=".tif,.tiff" 
      />
      
      {/* Top bar */}
      <div className="shrink-0 bg-navy-800 border-b border-navy-500/40 px-4 py-2.5 flex items-center justify-between gap-4">
        <div className="flex items-center gap-3 flex-wrap">
          <span className="font-display font-600 text-sm text-white">
            {uploadedFilename || "No File Loaded"}
          </span>
          {acquisitionDate && (
            <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-cyan-500/10 border border-cyan-500/30 text-cyan-400">
              Acquired {acquisitionDate.slice(0, 10)}
            </span>
          )}
          {objectName && !acquisitionDate && (
            <>
              {["Sentinel-2", "4× Upscale", "CRS Preserved"].map((chip) => (
                <span key={chip} className="px-2 py-0.5 rounded text-[10px] font-mono bg-navy-700 border border-navy-500/40 text-slate-400">
                  {chip}
                </span>
              ))}
            </>
          )}
          {objectName && (
            <span className={`px-2 py-0.5 rounded text-[10px] font-mono border ${
              status === "completed" ? "bg-emerald-signal/10 border-emerald-signal/30 text-emerald-signal" :
              status === "processing" ? "bg-amber-warn/10 border-amber-warn/30 text-amber-warn" :
              "bg-navy-700 border-navy-500/40 text-slate-400"
            }`}>
              {status === "completed" ? "✓ Enhanced" : status === "processing" ? "⟳ Processing" : "Pending"}
            </span>
          )}
        </div>
        <div className="flex items-center gap-2 shrink-0">
          {/* Mode Toggle */}
          <div className="flex items-center rounded-lg border border-navy-600 overflow-hidden text-xs">
            <button
              onClick={() => { setInputMode("upload"); setPickMode(false); }}
              className={`px-3 py-1.5 transition-colors ${inputMode === "upload" ? "bg-navy-600 text-white" : "text-slate-400 hover:text-slate-200"}`}
            >
              Upload File
            </button>
            <button
              onClick={() => setInputMode("realtime")}
              className={`px-3 py-1.5 transition-colors ${inputMode === "realtime" ? "bg-emerald-700 text-white" : "text-slate-400 hover:text-slate-200"}`}
            >
              🛰 Fetch Realtime
            </button>
          </div>

          {inputMode === "upload" && (
            <button
              onClick={handleUploadClick}
              disabled={isUploading}
              className="px-3 py-1.5 rounded-lg border border-navy-500/50 text-xs text-slate-400 hover:text-slate-200 hover:border-slate-500 transition-colors disabled:opacity-50"
            >
              {isUploading ? "Uploading..." : "Upload GeoTIFF"}
            </button>
          )}
          {inputMode === "realtime" && (
            <button
              onClick={() => setPickMode(p => !p)}
              className={`px-3 py-1.5 rounded-lg text-xs border transition-colors ${pickMode ? "bg-cyan-600 border-cyan-500 text-white" : "bg-navy-700 border-navy-600 text-slate-300 hover:text-white"}`}
            >
              {pickMode ? "📍 Click map to pick" : "Pick Location"}
            </button>
          )}
          <button
            onClick={handleRunEnhancement}
            disabled={isRunning || !objectName || inputMode === "realtime"}
            className="px-3 py-1.5 rounded-lg bg-blue-electric/15 border border-blue-electric/40 text-xs text-blue-electric hover:bg-blue-electric/25 transition-colors font-display font-600 disabled:opacity-50 disabled:cursor-not-allowed"
            title={inputMode === "realtime" ? 'Use "Fetch & Process" in the panel' : undefined}
          >
            {isRunning ? "Running..." : "Run Enhancement"}
          </button>
          {selectedBbox && (
            <button onClick={handleFetchGEE} disabled={isUploading}
              className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-medium transition-colors disabled:opacity-50"
            >
              {isUploading ? "Fetching..." : "Fetch Live from GEE"}
            </button>
          )}
          <button
            onClick={() => setShowExport(true)}
            disabled={status !== "completed"}
            className="px-3 py-1.5 bg-navy-800 hover:bg-navy-700 text-white border border-navy-700 rounded-lg text-xs font-medium transition-colors disabled:opacity-50 flex items-center gap-1.5"
          >
            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" /></svg>
            Export
          </button>
        </div>
      </div>

      {/* Main area */}
      <div className="flex-1 flex overflow-hidden">
        {/* Map area */}
        <div className="flex-1 flex flex-col min-w-0">
          {/* Map */}
          <div className="flex-1 relative border border-navy-800 rounded-lg overflow-hidden shadow-2xl">
            {/* Map Placeholder or Actual Component */}
            <MapViewer 
              activeLayers={activeLayers} 
              isCompleted={status === "completed"}
              objectName={objectName}
              onBboxSelect={inputMode === "upload" ? (bbox) => setSelectedBbox(bbox) : undefined}
              pickMode={inputMode === "realtime" && pickMode}
              onLocationPick={(lat, lon) => { setPickedLat(lat); setPickedLon(lon); }}
              realtimeBounds={realtimeBounds}
            />  </div>

          {/* Layer toggles */}
          <div className="shrink-0 bg-navy-800 border-t border-navy-500/40 px-4 py-2 flex items-center gap-3 flex-wrap">
            <span className="text-[10px] font-mono text-slate-500 uppercase tracking-widest">Layers</span>
            {layers.map((l) => (
              <button
                key={l.id}
                onClick={() => toggleLayer(l.id)}
                className={`flex items-center gap-1.5 px-2.5 py-1 rounded text-xs font-medium transition-all ${
                  activeLayers.has(l.id)
                    ? "bg-navy-700 text-slate-200 border border-navy-500/60"
                    : "text-slate-600 border border-transparent hover:text-slate-400"
                }`}
              >
                <span className={`w-1.5 h-1.5 rounded-full ${activeLayers.has(l.id) ? l.color : "bg-slate-700"}`} />
                {l.label}
              </button>
            ))}
          </div>

          {/* Intelligence quick-summary strip */}
          {intelSummary && (
            <div className="shrink-0 bg-navy-800/60 border-t border-navy-500/30 px-4 py-2 flex items-center gap-4 flex-wrap">
              <span className="text-[10px] font-mono text-slate-500 uppercase tracking-widest shrink-0">Intelligence</span>
              {intelSummary.ndvi_mean !== null && (
                <span className="text-[11px] font-mono text-emerald-signal">
                  NDVI {intelSummary.ndvi_mean?.toFixed(3)} · {intelSummary.ndvi_health_class}
                </span>
              )}
              {intelSummary.risk_score !== null && (
                <span className={`text-[11px] font-mono font-600 ${
                  intelSummary.risk_score >= 75 ? "text-red-alert" :
                  intelSummary.risk_score >= 50 ? "text-amber-warn" : "text-emerald-signal"
                }`}>
                  GeoRisk {Math.round(intelSummary.risk_score)} · {intelSummary.risk_label}
                </span>
              )}
              {intelSummary.anomaly_count > 0 && (
                <span className="text-[11px] font-mono text-purple-ai">
                  {intelSummary.anomaly_count} anomal{intelSummary.anomaly_count === 1 ? "y" : "ies"}
                </span>
              )}
              <div className="ml-auto flex items-center gap-2 shrink-0">
                <button
                  onClick={() => onNavigate("intelligence")}
                  className="px-2.5 py-1 rounded text-[10px] font-mono border border-cyan-glow/30 text-cyan-glow hover:bg-cyan-glow/10 transition-colors"
                >Intelligence →</button>
                <button
                  onClick={() => onNavigate("risk-analysis")}
                  className="px-2.5 py-1 rounded text-[10px] font-mono border border-amber-warn/30 text-amber-warn hover:bg-amber-warn/10 transition-colors"
                >Risk Analysis →</button>
              </div>
            </div>
          )}

          {/* Metrics row — dynamic from API */}
          <div className="shrink-0 bg-navy-800/80 border-t border-navy-500/30 px-4 py-3 grid grid-cols-5 gap-3">
            {metricCards.map((m) => (
              <div key={m.label} className="space-y-1">
                <div className="flex items-baseline justify-between">
                  <span className="text-[10px] font-mono text-slate-500">{m.label}</span>
                  <span className={`text-sm font-display font-700 ${m.color}`}>
                    {m.value}<span className="text-xs">{m.unit}</span>
                  </span>
                </div>
                <div className="h-1 rounded-full bg-navy-600 overflow-hidden">
                  <div
                    className={`h-full rounded-full ${m.color.replace("text-", "bg-")} transition-all duration-700`}
                    style={{ width: `${m.bar}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Right panel */}
        <div className="w-64 shrink-0 bg-navy-800 border-l border-navy-500/40 flex flex-col overflow-y-auto">
          <div className="px-4 py-3 border-b border-navy-500/40">
            <div className="text-xs font-display font-600 text-slate-300 uppercase tracking-wider">Processing Pipeline</div>
          </div>
          <div className="px-4 py-3 space-y-1.5">
            {pipeline.map((step, i) => (
              <div key={i} className="flex items-center gap-2.5">
                <div className={`w-4 h-4 rounded-full flex items-center justify-center shrink-0 ${
                  step.done ? "bg-emerald-signal/20 border border-emerald-signal/40" : "bg-navy-600 border border-navy-500/40"
                }`}>
                  {step.done && <span className="text-emerald-signal text-[9px]">✓</span>}
                </div>
                <div className={`flex-1 h-px`} />
                <span className={`text-xs ${step.done ? "text-slate-300" : "text-slate-600"}`}>{step.label}</span>
              </div>
            ))}
          </div>

          {/* Resolution display (hide in realtime mode to save space) */}
          {inputMode !== "realtime" && (
            <div className="mx-4 my-3 p-3 rounded-xl bg-navy-700 border border-navy-500/40">
              <div className="text-[10px] font-mono text-slate-500 mb-1">Resolution Improvement</div>
              <div className="flex items-center gap-2">
                <span className="font-display font-700 text-white text-lg">10m</span>
                <span className="text-blue-electric text-sm">→</span>
                <span className="font-display font-700 text-blue-electric text-lg text-glow-blue">2.5m</span>
              </div>
              <div className="text-[10px] font-mono text-slate-500 mt-1">4× spatial resolution increase</div>
            </div>
          )}

          {/* ── Realtime Panel (shown in realtime mode) ── */}
          {inputMode === "realtime" && (
            <div className="px-3 py-3 border-b border-navy-600/30">
              <FetchRealtimePanel
                projectId={1}
                pickedLat={pickedLat}
                pickedLon={pickedLon}
                onFetchSuccess={handleRealtimeFetchSuccess}
                onProcessStarted={handleRealtimeProcessStarted}
              />
            </div>
          )}

          {/* Run button (hide in realtime mode since the panel has its own button) */}
          {inputMode !== "realtime" && (
            <div className="px-4 pb-4 mt-auto">
              <button 
                onClick={handleRunEnhancement}
                disabled={isRunning || !objectName}
                className="w-full py-3 rounded-xl bg-blue-electric text-white font-display font-700 text-sm glow-blue hover:bg-blue-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isRunning ? "Running..." : "Run Super Resolution"}
              </button>
              <button
                onClick={() => onNavigate("uncertainty")}
                className="w-full mt-2 py-2 rounded-xl border border-navy-500/40 text-xs text-slate-400 hover:text-slate-200 hover:border-slate-500 transition-colors"
              >
                View Uncertainty Map
              </button>
            </div>
          )}
        </div>
      </div>

      {showExport && <ExportModal onClose={() => setShowExport(false)} objectName={objectName} />}
    </div>
  );
}
