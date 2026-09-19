/**
 * FetchRealtimePanel.tsx
 * ----------------------
 * A glassmorphism control panel for real-time Sentinel-2 data acquisition
 * from the Copernicus Data Space Ecosystem (CDSE) + Open-Meteo weather.
 *
 * Supports:
 *  - Lat/lon inputs (pre-fillable from map clicks)
 *  - Cloud cover / days back / buffer sliders
 *  - "Check Availability" (catalog only, no download)
 *  - "Fetch Latest Imagery" (download + store in MinIO)
 *  - "Fetch & Process" (full SR + intelligence pipeline)
 *  - Graceful error messages for every failure mode
 */

import { useState, useEffect } from "react";
import {
  fetchRealtimeStatus,
  checkSceneAvailability,
  fetchRealtimeImagery,
  fetchAndProcessRealtime,
  checkJobStatus,
  triggerSuperResolution,
  type RealtimeFetchParams,
  type RealtimeFetchResult,
  type FetchAndProcessResult,
} from "../services/api";

// ─── Types ────────────────────────────────────────────────────────────────────

type Stage = "idle" | "checking" | "fetching" | "uploading" | "enhancing" | "analyzing" | "done" | "error";

interface Props {
  projectId: number;
  /** If provided, pre-fills the lat/lon fields (e.g. from map click). */
  pickedLat?: number | null;
  pickedLon?: number | null;
  /** If provided, pre-fills the bounding box (e.g. from map draw). */
  pickedBbox?: [number, number, number, number] | null;
  /** Called when a scene is successfully fetched — so Dashboard can update the map. */
  onFetchSuccess?: (result: RealtimeFetchResult) => void;
  /** Called when fetch+process completes so Dashboard can start polling the SR job. */
  onProcessStarted?: (result: FetchAndProcessResult) => void;
}

// ─── Sub-components ───────────────────────────────────────────────────────────

const StageStep = ({
  label,
  active,
  done,
  error,
}: {
  label: string;
  active: boolean;
  done: boolean;
  error: boolean;
}) => (
  <div className="flex items-center gap-2">
    <div
      className={`w-5 h-5 rounded-full flex items-center justify-center text-xs font-bold transition-all duration-300 ${
        error
          ? "bg-red-500 text-white"
          : done
          ? "bg-emerald-500 text-white"
          : active
          ? "bg-blue-500 text-white animate-pulse"
          : "bg-navy-700 text-slate-500"
      }`}
    >
      {error ? "✕" : done ? "✓" : "·"}
    </div>
    <span
      className={`text-xs transition-colors duration-300 ${
        error
          ? "text-red-400"
          : done
          ? "text-emerald-400"
          : active
          ? "text-blue-300 font-medium"
          : "text-slate-500"
      }`}
    >
      {label}
    </span>
  </div>
);

const WeatherCard = ({
  weather,
}: {
  weather: RealtimeFetchResult["weather_summary"];
}) => {
  if (!weather.available) {
    return (
      <div className="text-xs text-amber-400/70 italic">
        Weather data unavailable — GeoRisk will use a neutral weather score.
      </div>
    );
  }

  return (
    <div className="grid grid-cols-2 gap-2 mt-2">
      <div className="bg-navy-900/60 rounded-lg p-2 text-center">
        <div className="text-lg font-bold text-cyan-400">
          {weather.current_precip_mm !== null ? `${weather.current_precip_mm}` : "—"}
          <span className="text-xs font-normal text-slate-400 ml-1">mm</span>
        </div>
        <div className="text-xs text-slate-500 mt-0.5">Current Rain</div>
      </div>
      <div className="bg-navy-900/60 rounded-lg p-2 text-center">
        <div className="text-lg font-bold text-blue-400">
          {weather.total_7d_rain_mm !== null ? `${weather.total_7d_rain_mm}` : "—"}
          <span className="text-xs font-normal text-slate-400 ml-1">mm</span>
        </div>
        <div className="text-xs text-slate-500 mt-0.5">7-day Total</div>
      </div>
    </div>
  );
};

// ─── Main Component ───────────────────────────────────────────────────────────

