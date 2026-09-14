import { useState, useRef, useCallback, useEffect } from "react";
import ExportModal from "../components/ExportModal";
import MapViewer from "../components/MapViewer";
import type { Page } from "../App";
import { uploadGeoTIFF, triggerSuperResolution, checkJobStatus } from "../services/api";

const pipeline = [
  { label: "Geo Preprocessing", done: true },
  { label: "Cloud Masking", done: true },
  { label: "Band Alignment", done: true },
  { label: "Multispectral Feature Extraction", done: true },
  { label: "Super Resolution", done: true },
  { label: "Geo-Consistency Check", done: true },
  { label: "Validation", done: true },
];

const layers = [
  { id: "enhanced", label: "Enhanced Image", color: "bg-blue-electric" },
  { id: "original", label: "Original Image", color: "bg-slate-500" },
  { id: "uncertainty", label: "Uncertainty Map", color: "bg-red-alert" },
  { id: "confidence", label: "Confidence Layer", color: "bg-emerald-signal" },
  { id: "reference", label: "Reference Image", color: "bg-amber-warn" },
  { id: "ndvi", label: "NDVI / Spectral Layer", color: "bg-purple-ai" },
];

const metricCards = [
  { label: "PSNR", value: "32.8", unit: "dB", color: "text-blue-electric", bar: 82 },
  { label: "SSIM", value: "0.91", unit: "", color: "text-cyan-glow", bar: 91 },
  { label: "Spectral Consistency", value: "94", unit: "%", color: "text-emerald-signal", bar: 94 },
  { label: "Avg Confidence", value: "87", unit: "%", color: "text-purple-ai", bar: 87 },
  { label: "Low Conf Regions", value: "12", unit: "", color: "text-amber-warn", bar: 12 },
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
  const [sliderX, setSliderX] = useState(45);
  const [activeLayers, setActiveLayers] = useState(new Set(["enhanced", "original"]));
  const [showExport, setShowExport] = useState(false);
  
  // API Integration states
  const [isUploading, setIsUploading] = useState(false);
  const [isRunning, setIsRunning] = useState(false);
  const [status, setStatus] = useState<string>("idle");
  
  const sliderRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const dragging = useRef(false);

  const handleMouseMove = useCallback((e: React.MouseEvent) => {
    if (!dragging.current || !sliderRef.current) return;
    const rect = sliderRef.current.getBoundingClientRect();
    setSliderX(Math.max(5, Math.min(95, ((e.clientX - rect.left) / rect.width) * 100)));
  }, []);

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
    try {
      // Hardcoding project_id to 1 for MVP
      const result = await uploadGeoTIFF(1, file);
      setObjectName(result.object_name);
      alert(`File uploaded successfully!`);
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
    try {
      const job = await triggerSuperResolution(1, objectName);
      console.log(`Super Resolution started! Job ID: ${job.job_id}`);
      
      // Basic polling for MVP
      const interval = setInterval(async () => {
        const jobStatus = await checkJobStatus(job.job_id);
        setStatus(jobStatus.status);
        if (jobStatus.status === "completed") {
          clearInterval(interval);
          setIsRunning(false);
          console.log("Super Resolution Completed!");
        } else if (jobStatus.status === "failed") {
          clearInterval(interval);
          setIsRunning(false);
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
          <span className="font-display font-600 text-sm text-white">Chandigarh Urban Analysis</span>
          {["Sentinel-2", "Resolution: 10m", "Output: 2.5m", "RGB + NIR", "CRS Preserved"].map((chip) => (
            <span key={chip} className="px-2 py-0.5 rounded text-[10px] font-mono bg-navy-700 border border-navy-500/40 text-slate-400">
              {chip}
            </span>
          ))}
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <button 
            onClick={handleUploadClick}
            disabled={isUploading}
            className="px-3 py-1.5 rounded-lg border border-navy-500/50 text-xs text-slate-400 hover:text-slate-200 hover:border-slate-500 transition-colors disabled:opacity-50"
          >
            {isUploading ? "Uploading..." : "Upload GeoTIFF"}
          </button>
          <button className="px-3 py-1.5 rounded-lg border border-navy-500/50 text-xs text-slate-400 hover:text-slate-200 hover:border-slate-500 transition-colors">
            Select AOI
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
          <div
            ref={sliderRef}
            className="flex-1 relative overflow-hidden cursor-ew-resize select-none bg-navy-950 grid-bg"
            onMouseMove={handleMouseMove}
            onMouseUp={() => { dragging.current = false; }}
            onMouseLeave={() => { dragging.current = false; }}
          >
            {/* The Leaflet Map acts as the background/original */}
            <MapViewer sliderX={sliderX} isCompleted={status === "completed"} objectName={objectName} />
            
            {/* We no longer need the mock overlay because MapViewer handles the real ImageOverlay */}

            {/* Labels */}
            <div className="absolute top-3 left-3 px-2.5 py-1 rounded-lg bg-navy-950/80 border border-navy-500/40 text-xs font-mono text-slate-400 backdrop-blur-sm z-[500]">
              Original Sentinel-2 · 10m
            </div>
            <div className="absolute top-3 right-3 px-2.5 py-1 rounded-lg bg-navy-950/80 border border-blue-electric/30 text-xs font-mono text-blue-electric backdrop-blur-sm z-[500]">
              GeoSR-AI Enhanced · 2.5m
            </div>

            {/* Slider divider */}
            <div
              className="absolute top-0 bottom-0 w-0.5 bg-blue-electric/90 glow-blue z-[500]"
              style={{ left: `${sliderX}%` }}
              onMouseDown={() => { dragging.current = true; }}
            >
              <div className="absolute top-1/2 -translate-y-1/2 left-1/2 -translate-x-1/2 w-7 h-7 rounded-full bg-blue-electric glow-blue flex items-center justify-center text-white text-xs cursor-ew-resize shadow-[0_0_15px_rgba(0,212,255,0.6)]">
                ⇔
              </div>
            </div>

            {/* Map controls */}
            <div className="absolute right-3 bottom-16 flex flex-col gap-1">
              {["+", "−", "⊞", "⛶"].map((icon, i) => (
                <button key={i} className="w-7 h-7 rounded bg-navy-800/90 border border-navy-500/40 text-slate-400 hover:text-white hover:border-slate-500 text-sm backdrop-blur-sm transition-colors flex items-center justify-center">
                  {icon}
                </button>
              ))}
            </div>

            {/* Coordinate overlay */}
            <div className="absolute bottom-3 left-3 px-2 py-1 rounded bg-navy-950/80 text-[10px] font-mono text-slate-500 backdrop-blur-sm">
              30.7333°N, 76.7794°E · UTM 43N · WGS-84
            </div>
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

          {/* Metrics row */}
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
                    className={`h-full rounded-full ${m.color.replace("text-", "bg-")} transition-all`}
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
                <div className={`flex-1 h-px ${i < pipeline.length - 1 ? "" : ""}`} />
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

      {showExport && <ExportModal onClose={() => setShowExport(false)} />}
    </div>
  );
}
