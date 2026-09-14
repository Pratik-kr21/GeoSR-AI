import { useState } from "react";

const exportOptions = [
  { id: "geotiff", label: "Enhanced GeoTIFF", desc: "2.5m super-resolved output", size: "~142 MB" },
  { id: "metrics", label: "Validation Metrics", desc: "PSNR, SSIM, LPIPS, SAM scores", size: "~48 KB" },
  { id: "uncertainty", label: "Uncertainty Heatmap", desc: "Pixel-level confidence map", size: "~8 MB" },
  { id: "confidence", label: "Confidence Map", desc: "Per-region trust scores", size: "~8 MB" },
  { id: "summary", label: "GeoAssist AI Summary", desc: "Natural language analysis report", size: "~12 KB" },
  { id: "metadata", label: "Metadata & CRS Information", desc: "EPSG codes, bounds, projection", size: "~4 KB" },
];

export default function ExportModal({ onClose }: { onClose: () => void }) {
  const [selected, setSelected] = useState(new Set(["geotiff", "metrics", "uncertainty", "confidence", "summary", "metadata"]));
  const [generating, setGenerating] = useState(false);

  const toggle = (id: string) => {
    setSelected((s) => {
      const next = new Set(s);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  };

  const handleGenerate = () => {
    setGenerating(true);
    setTimeout(() => { setGenerating(false); onClose(); }, 2000);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-navy-950/80 backdrop-blur-sm">
      <div className="bg-navy-800 border border-navy-500/50 rounded-2xl w-full max-w-md mx-4 shadow-2xl">
        <div className="px-6 py-5 border-b border-navy-500/40 flex items-center justify-between">
          <div>
            <h2 className="font-display font-700 text-lg text-white">Export Analysis</h2>
            <p className="text-xs text-slate-400 mt-0.5 font-mono">Chandigarh Urban Analysis · 2024-01-15</p>
          </div>
          <button onClick={onClose} className="text-slate-500 hover:text-slate-300 text-xl leading-none">×</button>
        </div>

        <div className="px-6 py-4 space-y-2">
          {exportOptions.map((opt) => (
            <label
              key={opt.id}
              className={`flex items-start gap-3 p-3 rounded-xl border cursor-pointer transition-all ${
                selected.has(opt.id)
                  ? "bg-blue-electric/8 border-blue-electric/40"
                  : "bg-navy-700/40 border-navy-500/30 hover:border-navy-500/60"
              }`}
            >
              <input
                type="checkbox"
                checked={selected.has(opt.id)}
                onChange={() => toggle(opt.id)}
                className="mt-0.5 accent-blue-electric"
              />
              <div className="flex-1 min-w-0">
                <div className="text-sm font-medium text-slate-200">{opt.label}</div>
                <div className="text-xs text-slate-500 mt-0.5">{opt.desc}</div>
              </div>
              <span className="text-[10px] font-mono text-slate-500 shrink-0">{opt.size}</span>
            </label>
          ))}
        </div>

        <div className="px-6 py-4 border-t border-navy-500/40 flex gap-3">
          <button
            onClick={onClose}
            className="flex-1 py-2.5 rounded-xl border border-navy-500/50 text-sm text-slate-400 hover:text-slate-200 hover:border-navy-400/60 transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleGenerate}
            disabled={generating || selected.size === 0}
            className="flex-1 py-2.5 rounded-xl bg-blue-electric text-white text-sm font-display font-600 glow-blue hover:bg-blue-600 transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
          >
            {generating ? (
              <>
                <span className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                Generating…
              </>
            ) : (
              "Generate Report"
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
