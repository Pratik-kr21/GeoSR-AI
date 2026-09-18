import { useEffect, useState } from "react";
import { listProjects, createProject } from "../services/api";
import type { Page } from "../App";

interface ProjectData {
  id: number;
  name: string;
  location: string;
  description: string | null;
  created_at: string;
  updated_at: string;
}

function ConfidenceBar({ value }: { value: number }) {
  const color = value >= 85 ? "#10d98b" : value >= 75 ? "#f59e0b" : "#ef4444";
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1 rounded-full bg-navy-600">
        <div className="h-full rounded-full transition-all" style={{ width: `${value}%`, background: color }} />
      </div>
      <span className="text-xs font-mono" style={{ color }}>{value}%</span>
    </div>
  );
}

export default function ProjectsPage({ onNavigate }: { onNavigate: (p: Page) => void }) {
  const [projects, setProjects] = useState<ProjectData[]>([]);
  const [loading, setLoading] = useState(true);
  const [showNewForm, setShowNewForm] = useState(false);
  const [newName, setNewName] = useState("");
  const [newLocation, setNewLocation] = useState("");
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    loadProjects();
  }, []);

  const loadProjects = async () => {
    setLoading(true);
    try {
      const data = await listProjects();
      setProjects(data);
    } catch (err) {
      console.error("Failed to load projects", err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async () => {
    if (!newName.trim() || !newLocation.trim()) return;
    setCreating(true);
    try {
      await createProject({ name: newName, location: newLocation });
      setNewName("");
      setNewLocation("");
      setShowNewForm(false);
      await loadProjects();
    } catch (err) {
      console.error("Failed to create project", err);
      alert("Failed to create project.");
    } finally {
      setCreating(false);
    }
  };

  return (
    <div className="h-full overflow-y-auto bg-navy-900">
      <div className="max-w-6xl mx-auto p-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <div className="text-xs font-mono text-blue-electric uppercase tracking-widest mb-1">Project History</div>
            <h1 className="font-display font-700 text-2xl text-white">Satellite Analysis Projects</h1>
          </div>
          <div className="flex items-center gap-3">
            <div className="px-3 py-1.5 rounded-lg bg-navy-800 border border-navy-500/40 text-xs text-slate-400">
              {projects.length} Project{projects.length !== 1 ? "s" : ""}
            </div>
            <button
              onClick={() => setShowNewForm(true)}
              className="px-4 py-2 rounded-xl bg-blue-electric text-white text-xs font-display font-600 glow-blue hover:bg-blue-600 transition-colors"
            >
              + New Analysis
            </button>
          </div>
        </div>

        {/* New Project Form */}
        {showNewForm && (
          <div className="mb-6 bg-navy-800 border border-blue-electric/30 rounded-xl p-5">
            <div className="text-sm font-display font-600 text-white mb-3">Create New Project</div>
            <div className="flex gap-3 items-end flex-wrap">
              <div className="flex-1 min-w-48">
                <label className="text-[10px] font-mono text-slate-500 uppercase tracking-widest block mb-1">Project Name</label>
                <input
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  placeholder="e.g. Chandigarh Urban Mapping"
                  className="w-full bg-navy-700 border border-navy-500/40 rounded-lg px-3 py-2 text-sm text-slate-200 placeholder-slate-600 focus:outline-none focus:border-blue-electric/50"
                />
              </div>
              <div className="flex-1 min-w-48">
                <label className="text-[10px] font-mono text-slate-500 uppercase tracking-widest block mb-1">Location</label>
                <input
                  value={newLocation}
                  onChange={(e) => setNewLocation(e.target.value)}
                  placeholder="e.g. Chandigarh, India"
                  className="w-full bg-navy-700 border border-navy-500/40 rounded-lg px-3 py-2 text-sm text-slate-200 placeholder-slate-600 focus:outline-none focus:border-blue-electric/50"
                />
              </div>
              <button
                onClick={handleCreate}
                disabled={creating || !newName.trim() || !newLocation.trim()}
                className="px-4 py-2 rounded-lg bg-blue-electric text-white text-xs font-display font-600 hover:bg-blue-600 disabled:opacity-50 transition-colors"
              >
                {creating ? "Creating..." : "Create"}
              </button>
              <button
                onClick={() => setShowNewForm(false)}
                className="px-4 py-2 rounded-lg border border-navy-500/40 text-xs text-slate-400 hover:text-slate-200 transition-colors"
              >
                Cancel
              </button>
            </div>
          </div>
        )}

        {/* Loading state */}
        {loading && (
          <div className="flex items-center justify-center py-20">
            <div className="w-6 h-6 border-2 border-blue-electric/30 border-t-blue-electric rounded-full animate-spin" />
            <span className="ml-3 text-sm text-slate-400">Loading projects...</span>
          </div>
        )}

        {/* Empty state */}
        {!loading && projects.length === 0 && (
          <div className="text-center py-20">
            <div className="text-4xl mb-3">🛰️</div>
            <div className="font-display font-600 text-white text-lg mb-1">No Projects Yet</div>
            <p className="text-sm text-slate-400 mb-4">Create your first satellite analysis project to get started.</p>
            <button
              onClick={() => setShowNewForm(true)}
              className="px-5 py-2.5 rounded-xl bg-blue-electric text-white text-sm font-display font-600 glow-blue hover:bg-blue-600 transition-colors"
            >
              + Create Project
            </button>
          </div>
        )}

        {/* Grid */}
        {!loading && projects.length > 0 && (
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
            {projects.map((p) => (
              <div
                key={p.id}
                onClick={() => onNavigate("dashboard")}
                className="bg-navy-800 border border-navy-500/40 rounded-xl overflow-hidden hover:border-blue-electric/30 transition-all hover:-translate-y-0.5 cursor-pointer group"
              >
                {/* Thumbnail placeholder with gradient */}
                <div className="relative h-36 bg-gradient-to-br from-navy-700 via-navy-600 to-blue-electric/10 overflow-hidden flex items-center justify-center">
                  <div className="text-4xl opacity-30">🛰️</div>
                  <div className="absolute inset-0 bg-navy-900/20" />
                  <div className="absolute top-2 right-2">
                    <span className="px-2 py-0.5 rounded text-[10px] font-mono border text-emerald-signal bg-emerald-signal/10 border-emerald-signal/20">
                      Active
                    </span>
                  </div>
                  <div className="absolute bottom-2 left-2 px-1.5 py-0.5 rounded bg-navy-950/80 text-[10px] font-mono text-slate-400">
                    10m → 2.5m
                  </div>
                </div>

                {/* Info */}
                <div className="p-4 space-y-3">
                  <div>
                    <div className="font-display font-600 text-sm text-white group-hover:text-blue-electric transition-colors">{p.name}</div>
                    <div className="text-[10px] font-mono text-slate-500 mt-0.5 flex items-center gap-1">
                      <span>◉</span> {p.location}
                    </div>
                  </div>

                  <ConfidenceBar value={88} />

                  <div className="flex items-center justify-between text-[10px] font-mono text-slate-600">
                    <span>{new Date(p.created_at).toLocaleDateString()}</span>
                    <span className="text-slate-500">Sentinel-2</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
