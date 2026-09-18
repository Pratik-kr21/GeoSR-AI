import { useState, useRef, useCallback, useEffect } from "react";
import ExportModal from "../components/ExportModal";
import MapViewer from "../components/MapViewer";
import type { Page } from "../App";
import { uploadGeoTIFF, triggerSuperResolution, checkJobStatus, fetchValidationMetrics } from "../services/api";

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
          {objectName && (
            <>
              {["Sentinel-2", "4× Upscale", "CRS Preserved"].map((chip) => (
                <span key={chip} className="px-2 py-0.5 rounded text-[10px] font-mono bg-navy-700 border border-navy-500/40 text-slate-400">
                  {chip}
                </span>
              ))}
              <span className={`px-2 py-0.5 rounded text-[10px] font-mono border ${
                status === "completed" ? "bg-emerald-signal/10 border-emerald-signal/30 text-emerald-signal" :
                status === "processing" ? "bg-amber-warn/10 border-amber-warn/30 text-amber-warn" :
                "bg-navy-700 border-navy-500/40 text-slate-400"
              }`}>
                {status === "completed" ? "✓ Enhanced" : status === "processing" ? "⟳ Processing" : "Pending"}
              </span>
            </>
          )}
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <button 
            onClick={handleUploadClick}
            disabled={isUploading}
            className="px-3 py-1.5 rounded-lg border border-navy-500/50 text-xs text-slate-400 hover:text-slate-200 hover:border-slate-500 transition-colors disabled:opacity-50"
          >
            {isUploading ? "Uploading..." : "Upload GeoTIFF"}
          </button>
          <button 
            onClick={handleRunEnhancement}
            disabled={isRunning || !objectName}
            className="px-3 py-1.5 rounded-lg bg-blue-electric/15 border border-blue-electric/40 text-xs text-blue-electric hover:bg-blue-electric/25 transition-colors font-display font-600 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isRunning ? "Running..." : "Run Enhancement"}
          </button>
          <button
            onClick={() => setShowExport(true)}
            className="px-3 py-1.5 rounded-lg bg-emerald-signal/10 border border-emerald-signal/30 text-xs text-emerald-signal hover:bg-emerald-signal/20 transition-colors"
          >
            Export
          </button>
        </div>
      </div>

      {/* Main area */}
      <div className="flex-1 flex overflow-hidden">
        {/* Map area */}
        <div className="flex-1 flex flex-col min-w-0">
          {/* Map */}
          <div className="flex-1 relative overflow-hidden select-none bg-navy-950 grid-bg">
            <MapViewer activeLayers={activeLayers} isCompleted={status === "completed"} objectName={objectName} />
          </div>

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

          {/* Resolution display */}
          <div className="mx-4 my-3 p-3 rounded-xl bg-navy-700 border border-navy-500/40">
            <div className="text-[10px] font-mono text-slate-500 mb-1">Resolution Improvement</div>
            <div className="flex items-center gap-2">
              <span className="font-display font-700 text-white text-lg">10m</span>
              <span className="text-blue-electric text-sm">→</span>
              <span className="font-display font-700 text-blue-electric text-lg text-glow-blue">2.5m</span>
            </div>
            <div className="text-[10px] font-mono text-slate-500 mt-1">4× spatial resolution increase</div>
          </div>

          {/* Run button */}
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
        </div>
      </div>

      {showExport && <ExportModal onClose={() => setShowExport(false)} objectName={objectName} />}
    </div>
  );
}
