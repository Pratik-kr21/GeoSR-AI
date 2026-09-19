import { useState, useRef, useCallback } from "react";
import type { Page } from "../App";

const metrics = [
  { label: "10m → 2.5m–4m", sub: "Resolution Gain" },
  { label: "Spectral Aware", sub: "13 Band Processing" },
  { label: "Geo-Consistent", sub: "CRS Preserved" },
  { label: "Confidence-Aware", sub: "Uncertainty Maps" },
  { label: "Offline AI", sub: "Powered by Ollama" },
];

const features = [
  {
    icon: "◈",
    color: "text-blue-electric",
    bg: "bg-blue-electric/10",
    border: "border-blue-electric/20",
    title: "Controlled Super Resolution",
    desc: "AI-generated details remain constrained by the original satellite observation — no hallucinated structure.",
  },
  {
    icon: "◉",
    color: "text-cyan-glow",
    bg: "bg-cyan-glow/10",
    border: "border-cyan-glow/20",
    title: "Multispectral Intelligence",
    desc: "Uses all Sentinel-2 spectral bands including NIR, SWIR and Red Edge instead of treating imagery as plain RGB.",
  },
  {
    icon: "◫",
    color: "text-emerald-signal",
    bg: "bg-emerald-signal/10",
    border: "border-emerald-signal/20",
    title: "Scientific Validation",
    desc: "Measures PSNR, SSIM, LPIPS, SAM spectral accuracy, and edge/boundary fidelity against reference imagery.",
  },
  {
    icon: "⬡",
    color: "text-purple-ai",
    bg: "bg-purple-ai/10",
    border: "border-purple-ai/20",
    title: "Uncertainty Heatmap",
    desc: "Highlights every region where AI-generated detail has lower confidence — so you always know what to trust.",
  },
];

