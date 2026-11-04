"use client";
import { DAYS, FPoint, Role } from "../lib/api";

const W = 860, H = 220, PL = 36, PR = 8, PT = 10, PB = 22;
const iw = W - PL - PR, ih = H - PT - PB;
const x = (t: number) => PL + (t / 167) * iw;

function Axes({ max, label }: { max: number; label: string }) {
  const ticks = [0, 0.5, 1].map((f) => f * max);
  return (
    <g className="text-[10px]" fill="#8fa6b2">
      {ticks.map((v) => {
        const y = PT + ih - (v / max) * ih;
        return (<g key={v}><line x1={PL} x2={W - PR} y1={y} y2={y} stroke="#1d3441" /><text x={PL - 4} y={y + 3} textAnchor="end">{v.toFixed(max < 5 ? 1 : 0)}</text></g>);
      })}
      {DAYS.map((d, i) => (<g key={d}><line x1={x(i * 24)} x2={x(i * 24)} y1={PT} y2={PT + ih} stroke="#1d3441" strokeDasharray="2 3" /><text x={x(i * 24 + 12)} y={H - 6} textAnchor="middle">{d}</text></g>))}
      <text x={PL} y={8}>{label}</text>
    </g>
  );
}

export function ForecastChart({ points, showReal, disruptions }: { points: FPoint[]; showReal: boolean; disruptions: { start_hour: number; end_hour: number }[] }) {
  const max = Math.max(1, ...points.map((p) => Math.max(p.p90, p.realized_synthetic, p.ordinary_expected))) * 1.1;
  const y = (v: number) => PT + ih - (v / max) * ih;
  const band = points.map((p, t) => `${x(t)},${y(p.p90)}`).join(" ") + " " + [...points].reverse().map((p, i) => `${x(167 - i)},${y(p.p10)}`).join(" ");
  const line = (k: "expected" | "ordinary_expected") => points.map((p, t) => `${t ? "L" : "M"}${x(t)},${y(p[k])}`).join(" ");
  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="w-full" role="img" aria-label="Hourly arrivals forecast">
      <Axes max={max} label="aircraft arrivals / hour (SYNTHETIC)" />
      {disruptions.map((d, i) => (<rect key={i} x={x(d.start_hour)} y={PT} width={Math.max(2, x(d.end_hour) - x(d.start_hour))} height={ih} fill="#e0a43c" opacity={0.18} />))}
      <polygon points={band} fill="#2e8fb0" opacity={0.22} />
      <path d={line("ordinary_expected")} fill="none" stroke="#8fa6b2" strokeWidth={1.2} strokeDasharray="4 3" />
      <path d={line("expected")} fill="none" stroke="#c5d86d" strokeWidth={1.8} />
      {showReal && points.map((p, t) => (<circle key={t} cx={x(t)} cy={y(p.realized_synthetic)} r={1.8} fill="#f4f7f8" opacity={0.75} />))}
    </svg>
  );
}

export function SeatChart({ required, supply, role }: { required: number[]; supply: number[]; role: Role }) {
  const max = Math.max(1, ...required, ...supply) * 1.15;
  const y = (v: number) => PT + ih - (v / max) * ih;
  const step = (arr: number[]) => arr.map((v, t) => `${t ? "L" : "M"}${x(t)},${y(v)} L${x(t + 1 > 167 ? 167 : t + 1)},${y(v)}`).join(" ");
  const gaps = required.map((r, t) => (r - (supply[t] ?? 0) > 1e-9 ? t : -1)).filter((t) => t >= 0);
  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="w-full" role="img" aria-label={`Seats required vs scheduled, ${role}`}>
      <Axes max={max} label="seats (required vs on duty)" />
      {gaps.map((t) => (<rect key={t} x={x(t)} y={PT} width={iw / 167} height={ih} fill="#e5604d" opacity={0.28} />))}
      <path d={step(supply)} fill="none" stroke="#2e8fb0" strokeWidth={1.8} />
      <path d={step(required)} fill="none" stroke="#c5d86d" strokeWidth={1.6} strokeDasharray="5 3" />
    </svg>
  );
}

export function RiskHeatmap({ p }: { p: number[] }) {
  const cw = (W - 46) / 24, ch = 20;
  const color = (v: number) => (v < 0.05 ? "#12303c" : `rgba(229,96,77,${0.2 + 0.8 * Math.min(1, v * 1.5)})`);
  return (
    <svg viewBox={`0 0 ${W} ${7 * ch + 22}`} className="w-full" role="img" aria-label="Probability of understaffing by hour">
      {DAYS.map((d, i) => (<text key={d} x={0} y={i * ch + 14} fontSize={10} fill="#8fa6b2">{d}</text>))}
      {p.map((v, t) => {
        const d = Math.floor(t / 24), h = t % 24;
        return (<rect key={t} x={34 + h * cw} y={d * ch} width={cw - 1} height={ch - 1} rx={2} fill={color(v)}><title>{`${DAYS[d]} ${h}:00 - ${(v * 100).toFixed(0)}% chance short`}</title></rect>);
      })}
      {[0, 6, 12, 18].map((h) => (<text key={h} x={34 + h * cw} y={7 * ch + 14} fontSize={10} fill="#8fa6b2">{h}:00</text>))}
    </svg>
  );
}
