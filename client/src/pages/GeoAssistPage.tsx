import { useState } from "react";
import { queryGeoAssist } from "../services/api";

const suggestions = [
  "Explain validation results",
  "Analyze uncertainty hotspots",
  "What does SAM score mean?",
  "Compare original vs enhanced image",
  "Generate analysis report",
];

const initialMessages = [
  {
    role: "assistant",
    text: "Welcome to GeoAssist! I am connected to the backend. How can I help you analyze your satellite data today?",
  },
];

export default function GeoAssistPage() {
  const [messages, setMessages] = useState(initialMessages);
  const [input, setInput] = useState("");
  const [thinking, setThinking] = useState(false);

  const send = async (text: string) => {
    if (!text.trim()) return;
    setMessages((m) => [...m, { role: "user", text }]);
    setInput("");
    setThinking(true);
    
    try {
      // Hardcoding project_id to 1 for MVP
      const result = await queryGeoAssist(1, text);
      setMessages((m) => [
        ...m,
        { role: "assistant", text: result.response },
      ]);
    } catch (error) {
      console.error("GeoAssist error", error);
      setMessages((m) => [
        ...m,
        { role: "assistant", text: "Sorry, I am currently unable to reach the backend Ollama service. Please make sure the server is running." },
      ]);
    } finally {
      setThinking(false);
    }
  };

  return (
    <div className="flex h-full overflow-hidden bg-navy-900">
      {/* Chat area */}
      <div className="flex-1 flex flex-col min-w-0 border-r border-navy-500/40">
        {/* Header */}
        <div className="shrink-0 bg-navy-800 border-b border-navy-500/40 px-5 py-4">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-purple-ai/20 border border-purple-ai/40 flex items-center justify-center text-purple-ai text-sm">◎</div>
            <div>
              <div className="font-display font-700 text-white text-sm">GeoAssist</div>
              <div className="text-[10px] font-mono text-slate-500">Offline AI Assistant for Satellite Image Interpretation</div>
            </div>
            <div className="ml-auto flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-signal/10 border border-emerald-signal/20 text-[10px] font-mono text-emerald-signal">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-signal animate-pulse" />
              Running Locally via Ollama
            </div>
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-5 py-4 space-y-4">
          {messages.map((msg, i) => (
            <div key={i} className={`flex gap-3 ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
              {msg.role === "assistant" && (
                <div className="w-7 h-7 rounded-lg bg-purple-ai/20 border border-purple-ai/30 flex items-center justify-center text-purple-ai text-xs shrink-0 mt-0.5">◎</div>
              )}
              <div
                className={`max-w-lg rounded-2xl px-4 py-3 text-sm leading-relaxed ${
                  msg.role === "user"
                    ? "bg-blue-electric/20 border border-blue-electric/30 text-slate-200 rounded-tr-sm"
                    : "bg-navy-800 border border-navy-500/40 text-slate-300 rounded-tl-sm"
                }`}
              >
                {msg.text.split("**").map((part, j) =>
                  j % 2 === 1 ? <strong key={j} className="text-white">{part}</strong> : <span key={j}>{part}</span>
                )}
              </div>
              {msg.role === "user" && (
                <div className="w-7 h-7 rounded-lg bg-blue-electric/20 border border-blue-electric/30 flex items-center justify-center text-blue-electric text-xs shrink-0 mt-0.5">U</div>
              )}
            </div>
          ))}
          {thinking && (
            <div className="flex gap-3">
              <div className="w-7 h-7 rounded-lg bg-purple-ai/20 border border-purple-ai/30 flex items-center justify-center text-purple-ai text-xs shrink-0">◎</div>
              <div className="bg-navy-800 border border-navy-500/40 rounded-2xl rounded-tl-sm px-4 py-3 flex gap-1 items-center">
                {[0, 1, 2].map((d) => (
                  <span key={d} className="w-1.5 h-1.5 rounded-full bg-slate-500 animate-bounce" style={{ animationDelay: `${d * 0.15}s` }} />
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Suggestions */}
        <div className="shrink-0 px-5 py-2 flex gap-2 overflow-x-auto">
          {suggestions.map((s) => (
            <button
              key={s}
              onClick={() => send(s)}
              className="shrink-0 px-3 py-1.5 rounded-full border border-navy-500/50 text-xs text-slate-400 hover:text-slate-200 hover:border-slate-500 transition-colors whitespace-nowrap"
            >
              {s}
            </button>
          ))}
        </div>

        {/* Input */}
        <div className="shrink-0 border-t border-navy-500/40 bg-navy-800 px-4 py-3 flex gap-2">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && send(input)}
            placeholder="Ask about the satellite analysis, uncertainty, or validation results…"
            className="flex-1 bg-navy-700 border border-navy-500/40 rounded-xl px-4 py-2.5 text-sm text-slate-200 placeholder-slate-600 focus:outline-none focus:border-blue-electric/50 transition-colors"
          />
          <button
            onClick={() => send(input)}
            disabled={!input.trim() || thinking}
            className="px-4 py-2 rounded-xl bg-blue-electric text-white text-sm font-display font-600 hover:bg-blue-600 disabled:opacity-40 transition-colors"
          >
            Send
          </button>
        </div>
      </div>

      {/* Context panel */}
      <div className="w-64 shrink-0 bg-navy-800 overflow-y-auto">
        <div className="px-4 py-3 border-b border-navy-500/40">
          <div className="text-xs font-display font-600 text-slate-300 uppercase tracking-wider">Analysis Context</div>
        </div>
        <div className="px-4 py-4 space-y-3">
          {[
            { label: "Input", value: "Sentinel-2 GeoTIFF" },
            { label: "Input Resolution", value: "10m" },
            { label: "Enhanced Resolution", value: "2.5m" },
            { label: "Spectral Consistency", value: "94%" },
            { label: "Avg Confidence", value: "87%" },
            { label: "Low Conf Regions", value: "12 patches" },
            { label: "CRS", value: "EPSG:32643" },
            { label: "Bands", value: "B2,B3,B4,B8,B11,B12" },
          ].map((row) => (
            <div key={row.label} className="flex items-start justify-between gap-2">
              <span className="text-[10px] font-mono text-slate-500">{row.label}</span>
              <span className="text-[10px] font-mono text-slate-300 text-right">{row.value}</span>
            </div>
          ))}
        </div>

        <div className="mx-4 p-3 rounded-xl bg-purple-ai/10 border border-purple-ai/20">
          <div className="text-[10px] font-mono text-purple-ai mb-1 uppercase tracking-widest">Model</div>
          <div className="text-xs text-slate-300 font-medium">llama3.2-vision</div>
          <div className="text-[10px] font-mono text-slate-500 mt-0.5">Running locally · No data leaves device</div>
        </div>

        <div className="px-4 py-4">
          <div className="text-[10px] font-mono text-slate-500 uppercase tracking-widest mb-2">Suggested Analysis</div>
          <div className="space-y-1.5">
            {["Urban density mapping", "Crop classification", "Flood extent detection", "Change detection"].map((t) => (
              <div key={t} className="text-xs text-slate-400 py-1.5 px-2 rounded hover:bg-navy-700 cursor-pointer transition-colors">{t}</div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