export default function FetchRealtimePanel({
  projectId,
  pickedLat,
  pickedLon,
  pickedBbox,
  onFetchSuccess,
  onProcessStarted,
}: Props) {
  // Form state
  const [lat, setLat] = useState<string>("28.6139"); // Delhi default
  const [lon, setLon] = useState<string>("77.2090");
  const [bufferKm, setBufferKm] = useState(5);
  const [daysBack, setDaysBack] = useState(30);
  const [maxCloud, setMaxCloud] = useState(20);
  
  const [selectionMode, setSelectionMode] = useState<"point" | "area">("point");

  // Capability state
  const [cdseEnabled, setCdseEnabled] = useState<boolean | null>(null);
  const [cdseMessage, setCdseMessage] = useState<string>("");

  // UI state
  const [stage, setStage] = useState<Stage>("idle");
  const [error, setError] = useState<string | null>(null);
  const [fetchResult, setFetchResult] = useState<RealtimeFetchResult | null>(null);
  const [scenePreview, setScenePreview] = useState<any | null>(null);

  // Pre-fill lat/lon when map pick changes
  useEffect(() => {
    if (pickedLat != null) {
      setLat(pickedLat.toFixed(6));
      setSelectionMode("point");
    }
    if (pickedLon != null) {
      setLon(pickedLon.toFixed(6));
      setSelectionMode("point");
    }
  }, [pickedLat, pickedLon]);

  // Set area mode when bbox changes
  useEffect(() => {
    if (pickedBbox != null) {
      setSelectionMode("area");
    }
  }, [pickedBbox]);

  // Check CDSE status on mount
  useEffect(() => {
    fetchRealtimeStatus()
      .then((s) => {
        setCdseEnabled(s.cdse_enabled);
        setCdseMessage(s.message);
      })
      .catch(() => {
        setCdseEnabled(false);
        setCdseMessage("Could not reach backend to check CDSE status.");
      });
  }, []);

  // ── Handlers ───────────────────────────────────────────────────────────────

  const validateCoords = (): RealtimeFetchParams | null => {
    if (selectionMode === "area" && pickedBbox) {
      return {
        bbox: pickedBbox,
        days_back: daysBack,
        max_cloud_cover: maxCloud,
      };
    }

    const latN = parseFloat(lat);
    const lonN = parseFloat(lon);
    if (isNaN(latN) || latN < -90 || latN > 90) {
      setError("Latitude must be between -90 and 90.");
      return null;
    }
    if (isNaN(lonN) || lonN < -180 || lonN > 180) {
      setError("Longitude must be between -180 and 180.");
      return null;
    }
    return {
      latitude: latN,
      longitude: lonN,
      buffer_km: bufferKm,
      days_back: daysBack,
      max_cloud_cover: maxCloud,
    };
  };

  const handleCheckAvailability = async () => {
    const params = validateCoords();
    if (!params) return;
    setStage("checking");
    setError(null);
    setScenePreview(null);
    setFetchResult(null);
    try {
      const result = await checkSceneAvailability(params);
      setScenePreview(result);
      setStage("idle");
    } catch (e: any) {
      setError(e?.response?.data?.detail?.message || e?.message || "Availability check failed.");
      setStage("error");
    }
  };

  const handleFetch = async () => {
    const params = validateCoords();
    if (!params) return;
    if (!cdseEnabled) {
      setError("CDSE credentials are not configured. See the setup guide to add them.");
      return;
    }
    setStage("fetching");
    setError(null);
    setFetchResult(null);
    setScenePreview(null);
    try {
      // This can take several minutes — a real download
      const result = await fetchRealtimeImagery(projectId, params);
      setFetchResult(result);
      setStage("done");
      onFetchSuccess?.(result);
    } catch (e: any) {
      const detail = e?.response?.data?.detail;
      const msg = typeof detail === "object"
        ? detail.message
        : detail || e?.message || "Failed to fetch satellite imagery.";
      setError(msg);
      setStage("error");
    }
  };

  const handleFetchAndProcess = async () => {
    const params = validateCoords();
    if (!params) return;
    setStage("fetching");
    setError(null);
    setFetchResult(null);
    setScenePreview(null);
    try {
      // Phase 1 & 2: Download + Upload (server-side, shown as "fetching")
      setStage("uploading");
      const result = await fetchAndProcessRealtime(projectId, params);
      setStage("enhancing");

      // Convert to a RealtimeFetchResult-compatible object for display
      setFetchResult({
        observation_id: result.observation_id,
        object_name: result.object_name,
        filename: result.object_name.split("/").pop() || "",
        acquisition_date: result.acquisition_date,
        cloud_cover: result.cloud_cover,
        bounds: null, // will be filled by map auto-fly
        weather_summary: {
          available: result.weather_summary.available,
          current_precip_mm: result.weather_summary.current_precip_mm,
          total_7d_rain_mm: result.weather_summary.total_7d_rain_mm,
          daily_breakdown: [],
        },
        message: result.message,
      });

      onProcessStarted?.(result);

      // Poll SR job until done
      const pollInterval = setInterval(async () => {
        try {
          const status = await checkJobStatus(result.sr_job_id);
          if (status.status === "completed") {
            clearInterval(pollInterval);
            setStage("done");
          } else if (status.status === "failed") {
            clearInterval(pollInterval);
            setStage("error");
            setError("Super-resolution job failed. The image was fetched but could not be enhanced.");
          }
        } catch {
          clearInterval(pollInterval);
        }
      }, 3000);
    } catch (e: any) {
      const detail = e?.response?.data?.detail;
      const msg = typeof detail === "object"
        ? detail.message
        : detail || e?.message || "Failed to fetch and process.";
      setError(msg);
      setStage("error");
    }
  };

  const handleEnhance = async () => {
    if (!fetchResult) return;
    setStage("enhancing");
    setError(null);
    try {
      const result = await triggerSuperResolution(projectId, fetchResult.object_name);
      
      onProcessStarted?.({
        observation_id: fetchResult.observation_id,
        object_name: fetchResult.object_name,
        sr_job_id: result.job_id,
        acquisition_date: fetchResult.acquisition_date,
        cloud_cover: fetchResult.cloud_cover,
        weather_summary: fetchResult.weather_summary,
        message: result.message
      });

      const pollInterval = setInterval(async () => {
        try {
          const status = await checkJobStatus(result.job_id);
          if (status.status === "completed") {
            clearInterval(pollInterval);
            setStage("done");
          } else if (status.status === "failed") {
            clearInterval(pollInterval);
            setStage("error");
            setError("Super-resolution job failed.");
          }
        } catch {
          clearInterval(pollInterval);
        }
      }, 3000);
    } catch (e: any) {
      setError("Failed to trigger super-resolution enhancement.");
      setStage("error");
    }
  };

  // ── Derived state ──────────────────────────────────────────────────────────

  const isBusy = ["checking", "fetching", "uploading", "enhancing", "analyzing"].includes(stage);

  const stageLabels: { key: Stage; label: string }[] = [
    { key: "fetching", label: "Fetching from CDSE" },
    { key: "uploading", label: "Uploading to Storage" },
    { key: "enhancing", label: "Super Resolution" },
    { key: "analyzing", label: "Intelligence Analysis" },
  ];

  const currentStageIdx = stageLabels.findIndex((s) => s.key === stage);

  // ── Render ─────────────────────────────────────────────────────────────────

  return (
    <div className="flex flex-col gap-3 p-4 bg-navy-900/80 backdrop-blur-xl rounded-xl border border-navy-700/60 shadow-2xl">

      {/* Header */}
      <div className="flex items-center gap-2">
        <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-emerald-500 to-cyan-500 flex items-center justify-center shadow-lg">
          <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064" />
          </svg>
        </div>
        <div>
          <h3 className="text-sm font-bold text-white">Live Sentinel-2 Data</h3>
          <p className="text-xs text-slate-400">Copernicus Data Space Ecosystem</p>
        </div>
        {cdseEnabled !== null && (
          <div className={`ml-auto flex items-center gap-1 text-xs px-2 py-0.5 rounded-full border ${
            cdseEnabled
              ? "text-emerald-400 border-emerald-500/30 bg-emerald-500/10"
              : "text-amber-400 border-amber-500/30 bg-amber-500/10"
          }`}>
            <div className={`w-1.5 h-1.5 rounded-full ${cdseEnabled ? "bg-emerald-400 animate-pulse" : "bg-amber-400"}`} />
            {cdseEnabled ? "Live" : "No Credentials"}
          </div>
        )}
      </div>

      {/* CDSE not configured warning */}
      {cdseEnabled === false && (
        <div className="bg-amber-900/20 border border-amber-500/30 rounded-lg p-3 text-xs text-amber-300">
          <strong>CDSE credentials missing.</strong> Weather data (Open-Meteo) still works for free.
          To enable satellite downloads, add <code className="bg-black/30 px-1 rounded">CDSE_CLIENT_ID</code> and{" "}
          <code className="bg-black/30 px-1 rounded">CDSE_CLIENT_SECRET</code> to your{" "}
          <code className="bg-black/30 px-1 rounded">.env</code> file.{" "}
          <a
            href="https://dataspace.copernicus.eu/"
            target="_blank"
            rel="noreferrer"
            className="underline text-amber-200"
          >
            Register free →
          </a>
        </div>
      )}

      {/* Coordinate Inputs */}
      {selectionMode === "area" && pickedBbox ? (
        <div className="bg-navy-800/60 border border-navy-600/40 rounded-lg p-3 text-xs text-slate-300">
          <div className="text-cyan-400 font-medium mb-1">Selected Area (Bounding Box)</div>
          <div className="grid grid-cols-2 gap-x-2 gap-y-1">
            <span className="text-slate-500">Min Lon:</span> <span>{pickedBbox[0].toFixed(5)}</span>
            <span className="text-slate-500">Min Lat:</span> <span>{pickedBbox[1].toFixed(5)}</span>
            <span className="text-slate-500">Max Lon:</span> <span>{pickedBbox[2].toFixed(5)}</span>
            <span className="text-slate-500">Max Lat:</span> <span>{pickedBbox[3].toFixed(5)}</span>
          </div>
          <button
            onClick={() => setSelectionMode("point")}
            className="mt-2 text-[10px] text-blue-400 hover:text-blue-300 underline"
          >
            Switch back to Point mode
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-2 gap-2">
          <div>
            <label className="text-xs text-slate-400 mb-1 block">Latitude</label>
            <input
              type="number"
              value={lat}
              onChange={(e) => { setLat(e.target.value); setSelectionMode("point"); }}
              min={-90} max={90} step={0.0001}
              disabled={isBusy}
              className="w-full bg-navy-800 border border-navy-600 text-white text-sm rounded-lg px-3 py-2 focus:outline-none focus:border-blue-500 disabled:opacity-50"
              placeholder="e.g. 28.6139"
            />
          </div>
          <div>
            <label className="text-xs text-slate-400 mb-1 block">Longitude</label>
            <input
              type="number"
              value={lon}
              onChange={(e) => { setLon(e.target.value); setSelectionMode("point"); }}
              min={-180} max={180} step={0.0001}
              disabled={isBusy}
              className="w-full bg-navy-800 border border-navy-600 text-white text-sm rounded-lg px-3 py-2 focus:outline-none focus:border-blue-500 disabled:opacity-50"
              placeholder="e.g. 77.2090"
            />
          </div>
        </div>
      )}

      {/* Advanced Options */}
      <div className="flex flex-col gap-3 text-xs mt-1">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="text-slate-400 mb-1 flex justify-between">
              <span>Search radius</span>
              <span className="text-white">{selectionMode === "area" ? "—" : `${bufferKm}km`}</span>
            </label>
            <input type="range" min={1} max={50} value={bufferKm}
              onChange={(e) => setBufferKm(+e.target.value)} disabled={isBusy || selectionMode === "area"}
              className={`w-full accent-blue-500 ${selectionMode === "area" ? "opacity-30" : "disabled:opacity-50"}`} />
          </div>
          <div>
            <label className="text-slate-400 mb-1 flex justify-between">
              <span>Max cloud</span>
              <span className="text-white">{maxCloud}%</span>
            </label>
            <input type="range" min={0} max={80} value={maxCloud}
              onChange={(e) => setMaxCloud(+e.target.value)} disabled={isBusy}
              className="w-full accent-cyan-500 disabled:opacity-50" />
          </div>
        </div>
        <div>
          <label className="text-slate-400 mb-1 flex justify-between">
            <span>Days back</span>
            <span className="text-white">{daysBack}</span>
          </label>
          <input type="range" min={5} max={90} value={daysBack}
            onChange={(e) => setDaysBack(+e.target.value)} disabled={isBusy}
            className="w-full accent-purple-500 disabled:opacity-50" />
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex flex-col gap-2 mt-2">
        <button
          onClick={handleFetch}
          disabled={isBusy || !cdseEnabled}
          className="w-full py-3 rounded-lg bg-gradient-to-r from-emerald-600 to-cyan-600 hover:from-emerald-500 hover:to-cyan-500 text-white text-sm font-bold shadow-[0_0_15px_rgba(16,185,129,0.25)] transition-all disabled:opacity-40 disabled:cursor-not-allowed disabled:shadow-none"
        >
          {isBusy && stage !== "checking" ? (
            <span className="flex items-center justify-center gap-2">
              <span className="animate-spin">⟳</span> Fetching from CDSE...
            </span>
          ) : "Fetch Latest Imagery"}
        </button>
        <button
          onClick={handleCheckAvailability}
          disabled={isBusy}
          className="w-full py-2 rounded-lg border border-slate-600 text-slate-300 text-xs hover:border-slate-400 hover:text-white transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
        >
          {stage === "checking" ? (
            <span className="flex items-center justify-center gap-1">
              <span className="animate-spin">⟳</span> Checking catalog...
            </span>
          ) : "Check Availability Only"}
        </button>
      </div>

      {/* Progress Steps (shown when pipeline is running) */}
      {isBusy && stage !== "checking" && (
        <div className="flex justify-between bg-navy-950/60 rounded-lg px-3 py-2">
          {stageLabels.map((s, idx) => (
            <StageStep
              key={s.key}
              label={s.label}
              active={stage === s.key}
              done={currentStageIdx > idx || stage === "done"}
              error={stage === "error" && currentStageIdx === idx}
            />
          ))}
        </div>
      )}

      {/* Error Message */}
      {error && (
        <div className="bg-red-900/20 border border-red-500/30 rounded-lg p-3 text-xs text-red-300 flex gap-2">
          <svg className="w-4 h-4 shrink-0 mt-0.5 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
          <span>{error}</span>
        </div>
      )}

      {/* Scene Availability Preview */}
      {scenePreview && !fetchResult && (
        <div className="bg-navy-800/60 rounded-lg p-3 border border-navy-600/40 text-xs">
          {scenePreview.found ? (
            <>
              <div className="text-emerald-400 font-medium mb-2 flex items-center gap-1">
                <span>✓</span> Scene available
              </div>
              <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-slate-300">
                <span className="text-slate-500">Acquisition</span>
                <span>{scenePreview.acquisition_date?.slice(0, 10) || "—"}</span>
                <span className="text-slate-500">Cloud cover</span>
                <span>{scenePreview.cloud_cover?.toFixed(1)}%</span>
                <span className="text-slate-500">Scene size</span>
                <span>{scenePreview.size_mb} MB</span>
              </div>
            </>
          ) : (
            <div className="text-amber-300">{scenePreview.error || "No scene found."}</div>
          )}
        </div>
      )}

      {/* Fetch Result */}
      {fetchResult && (
        <div className="bg-emerald-900/20 border border-emerald-500/30 rounded-lg p-3 text-xs">
          <div className="text-emerald-400 font-medium mb-2 flex items-center gap-1">
            <span>✓</span> {stage === "done" ? "Complete!" : "Imagery Stored"}
          </div>
          <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-slate-300 mb-2">
            <span className="text-slate-500">Acquired</span>
            <span className="text-white font-medium">
              {fetchResult.acquisition_date?.slice(0, 10) || "—"}
            </span>
            <span className="text-slate-500">Cloud cover</span>
            <span>{fetchResult.cloud_cover?.toFixed(1) ?? "—"}%</span>
            <span className="text-slate-500">File</span>
            <span className="text-slate-300 truncate">{fetchResult.filename}</span>
          </div>

          {/* Weather snapshot */}
          <div className="border-t border-emerald-700/30 pt-2 mt-1 mb-3">
            <div className="text-slate-400 mb-1">Live Weather (Open-Meteo)</div>
            <WeatherCard weather={fetchResult.weather_summary} />
          </div>

          <button
            onClick={handleEnhance}
            disabled={isBusy && stage === "enhancing"}
            className="w-full py-2 rounded-lg bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 text-white text-sm font-bold shadow-[0_0_15px_rgba(59,130,246,0.3)] transition-all disabled:opacity-50"
          >
            {isBusy && stage === "enhancing" ? (
              <span className="flex items-center justify-center gap-2">
                <span className="animate-spin">⟳</span> Enhancing Image...
              </span>
            ) : "Enhance Imagery (Super-Resolution)"}
          </button>
        </div>
      )}
    </div>
  );
}
