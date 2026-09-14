import type { Page } from "../App";

const navItems: { id: Page; label: string; icon: string }[] = [
  { id: "dashboard", label: "Dashboard", icon: "⬡" },
  { id: "new-analysis", label: "New Analysis", icon: "＋" },
  { id: "projects", label: "Projects", icon: "◫" },
  { id: "imagery", label: "Satellite Imagery", icon: "◉" },
  { id: "validation", label: "Validation", icon: "◈" },
  { id: "reports", label: "Reports", icon: "▣" },
  { id: "geoassist", label: "GeoAssist AI", icon: "◎" },
  { id: "settings", label: "Settings", icon: "⊛" },
];

export default function Sidebar({
  current,
  onNavigate,
}: {
  current: Page;
  onNavigate: (p: Page) => void;
}) {
  return (
    <aside className="w-16 lg:w-56 flex flex-col shrink-0 bg-navy-800 border-r border-navy-500/40 h-full">
      {/* Logo */}
      <div className="px-3 lg:px-4 py-5 border-b border-navy-500/40">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded bg-blue-electric flex items-center justify-center text-white font-display font-bold text-sm glow-blue shrink-0">
            G
          </div>
          <div className="hidden lg:block">
            <div className="font-display font-700 text-sm text-white leading-none">GeoSR-AI</div>
            <div className="text-[10px] text-navy-400 font-mono mt-0.5">v2.1.0 · PROD</div>
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
              {item.id === "geoassist" && (
                <span className="hidden lg:block ml-auto text-[9px] font-mono px-1 py-0.5 rounded bg-purple-ai/20 text-purple-ai border border-purple-ai/30">
                  AI
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
  );
}
