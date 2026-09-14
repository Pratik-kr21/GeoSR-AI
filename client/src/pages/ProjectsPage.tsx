const projects = [
  {
    id: 1,
    name: "Chandigarh Urban Mapping",
    location: "Chandigarh, India",
    date: "2024-01-15",
    inputRes: "10m",
    outputRes: "2.5m",
    confidence: 89,
    status: "Complete",
    statusColor: "text-emerald-signal bg-emerald-signal/10 border-emerald-signal/20",
    img: "https://images.unsplash.com/photo-1477959858617-67f85cf4f1df?w=300&h=200&fit=crop&auto=format",
  },
  {
    id: 2,
    name: "Punjab Crop Monitoring",
    location: "Punjab, India",
    date: "2024-01-08",
    inputRes: "10m",
    outputRes: "4m",
    confidence: 92,
    status: "Complete",
    statusColor: "text-emerald-signal bg-emerald-signal/10 border-emerald-signal/20",
    img: "https://images.unsplash.com/photo-1500382017468-9049fed747ef?w=300&h=200&fit=crop&auto=format",
  },
  {
    id: 3,
    name: "Flood Damage Assessment",
    location: "Assam, India",
    date: "2023-12-22",
    inputRes: "10m",
    outputRes: "2.5m",
    confidence: 78,
    status: "Review",
    statusColor: "text-amber-warn bg-amber-warn/10 border-amber-warn/20",
    img: "https://images.unsplash.com/photo-1504711434969-e33886168f5c?w=300&h=200&fit=crop&auto=format",
  },
  {
    id: 4,
    name: "Delhi Infrastructure Scan",
    location: "New Delhi, India",
    date: "2023-12-14",
    inputRes: "10m",
    outputRes: "2.5m",
    confidence: 85,
    status: "Complete",
    statusColor: "text-emerald-signal bg-emerald-signal/10 border-emerald-signal/20",
    img: "https://images.unsplash.com/photo-1449824913935-59a10b8d2000?w=300&h=200&fit=crop&auto=format",
  },
  {
    id: 5,
    name: "Rajasthan Arid Mapping",
    location: "Rajasthan, India",
    date: "2023-11-30",
    inputRes: "10m",
    outputRes: "4m",
    confidence: 91,
    status: "Complete",
    statusColor: "text-emerald-signal bg-emerald-signal/10 border-emerald-signal/20",
    img: "https://images.unsplash.com/photo-1509316785289-025f5b846b35?w=300&h=200&fit=crop&auto=format",
  },
  {
    id: 6,
    name: "Mumbai Coastal Change",
    location: "Maharashtra, India",
    date: "2023-11-18",
    inputRes: "10m",
    outputRes: "2.5m",
    confidence: 83,
    status: "Processing",
    statusColor: "text-blue-electric bg-blue-electric/10 border-blue-electric/20",
    img: "https://images.unsplash.com/photo-1529253355930-ddbe423a2ac7?w=300&h=200&fit=crop&auto=format",
  },
];

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

export default function ProjectsPage() {
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
              {projects.length} Projects
            </div>
            <button className="px-4 py-2 rounded-xl bg-blue-electric text-white text-xs font-display font-600 glow-blue hover:bg-blue-600 transition-colors">
              + New Analysis
            </button>
          </div>
        </div>

        {/* Grid */}
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
          {projects.map((p) => (
            <div key={p.id} className="bg-navy-800 border border-navy-500/40 rounded-xl overflow-hidden hover:border-blue-electric/30 transition-all hover:-translate-y-0.5 cursor-pointer group">
              {/* Thumbnail */}
              <div className="relative h-36 bg-navy-700 overflow-hidden">
                <img
                  src={p.img}
                  alt={p.name}
                  className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                />
                <div className="absolute inset-0 bg-navy-900/40" />
                <div className="absolute top-2 right-2">
                  <span className={`px-2 py-0.5 rounded text-[10px] font-mono border ${p.statusColor}`}>
                    {p.status}
                  </span>
                </div>
                <div className="absolute bottom-2 left-2 px-1.5 py-0.5 rounded bg-navy-950/80 text-[10px] font-mono text-slate-400">
                  {p.inputRes} → {p.outputRes}
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

                <ConfidenceBar value={p.confidence} />

                <div className="flex items-center justify-between text-[10px] font-mono text-slate-600">
                  <span>{p.date}</span>
                  <span className="text-slate-500">Sentinel-2</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
