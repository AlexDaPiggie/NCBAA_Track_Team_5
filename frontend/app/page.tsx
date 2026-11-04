"use client";
import { useCallback, useEffect, useState } from "react";
import Copilot from "./components/Copilot";
import { ForecastChart, RiskHeatmap, SeatChart } from "./components/Charts";
import { api, Audit, CopilotOut, Forecast, Metrics, Plan, Risk, ROLE_LABEL, ROLES, Role, Scenario } from "./lib/api";

const SCEN = ["ordinary", "low", "medium", "high"] as const;
const money = (v: number) => `$${Math.round(v).toLocaleString()}`;

function Kpi({ label, base, plan, fmt, lowerBetter }: { label: string; base: number; plan: number; fmt: (v: number) => string; lowerBetter: boolean }) {
  const good = lowerBetter ? plan <= base : plan >= base;
  return (
    <div className="rounded-xl border border-[#1d3441] bg-[#0f2530] p-4">
      <div className="text-xs uppercase tracking-wide text-[#8fa6b2]">{label}</div>
      <div className="mt-1 flex items-baseline gap-2">
        <span className={`text-2xl font-semibold ${good ? "text-[#c5d86d]" : "text-[#f08a7a]"}`}>{fmt(plan)}</span>
        <span className="text-xs text-[#6b8896]">plan</span>
      </div>
      <div className="text-xs text-[#8fa6b2]">ordinary roster: {fmt(base)}</div>
    </div>
  );
}

