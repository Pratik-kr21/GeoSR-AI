import { useState } from "react";

const exportOptions = [
  { id: "package", label: "Full Analysis Package (ZIP)", desc: "Includes Enhanced GeoTIFF, Confidence Map, Preview Image, JSON Metrics, and Provenance." },
];

export default function ExportModal({ onClose, objectName }: { onClose: () => void; objectName: string | null }) {
  const [selected, setSelected] = useState(new Set(["package"]));
  const [generating, setGenerating] = useState(false);

  const toggle = (id: string) => {
    setSelected((s) => {
      const next = new Set(s);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  };

  const handleGenerate = async () => {
    if (!objectName) {
      alert("No file has been processed yet. Please upload and enhance a GeoTIFF first.");
      return;
    }
    
    setGenerating(true);
    
    try {
      if (selected.has("package")) {
        // Trigger the backend to build and stream the ZIP package
        const url = `http://localhost:8000/api/v1/export/1/package?object_name=${encodeURIComponent(objectName)}`;
        const link = document.createElement("a");
        link.href = url;
        link.download = "export.zip"; // Actual filename is handled by Content-Disposition header
        link.click();
      }
      
      // Delay closing to show user something happened
      setTimeout(() => {
        onClose();
      }, 1500);
      
    } catch (error) {
      alert(`Export failed: ${error instanceof Error ? error.message : "Unknown error"}`);
    } finally {
      setGenerating(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-navy-950/80 backdrop-blur-sm">
      <div className="bg-navy-800 border border-navy-500/50 rounded-2xl w-full max-w-md mx-4 shadow-2xl">
        <div className="px-6 py-5 border-b border-navy-500/40 flex items-center justify-between">
          <div>
            <h2 className="font-display font-700 text-lg text-white">Export Analysis</h2>
            <p className="text-xs text-slate-400 mt-0.5 font-mono">
              {objectName ? objectName.split("/").pop() : "No file selected"}
            </p>
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
            </label>
          ))}
        </div>

        {!objectName && (
          <div className="px-6 pb-2">
            <div className="text-xs text-amber-warn font-mono">⚠ Upload and enhance a GeoTIFF before exporting</div>
          </div>
        )}

        <div className="px-6 py-4 border-t border-navy-500/40 flex gap-3">
          <button
            onClick={onClose}
            className="flex-1 py-2.5 rounded-xl border border-navy-500/50 text-sm text-slate-400 hover:text-slate-200 hover:border-navy-400/60 transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleGenerate}
            disabled={generating || selected.size === 0 || !objectName}
            className="flex-1 py-2.5 rounded-xl bg-blue-electric text-white text-sm font-display font-600 glow-blue hover:bg-blue-600 transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
          >
            {generating ? (
              <>
                <span className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                Downloading…
              </>
            ) : (
              "Download"
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