export default function LandingPage({ onNavigate }: { onNavigate: (p: Page) => void }) {
  const [sliderX, setSliderX] = useState(50);
  const sliderRef = useRef<HTMLDivElement>(null);
  const dragging = useRef(false);

  const handleMouseDown = () => { dragging.current = true; };

  const handleMouseMove = useCallback((e: React.MouseEvent) => {
    if (!dragging.current || !sliderRef.current) return;
    const rect = sliderRef.current.getBoundingClientRect();
    const x = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
    setSliderX(x * 100);
  }, []);

  const handleMouseUp = () => { dragging.current = false; };

  const handleTouchMove = useCallback((e: React.TouchEvent) => {
    if (!sliderRef.current) return;
    const rect = sliderRef.current.getBoundingClientRect();
    const x = Math.max(0, Math.min(1, (e.touches[0].clientX - rect.left) / rect.width));
    setSliderX(x * 100);
  }, []);

  return (
    <div className="min-h-full bg-navy-900 grid-bg overflow-y-auto">
      {/* Nav */}
      <header className="sticky top-0 z-40 bg-navy-900/90 backdrop-blur border-b border-navy-500/30 px-6 lg:px-16 py-4 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded bg-blue-electric flex items-center justify-center text-white font-display font-bold text-sm glow-blue">G</div>
          <span className="font-display font-700 text-white text-lg">GeoSR-AI</span>
        </div>
        <nav className="hidden md:flex items-center gap-6">
          <button onClick={() => onNavigate("intelligence")} className="text-sm text-slate-400 hover:text-slate-200 transition-colors">Technology</button>
          <button onClick={() => onNavigate("validation")} className="text-sm text-slate-400 hover:text-slate-200 transition-colors">Validation</button>
          <a href="https://github.com/Pratik-kr21/GeoSR-AI" target="_blank" rel="noreferrer" className="text-sm text-slate-400 hover:text-slate-200 transition-colors">Documentation</a>
        </nav>
        <button
          onClick={() => onNavigate("dashboard")}
          className="px-4 py-2 rounded-lg bg-blue-electric text-white text-sm font-display font-600 glow-blue hover:bg-blue-600 transition-colors"
        >
          Launch App
        </button>
      </header>

      {/* Hero */}
      <section className="px-6 lg:px-16 pt-16 pb-10 max-w-7xl mx-auto">
        <div className="grid lg:grid-cols-2 gap-12 items-center">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-blue-electric/10 border border-blue-electric/30 text-blue-electric text-xs font-mono mb-6">
              <span className="w-1.5 h-1.5 rounded-full bg-blue-electric animate-pulse" />
              Sentinel-2 · AI-Powered · Scientifically Validated
            </div>
            <h1 className="font-display font-800 text-4xl lg:text-5xl text-white leading-tight mb-5">
              Turn Medium-Resolution{" "}
              <span className="text-blue-electric text-glow-blue">Satellite Data</span>{" "}
              into Trustworthy High-Resolution Insights.
            </h1>
            <p className="text-slate-400 text-lg leading-relaxed mb-8">
              GeoSR-AI enhances Sentinel-2 imagery from 10m resolution to 2.5m–4m using AI-powered super-resolution while preserving geospatial and spectral consistency and clearly visualizing uncertainty.
            </p>
            <div className="flex flex-wrap gap-3">
              <button
                onClick={() => onNavigate("dashboard")}
                className="px-6 py-3 rounded-xl bg-blue-electric text-white font-display font-600 text-sm glow-blue hover:bg-blue-600 transition-colors"
              >
                Launch GeoSR-AI
              </button>
              <button
                onClick={() => onNavigate("validation")}
                className="px-6 py-3 rounded-xl border border-blue-electric/40 text-blue-electric font-display font-600 text-sm hover:bg-blue-electric/10 transition-colors"
              >
                Explore Technology
              </button>
            </div>
            {/* Metric pills */}
            <div className="flex flex-wrap gap-2 mt-8">
              {metrics.map((m) => (
                <div key={m.label} className="px-3 py-1.5 rounded-lg bg-navy-800 border border-navy-500/40 hover:border-blue-electric/30 transition-colors">
                  <div className="text-xs font-display font-600 text-white">{m.label}</div>
                  <div className="text-[10px] font-mono text-slate-500">{m.sub}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Before/After Slider */}
          <div className="relative">
            <div className="text-center mb-3 flex items-center justify-center gap-4 text-xs font-mono text-slate-500">
              <span className="text-slate-400">Original Sentinel-2 · 10m</span>
              <span className="w-4 h-px bg-navy-500" />
              <span className="text-blue-electric">GeoSR-AI Enhanced · 2.5m</span>
            </div>
            <div
              ref={sliderRef}
              className="relative rounded-xl overflow-hidden border border-navy-500/40 cursor-ew-resize select-none"
              style={{ aspectRatio: "4/3" }}
              onMouseMove={handleMouseMove}
              onMouseUp={handleMouseUp}
              onMouseLeave={handleMouseUp}
              onTouchMove={handleTouchMove}
              onTouchEnd={handleMouseUp}
            >
              {/* After — enhanced (sharp) */}
              <img
                src="https://images.unsplash.com/photo-1477959858617-67f85cf4f1df?w=900&h=700&fit=crop&auto=format"
                alt="GeoSR-AI enhanced satellite image 2.5m"
                className="absolute inset-0 w-full h-full object-cover"
                draggable={false}
              />
              {/* Before — original (blurred/desaturated) */}
              <div
                className="absolute inset-0 overflow-hidden"
                style={{ clipPath: `inset(0 ${100 - sliderX}% 0 0)` }}
              >
                <img
                  src="https://images.unsplash.com/photo-1477959858617-67f85cf4f1df?w=900&h=700&fit=crop&auto=format"
                  alt="Original Sentinel-2 10m resolution satellite image"
                  className="absolute inset-0 w-full h-full object-cover"
                  style={{ filter: "blur(3px) saturate(0.6) brightness(0.85)" }}
                  draggable={false}
                />
                <div className="absolute inset-0 bg-navy-800/20" />
                <div className="absolute top-3 left-3 px-2 py-1 rounded bg-navy-900/80 text-xs font-mono text-slate-300 border border-navy-500/40">
                  10m Input
                </div>
              </div>
              {/* Enhanced label */}
              <div className="absolute top-3 right-3 px-2 py-1 rounded bg-navy-900/80 text-xs font-mono text-blue-electric border border-blue-electric/30">
                2.5m Enhanced
              </div>
              {/* Slider handle */}
              <div
                className="absolute top-0 bottom-0 w-0.5 bg-blue-electric glow-blue cursor-ew-resize"
                style={{ left: `${sliderX}%` }}
                onMouseDown={handleMouseDown}
                onTouchStart={handleMouseDown}
              >
                <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-8 h-8 rounded-full bg-blue-electric glow-blue flex items-center justify-center text-white text-sm">
                  ⇔
                </div>
              </div>
              {/* Processing badge */}
              <div className="absolute bottom-3 left-1/2 -translate-x-1/2 flex items-center gap-2 px-3 py-1.5 rounded-full bg-navy-900/90 border border-navy-500/40 text-xs font-mono text-slate-300">
                <span className="text-slate-500">10m</span>
                <span className="text-navy-400">→</span>
                <span className="text-blue-electric">AI Processing</span>
                <span className="text-navy-400">→</span>
                <span className="text-emerald-signal">2.5m</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="px-6 lg:px-16 py-16 max-w-7xl mx-auto">
        <div className="text-center mb-10">
          <div className="text-xs font-mono text-blue-electric mb-2 uppercase tracking-widest">Core Capabilities</div>
          <h2 className="font-display font-700 text-2xl lg:text-3xl text-white">Scientific AI for Satellite Imagery</h2>
        </div>
        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {features.map((f) => (
            <div key={f.title} className={`p-5 rounded-xl bg-navy-800 border ${f.border} hover:border-opacity-50 transition-all hover:-translate-y-0.5`}>
              <div className={`w-9 h-9 rounded-lg ${f.bg} border ${f.border} flex items-center justify-center ${f.color} text-lg mb-4`}>
                {f.icon}
              </div>
              <h3 className={`font-display font-600 text-sm ${f.color} mb-2`}>{f.title}</h3>
              <p className="text-xs text-slate-400 leading-relaxed">{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-navy-500/30 px-6 lg:px-16 py-6 flex items-center justify-between text-xs font-mono text-slate-600">
        <span>© 2024 GeoSR-AI · All rights reserved</span>
        <span>Sentinel-2 · ESA Copernicus Programme</span>
      </footer>
    </div>
  );
}