export default function Home() {
  const [scenario, setScenario] = useState<Scenario | null>(null);
  const [forecast, setForecast] = useState<Forecast | null>(null);
  const [plan, setPlan] = useState<Plan | null>(null);
  const [risk, setRisk] = useState<Risk | null>(null);
  const [audit, setAudit] = useState<Audit[]>([]);
  const [riskZ, setRiskZ] = useState(0.5);
  const [role, setRole] = useState<Role>("ramp");
  const [basis, setBasis] = useState<"expected_demand" | "realized_synthetic_demand">("expected_demand");
  const [showReal, setShowReal] = useState(false);
  const [note, setNote] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [assump, setAssump] = useState<string[]>([]);

  const loadPlan = useCallback(async (p: Plan) => {
    setPlan(p);
    setRisk(null);
    try {
      setRisk(await api.risk(p.id));
    } catch {
      /* risk map is optional */
    }
  }, []);

  const run = useCallback(
    async (name: string, z: number) => {
      setBusy(true);
      setErr(null);
      try {
        const sc = await api.scenario(name);
        setScenario(sc);
        setForecast(await api.forecast(sc.id));
        await loadPlan(await api.plan(sc.id, z));
      } catch (e) {
        setErr((e as Error).message);
      } finally {
        setBusy(false);
      }
    },
    [loadPlan],
  );

  useEffect(() => {
    void Promise.resolve().then(() => run("medium", 0.5));
    api.assumptions().then((a) => setAssump(a.summary)).catch(() => {});
    api.audit().then(setAudit).catch(() => {});
  }, [run]);

  async function replan() {
    if (!scenario) return;
    setBusy(true);
    try {
      await loadPlan(await api.plan(scenario.id, riskZ));
    } catch (e) {
      setErr((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  async function onCopilot(o: CopilotOut) {
    if (!o.scenario_id) return;
    try {
      const sc = await api.getScenario(o.scenario_id);
      setScenario(sc);
      setForecast(await api.forecast(sc.id));
      if (o.plan_id) await loadPlan(await api.getPlan(o.plan_id));
    } catch (e) {
      setErr((e as Error).message);
    }
  }

  async function decide(action: "approve" | "reject") {
    if (!plan) return;
    setPlan(await api.decide(plan.id, action, note));
    setNote("");
    setAudit(await api.audit());
  }

  const cmp = plan?.comparison[basis];
  const m = (k: keyof Metrics, s: "baseline" | "proposed") => (cmp ? cmp[s][k] : 0);
  const statusColor = {
    proposed: "bg-[#e0a43c]/20 text-[#e0a43c]",
    approved: "bg-[#c5d86d]/20 text-[#c5d86d]",
    rejected: "bg-[#e5604d]/20 text-[#e5604d]",
    edited: "bg-[#2e8fb0]/20 text-[#7cc4de]",
  };

  return (
    <main className="min-h-screen bg-[#0b1f2a] text-[#dbe8ee]">
      <header className="flex flex-wrap items-center justify-between gap-3 border-b border-[#1d3441] px-6 py-4">
        <div>
          <h1 className="text-xl font-semibold text-[#f4f7f8]">
            FBO Staffing Planner <span className="font-normal text-[#8fa6b2]">- Super Bowl week, Los Angeles</span>
          </h1>
          <p className="text-sm text-[#c5d86d]">AI assists. People decide.</p>
        </div>
        <span className="rounded-full border border-[#e0a43c]/60 px-3 py-1 text-xs text-[#e0a43c]">SYNTHETIC DATA - not real FBO performance</span>
      </header>

      <div className="mx-auto grid max-w-[1400px] gap-5 p-6 lg:grid-cols-[1fr_380px]">
        <div className="flex min-w-0 flex-col gap-5">
          <section className="flex flex-wrap items-center gap-4 rounded-xl border border-[#1d3441] bg-[#0f2530] p-4">
            <div className="flex gap-1">
              {SCEN.map((s) => (
                <button
                  key={s}
                  disabled={busy}
                  onClick={() => run(s, riskZ)}
                  className={`rounded-lg px-3 py-1.5 text-sm capitalize ${
                    scenario?.name === s && !scenario.disruptions.length ? "bg-[#c5d86d] font-semibold text-[#0b1f2a]" : "border border-[#24485a] hover:bg-[#16384a]"
                  }`}
                >
                  {s}
                </button>
              ))}
            </div>
            <label className="flex items-center gap-2 text-sm">
              <span className="text-[#8fa6b2]">Lean</span>
              <input type="range" min={0} max={1} step={0.25} value={riskZ} onChange={(e) => setRiskZ(+e.target.value)} />
              <span className="text-[#8fa6b2]">Protected</span>
            </label>
            <button disabled={busy || !scenario} onClick={replan} className="rounded-lg border border-[#c5d86d] px-3 py-1.5 text-sm text-[#c5d86d] hover:bg-[#c5d86d]/10 disabled:opacity-50">
              Re-plan at this setting
            </button>
            {busy && <span className="animate-pulse text-sm text-[#c5d86d]">Solving roster...</span>}
            {plan && <span className="ml-auto text-xs text-[#6b8896]">solved in {plan.solve_seconds}s</span>}
          </section>

          {err && <div className="rounded-lg border border-[#e5604d]/60 bg-[#e5604d]/10 p-3 text-sm text-[#f08a7a]">{err}. Is the backend running on port 8000?</div>}

          {plan && cmp && (
            <>
              <div className="flex items-center gap-2 text-xs text-[#8fa6b2]">
                Scored on:
                <button onClick={() => setBasis("expected_demand")} className={`rounded px-2 py-0.5 ${basis === "expected_demand" ? "bg-[#16384a] text-[#f4f7f8]" : ""}`}>forecast (expected)</button>
                <button onClick={() => setBasis("realized_synthetic_demand")} className={`rounded px-2 py-0.5 ${basis === "realized_synthetic_demand" ? "bg-[#16384a] text-[#f4f7f8]" : ""}`}>one synthetic reality</button>
                <span className="text-[#6b8896]">Same demand for both rosters.</span>
              </div>
              <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
                <Kpi label="Coverage" base={m("coverage_pct", "baseline")} plan={m("coverage_pct", "proposed")} fmt={(v) => `${v.toFixed(1)}%`} lowerBetter={false} />
                <Kpi label="Understaffed hours" base={m("understaffed_hours", "baseline")} plan={m("understaffed_hours", "proposed")} fmt={(v) => `${v}`} lowerBetter />
                <Kpi label="Short seat-hours" base={m("understaffed_seat_hours", "baseline")} plan={m("understaffed_seat_hours", "proposed")} fmt={(v) => `${v}`} lowerBetter />
                <Kpi label="Labor cost (illustrative)" base={m("labor_cost_usd", "baseline")} plan={m("labor_cost_usd", "proposed")} fmt={money} lowerBetter />
              </div>
            </>
          )}

          {forecast && (
            <section className="rounded-xl border border-[#1d3441] bg-[#0f2530] p-4">
              <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
                <h2 className="font-semibold text-[#f4f7f8]">Demand forecast vs ordinary week</h2>
                <label className="flex items-center gap-2 text-xs text-[#8fa6b2]">
                  <input type="checkbox" checked={showReal} onChange={(e) => setShowReal(e.target.checked)} /> show synthetic reality
                </label>
              </div>
              <ForecastChart points={forecast.points} showReal={showReal} disruptions={scenario?.disruptions ?? []} />
              <div className="mt-2 flex flex-wrap gap-4 text-xs text-[#8fa6b2]">
                <span><b className="text-[#c5d86d]">-</b> expected</span>
                <span><b className="text-[#2e8fb0]">shaded</b> P10-P90</span>
                <span>dashed = ordinary week</span>
                {scenario?.disruptions.length ? <span className="text-[#e0a43c]">amber = disruption</span> : null}
              </div>
              <div className="mt-3 grid gap-3 text-sm sm:grid-cols-3">
                <div className="rounded-lg bg-[#0a1a22] p-3">
                  <div className="text-xs text-[#8fa6b2]">Hourly error (WAPE), holdout</div>
                  <div>model <b className="text-[#c5d86d]">{(forecast.metrics.backtest.wape_hourly * 100).toFixed(0)}%</b> vs naive {(forecast.metrics.backtest.naive_wape_hourly * 100).toFixed(0)}%</div>
                </div>
                <div className="rounded-lg bg-[#0a1a22] p-3">
                  <div className="text-xs text-[#8fa6b2]">Daily error, holdout</div>
                  <div>model <b className="text-[#c5d86d]">{(forecast.metrics.backtest.mape_daily * 100).toFixed(0)}%</b> vs naive {(forecast.metrics.backtest.naive_mape_daily * 100).toFixed(0)}%</div>
                </div>
                <div className="rounded-lg bg-[#0a1a22] p-3">
                  <div className="text-xs text-[#8fa6b2]">P10-P90 coverage (target 80%)</div>
                  <div><b className="text-[#c5d86d]">{(forecast.metrics.backtest.interval_coverage_p10_p90 * 100).toFixed(0)}%</b></div>
                </div>
              </div>
              <p className="mt-2 text-[11px] text-[#6b8896]">Accuracy is on a synthetic ordinary week. Event uplift is an assumption, not learned.</p>
            </section>
          )}

          {plan && (
            <section className="rounded-xl border border-[#1d3441] bg-[#0f2530] p-4">
              <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
                <h2 className="font-semibold text-[#f4f7f8]">Seats required vs scheduled</h2>
                <div className="flex gap-1">
                  {ROLES.map((r) => (
                    <button key={r} onClick={() => setRole(r)} className={`rounded px-2 py-1 text-xs ${role === r ? "bg-[#c5d86d] font-semibold text-[#0b1f2a]" : "border border-[#24485a]"}`}>
                      {ROLE_LABEL[r]}
                    </button>
                  ))}
                </div>
              </div>
              <SeatChart required={plan.required_seats[role]} supply={plan.supply_seats[role] ?? []} role={role} />
              <p className="text-[11px] text-[#6b8896]">Green dashed = seats the plan basis needs. Blue = on duty (break hour counts half). Red = short.</p>
            </section>
          )}

          {risk && (
            <section className="rounded-xl border border-[#1d3441] bg-[#0f2530] p-4">
              <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
                <h2 className="font-semibold text-[#f4f7f8]">Risk of understaffing ({risk.sims} simulated weeks)</h2>
                <span className="text-xs text-[#8fa6b2]">expected short seat-hours {risk.expected_short_seat_hours} | bad week (P90) {risk.p90_short_seat_hours}</span>
              </div>
              <RiskHeatmap p={risk.p_understaffed} />
            </section>
          )}
        </div>

        <aside className="flex flex-col gap-5">
          <Copilot scenarioId={scenario?.id ?? null} onResult={onCopilot} />

          {plan && (
            <section className="flex flex-col gap-3 rounded-xl border border-[#1d3441] bg-[#0f2530] p-4">
              <div className="flex items-center justify-between">
                <h2 className="font-semibold text-[#f4f7f8]">Manager approval</h2>
                <span className={`rounded-full px-2 py-0.5 text-xs ${statusColor[plan.status]}`}>{plan.status}</span>
              </div>
              <ul className="list-disc space-y-1 pl-4 text-sm text-[#cfe0e8]">
                {plan.rationale.map((r, i) => (<li key={i}>{r}</li>))}
              </ul>
              <input value={note} onChange={(e) => setNote(e.target.value)} placeholder="Note (optional)" className="rounded-lg border border-[#24485a] bg-[#0a1a22] px-3 py-2 text-sm outline-none focus:border-[#c5d86d]" />
              <div className="flex gap-2">
                <button onClick={() => decide("approve")} className="flex-1 rounded-lg bg-[#c5d86d] py-2 text-sm font-semibold text-[#0b1f2a]">Approve</button>
                <button onClick={() => decide("reject")} className="flex-1 rounded-lg border border-[#e5604d] py-2 text-sm text-[#f08a7a]">Reject</button>
              </div>
              <p className="text-[11px] text-[#6b8896]">Approval records a decision only. Nothing is dispatched and no movement is authorized.</p>
              {audit.length > 0 && (
                <div className="space-y-1 border-t border-[#1d3441] pt-2 text-xs text-[#8fa6b2]">
                  <div className="font-semibold text-[#cfe0e8]">Audit log</div>
                  {audit.slice(-4).reverse().map((a, i) => (
                    <div key={i}>{new Date(a.ts).toLocaleTimeString()} - {a.actor} {a.action} {a.plan_id}{a.note ? `: ${a.note}` : ""}</div>
                  ))}
                </div>
              )}
            </section>
          )}

          <section className="rounded-xl border border-[#1d3441] bg-[#0f2530] p-4 text-sm">
            <h2 className="mb-2 font-semibold text-[#f4f7f8]">AI never does</h2>
            <ul className="list-disc space-y-1 pl-4 text-[#cfe0e8]">
              <li>Dispatch workers or assign live tasks</li>
              <li>Authorize aircraft or vehicle movements</li>
              <li>Use passenger or sensitive data</li>
              <li>Approve its own plan</li>
            </ul>
          </section>

          <details className="rounded-xl border border-[#1d3441] bg-[#0f2530] p-4 text-sm">
            <summary className="cursor-pointer font-semibold text-[#f4f7f8]">Assumptions (unverified)</summary>
            <ul className="mt-2 list-disc space-y-1 pl-4 text-[#cfe0e8]">
              {(plan?.assumptions ?? assump).map((a, i) => (<li key={i}>{a}</li>))}
            </ul>
          </details>
        </aside>
      </div>
    </main>
  );
}
