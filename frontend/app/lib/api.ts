export const API = process.env.NEXT_PUBLIC_API ?? "http://localhost:8000";

export type Role = "ramp" | "fuel" | "cs";
export const ROLES: Role[] = ["ramp", "fuel", "cs"];
export const ROLE_LABEL: Record<Role, string> = { ramp: "Ramp", fuel: "Fuel", cs: "Customer service" };
export const DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

export interface Scenario { id: string; name: string; intensity: number; disruptions: Disruption[]; parent_id: string | null }
export interface Disruption { kind: "spike" | "delay" | "cancel"; start_hour: number; end_hour: number; extra_arrivals?: number; note?: string }
export interface FPoint { day: number; hour: number; p10: number; expected: number; p90: number; ordinary_expected: number; realized_synthetic: number }
export interface Metrics { coverage_pct: number; understaffed_seat_hours: number; understaffed_hours: number; idle_seat_hours: number; paid_hours: number; labor_cost_usd: number }
export interface Forecast {
  scenario_id: string; points: FPoint[];
  daily: { forecast: number[]; realized_synthetic: number[]; ordinary: number[] };
  metrics: {
    backtest: { wape_hourly: number; naive_wape_hourly: number; mape_daily: number; naive_mape_daily: number; interval_coverage_p10_p90: number; target_coverage: number };
    scenario_check: { wape_hourly: number; interval_coverage_p10_p90: number; mape_daily: number; note: string };
  };
}
export interface Shift { worker_id: string; role: Role; day: number; start_hour: number; end_hour: number; break_hour: number }
export interface Plan {
  id: string; scenario_id: string; status: "proposed" | "approved" | "rejected" | "edited"; risk_z: number;
  shifts: Shift[]; baseline_shifts: Shift[]; solve_seconds: number;
  comparison: { baseline_definition: string; expected_demand: { baseline: Metrics; proposed: Metrics }; realized_synthetic_demand: { baseline: Metrics; proposed: Metrics } };
  required_seats: Record<Role, number[]>; supply_seats: Record<Role, number[]>;
  assumptions: string[]; rationale: string[];
}
export interface Risk { p_understaffed: number[]; by_role: Record<Role, number[]>; expected_short_seat_hours: number; p90_short_seat_hours: number; sims: number }
export interface Audit { plan_id: string; action: string; actor: string; note: string; ts: string }
export interface ToolCall { name: string; args: Record<string, unknown>; result: Record<string, unknown> }
export interface CopilotOut { reply: string; tool_calls: ToolCall[]; scenario_id: string | null; plan_id: string | null; model: string }

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const r = await fetch(`${API}${path}`, { ...init, headers: { "Content-Type": "application/json" } });
  if (!r.ok) throw new Error(`${path}: ${r.status} ${await r.text()}`);
  return r.json();
}
export const api = {
  scenario: (name: string, disruptions: Disruption[] = []) => req<Scenario>("/scenarios", { method: "POST", body: JSON.stringify({ name, disruptions }) }),
  forecast: (id: string) => req<Forecast>(`/forecast?scenario_id=${id}`),
  plan: (scenario_id: string, risk_z: number) => req<Plan>("/plan", { method: "POST", body: JSON.stringify({ scenario_id, risk_z }) }),
  getPlan: (id: string) => req<Plan>(`/plan/${id}`),
  risk: (id: string) => req<Risk>(`/risk?plan_id=${id}`),
  decide: (plan_id: string, action: "approve" | "reject", note: string) => req<Plan>("/decision", { method: "POST", body: JSON.stringify({ plan_id, action, actor: "manager", note }) }),
  audit: () => req<Audit[]>("/audit"),
  assumptions: () => req<{ summary: string[]; unverified: string }>("/assumptions"),
  copilot: (message: string, scenario_id: string | null) => req<CopilotOut>("/copilot", { method: "POST", body: JSON.stringify({ message, scenario_id }) }),
  getScenario: (id: string) => req<Scenario>(`/scenario/${id}`),
};
