"use client";
import { useState } from "react";
import { api, CopilotOut, ToolCall } from "../lib/api";

interface Turn { role: "user" | "ai"; text: string; calls?: ToolCall[]; model?: string }
const SUGGEST = [
  "Rain delay Friday, 12 extra jets arrive between 6pm and midnight. Re-plan and tell me what changes.",
  "What if Super Bowl demand is high? Is a lean plan risky?",
  "Which hours are riskiest in the current plan?",
];

export default function Copilot({ scenarioId, onResult }: { scenarioId: string | null; onResult: (o: CopilotOut) => void }) {
  const [turns, setTurns] = useState<Turn[]>([]);
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const [open, setOpen] = useState<number | null>(null);

  async function send(msg: string) {
    if (!msg.trim() || busy) return;
    setTurns((t) => [...t, { role: "user", text: msg }]);
    setText(""); setBusy(true);
    try {
      const out = await api.copilot(msg, scenarioId);
      setTurns((t) => [...t, { role: "ai", text: out.reply, calls: out.tool_calls, model: out.model }]);
      onResult(out);
    } catch (e) {
      setTurns((t) => [...t, { role: "ai", text: `Error: ${(e as Error).message}` }]);
    } finally { setBusy(false); }
  }

  return (
    <section className="rounded-xl border border-[#1d3441] bg-[#0f2530] p-4 flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <h2 className="font-semibold text-[#f4f7f8]">AI co-pilot</h2>
        <span className="text-xs text-[#8fa6b2]">Calls the forecast + solver. Recommends only.</span>
      </div>
      <div className="flex flex-col gap-3 max-h-[420px] overflow-y-auto pr-1">
        {turns.length === 0 && (
          <div className="flex flex-col gap-2">
            {SUGGEST.map((s) => (
              <button key={s} onClick={() => send(s)} className="text-left text-sm rounded-lg border border-[#24485a] px-3 py-2 text-[#cfe0e8] hover:bg-[#16384a]">{s}</button>
            ))}
          </div>
        )}
        {turns.map((t, i) => (
          <div key={i} className={t.role === "user" ? "self-end max-w-[90%] rounded-lg bg-[#16384a] px-3 py-2 text-sm text-[#f4f7f8]" : "max-w-full text-sm text-[#dbe8ee]"}>
            {t.calls && t.calls.length > 0 && (
              <div className="mb-2 flex flex-wrap gap-1">
                {t.calls.map((c, j) => (
                  <button key={j} onClick={() => setOpen(open === i * 100 + j ? null : i * 100 + j)} className="rounded-full border border-[#c5d86d]/50 px-2 py-0.5 text-[11px] font-mono text-[#c5d86d] hover:bg-[#c5d86d]/10">
                    {c.name}({Object.keys(c.args).join(", ")})
                  </button>
                ))}
              </div>
            )}
            {t.calls?.map((c, j) => open === i * 100 + j && (
              <pre key={j} className="mb-2 max-h-48 overflow-auto rounded bg-[#0a1a22] p-2 text-[11px] text-[#9fc0cf]">{JSON.stringify({ args: c.args, result: c.result }, null, 1)}</pre>
            ))}
            <div className="whitespace-pre-wrap">{t.text}</div>
            {t.model && <div className="mt-1 text-[10px] text-[#6b8896]">{t.model}</div>}
          </div>
        ))}
        {busy && <div className="text-sm text-[#c5d86d] animate-pulse">Running forecast + solver tools...</div>}
      </div>
      <form onSubmit={(e) => { e.preventDefault(); send(text); }} className="flex gap-2">
        <input value={text} onChange={(e) => setText(e.target.value)} placeholder="Describe a disruption or ask a question" className="flex-1 rounded-lg border border-[#24485a] bg-[#0a1a22] px-3 py-2 text-sm text-[#f4f7f8] outline-none focus:border-[#c5d86d]" />
        <button disabled={busy} className="rounded-lg bg-[#c5d86d] px-4 py-2 text-sm font-semibold text-[#0b1f2a] disabled:opacity-50">Send</button>
      </form>
    </section>
  );
}
