import { useState } from "react";
import type { Page } from "../App";

const navItems: { id: Page; label: string; icon: string; badge?: string }[] = [
  { id: "dashboard", label: "Dashboard", icon: "⬡" },
  { id: "projects", label: "Projects", icon: "◫" },
  { id: "intelligence", label: "Intelligence", icon: "◈", badge: "NEW" },
  { id: "sensor-data", label: "Sensor Data", icon: "📡" },
  { id: "timeline", label: "Timeline", icon: "◷" },
  { id: "risk-analysis", label: "Risk Analysis", icon: "⚠" },
  { id: "validation", label: "Validation", icon: "◈" },
  { id: "historical", label: "Historical", icon: "◷" },
];

export default function Sidebar({
  current,
  onNavigate,
}: {
  current: Page;
  onNavigate: (p: Page) => void;
}) {
  const [mobileOpen, setMobileOpen] = useState(false);

  const handleNav = (p: Page) => {
    onNavigate(p);
    setMobileOpen(false);
  };

  return (
    <>
      {/* Mobile overlay backdrop */}
      {mobileOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm md:hidden"
          onClick={() => setMobileOpen(false)}
        />
      )}

      {/* Mobile top bar */}
      <div className="md:hidden fixed top-0 left-0 right-0 z-50 flex items-center justify-between px-4 py-3 bg-navy-800/95 backdrop-blur border-b border-navy-500/40">
        <div className="flex items-center gap-2">
          <img
            src="/logo.jpg"
            alt="GeoSR-AI Logo"
            className="w-7 h-7 rounded shrink-0 object-contain shadow-lg shadow-blue-electric/20"
          />
          <span className="font-display font-700 text-sm text-white">GeoSR-AI</span>
        </div>
        <button
          onClick={() => setMobileOpen((v) => !v)}
          className="w-9 h-9 flex flex-col items-center justify-center gap-1.5 rounded-lg hover:bg-navy-700 transition-colors"
          aria-label="Open menu"
        >
          <span
            className={`block w-5 h-0.5 bg-slate-300 transition-all duration-200 ${mobileOpen ? "rotate-45 translate-y-2" : ""}`}
          />
          <span
            className={`block w-5 h-0.5 bg-slate-300 transition-all duration-200 ${mobileOpen ? "opacity-0" : ""}`}
          />
          <span
            className={`block w-5 h-0.5 bg-slate-300 transition-all duration-200 ${mobileOpen ? "-rotate-45 -translate-y-2" : ""}`}
          />
        </button>
      </div>

      {/* Mobile drawer */}
      <aside
        className={`
          fixed top-0 left-0 z-50 h-full w-64 flex flex-col bg-navy-800 border-r border-navy-500/40
          transform transition-transform duration-250 ease-in-out
          md:hidden
          ${mobileOpen ? "translate-x-0" : "-translate-x-full"}
        `}
      >
        {/* Logo */}
        <div className="px-4 py-5 border-b border-navy-500/40 flex items-center gap-2">
          <img
            src="/logo.jpg"
            alt="GeoSR-AI Logo"
            className="w-8 h-8 rounded shrink-0 object-contain shadow-lg shadow-blue-electric/20"
          />
          <div className="font-display font-700 text-sm text-white leading-none">GeoSR-AI</div>
          <button
            onClick={() => setMobileOpen(false)}
            className="ml-auto text-slate-400 hover:text-white transition-colors p-1"
          >
            ✕
          </button>
        </div>

        {/* Nav */}
        <nav className="flex-1 py-4 space-y-0.5 px-2 overflow-y-auto">
          {navItems.map((item) => {
            const active = current === item.id;
            return (
              <button
                key={item.id}
                onClick={() => handleNav(item.id)}
                className={`w-full flex items-center gap-3 px-3 py-3 rounded-lg text-left transition-all duration-150 group ${
                  active
                    ? "bg-blue-electric/15 text-blue-electric border border-blue-electric/30"
                    : "text-slate-400 hover:text-slate-200 hover:bg-navy-700"
                }`}
              >
                <span className={`text-base shrink-0 ${active ? "text-blue-electric" : "text-navy-400 group-hover:text-slate-300"}`}>
                  {item.icon}
                </span>
                <span className="text-sm font-medium">{item.label}</span>
                {item.badge && (
                  <span className={`ml-auto text-[9px] font-mono px-1 py-0.5 rounded border ${
                    item.badge === "AI"
                      ? "bg-purple-ai/20 text-purple-ai border-purple-ai/30"
                      : "bg-cyan-glow/20 text-cyan-glow border-cyan-glow/30"
                  }`}>
                    {item.badge}
                  </span>
                )}
              </button>
            );
          })}
        </nav>

        {/* Footer */}
        <div className="px-2 py-4 border-t border-navy-500/40 space-y-2">
          <div className="flex items-center gap-2 px-3 py-2">
            <div className="w-6 h-6 rounded-full bg-blue-electric/20 border border-blue-electric/40 flex items-center justify-center text-xs text-blue-electric shrink-0">
              U
            </div>
            <div>
              <div className="text-xs font-medium text-slate-300">Analyst</div>
              <div className="text-[10px] text-slate-500">user@geosr.ai</div>
            </div>
          </div>
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded bg-emerald-signal/10 border border-emerald-signal/20">
            <div className="w-1.5 h-1.5 rounded-full bg-emerald-signal animate-pulse-glow shrink-0" />
            <span className="text-[10px] font-mono text-emerald-signal">AI Engine Online</span>
          </div>
        </div>
      </aside>

      {/* Desktop sidebar (always visible) */}
      <aside className="hidden md:flex w-16 lg:w-56 flex-col shrink-0 bg-navy-800 border-r border-navy-500/40 h-full">
        {/* Logo */}
        <div className="px-3 lg:px-4 py-5 border-b border-navy-500/40">
          <div className="flex items-center gap-2">
            <img
              src="/logo.jpg"
              alt="GeoSR-AI Logo"
              className="w-8 h-8 rounded shrink-0 object-contain shadow-lg shadow-blue-electric/20"
            />
            <div className="hidden lg:block">
              <div className="font-display font-700 text-sm text-white leading-none">GeoSR-AI</div>
            </div>
          </div>
        </div>

        {/* Nav */}
        <nav className="flex-1 py-4 space-y-0.5 px-2">
          {navItems.map((item) => {
            const active = current === item.id;
            return (
              <button
                key={item.id}
                onClick={() => onNavigate(item.id)}
                className={`w-full flex items-center gap-3 px-2 lg:px-3 py-2.5 rounded-lg text-left transition-all duration-150 group ${
                  active
                    ? "bg-blue-electric/15 text-blue-electric border border-blue-electric/30"
                    : "text-slate-400 hover:text-slate-200 hover:bg-navy-700"
                }`}
              >
                <span className={`text-base shrink-0 ${active ? "text-blue-electric" : "text-navy-400 group-hover:text-slate-300"}`}>
                  {item.icon}
                </span>
                <span className="hidden lg:block text-sm font-medium">{item.label}</span>
                {item.badge && (
                  <span className={`hidden lg:block ml-auto text-[9px] font-mono px-1 py-0.5 rounded border ${
                    item.badge === "AI"
                      ? "bg-purple-ai/20 text-purple-ai border-purple-ai/30"
                      : "bg-cyan-glow/20 text-cyan-glow border-cyan-glow/30"
                  }`}>
                    {item.badge}
                  </span>
                )}
              </button>
            );
          })}
        </nav>

        {/* Footer */}
        <div className="px-2 py-4 border-t border-navy-500/40 space-y-2">
          <div className="flex items-center gap-2 px-2 lg:px-3 py-2">
            <div className="w-6 h-6 rounded-full bg-blue-electric/20 border border-blue-electric/40 flex items-center justify-center text-xs text-blue-electric shrink-0">
              U
            </div>
            <div className="hidden lg:block">
              <div className="text-xs font-medium text-slate-300">Analyst</div>
              <div className="text-[10px] text-slate-500">user@geosr.ai</div>
            </div>
          </div>
          <div className="flex items-center gap-1.5 px-2 lg:px-3 py-1.5 rounded bg-emerald-signal/10 border border-emerald-signal/20">
            <div className="w-1.5 h-1.5 rounded-full bg-emerald-signal animate-pulse-glow shrink-0" />
            <span className="hidden lg:block text-[10px] font-mono text-emerald-signal">AI Engine Online</span>
          </div>
        </div>
      </aside>
    </>
  );
}
