# CrewPilot AI operations command center

## Current direction

The user's latest request replaces the earlier light guided design with a premium dark aviation dashboard. Use Next.js App Router, TypeScript, Tailwind CSS, shadcn/ui, and Recharts. Prioritize Mission Control and Crisis Mode; keep the product focused on staffing.

## Page structure

1. Mission Control: synthetic arrival wave, qualified staffing capacity, service workload, operational risk, task activity, compact workforce timeline.
2. Workforce Timeline: inspect worker assignments and service tasks, identify uncovered work and eligibility constraints.
3. Crisis Mode: unexpected arrivals, named synthetic worker absences, and actual arrival-time delays. Make the change from the original plan explicit.
4. Recovery Planner: recompute a candidate task assignment plan; explain changed workers/times and remaining gaps. Manager approves or rejects a draft.

## Options assessed

| Experience | Pain / novelty | Judging | Feasibility / data | Safety / 48-hour risk |
| --- | --- | --- | --- | --- |
| Aviation command center (selected) | Highlights flight-triggered work and disruption consequences; novelty remains unverified | Clear visual cause and effect | Deterministic synthetic flights, staff, skills, shifts, breaks, service durations | Planning-only; moderate integration risk, core demo first |
| Generic employee roster | Shift administration pain; crowded category | Weak aviation story | Existing weekly scheduler | Low technical risk, poor fit to requested experience |
| Animated airport digital twin | Memorable activity visualization; no verified novelty | Strong visuals but can hide missing computation | Needs geometry and reliable operational data | High execution risk; can imply movement authority; exclude |

## Component architecture

- App Router shell and route metadata; shared command-center client workspace.
- Local shadcn/ui components: buttons, cards, badges, dialogs, tabs, sliders/tooltips as needed.
- Typed domain: synthetic aircraft visits, service tasks, qualified workers, shift/break windows, assignments, disruptions, coverage metrics, recovery explanations, review records.
- Deterministic fixture generator and pure scheduling/replay functions. No baked-in improvement percentages.
- Typed provider boundary for the synthetic demo and a later FastAPI integration. Existing backend APIs and CSV work remain available.
- Recharts workload/capacity chart, task timeline, aircraft service feed, crisis controls, recovery/approval panel.

## Phases

1. Migrate frontend to Next.js and establish dark navy/cyan/green/amber/red design tokens. Static export preserves the optional desktop package.
2. Implement deterministic demo data, skill/shift/break-aware task assignments, and fixed-original-plan evaluation after disruptions. Arrival delay shifts flight/task times; it is not service-duration inflation.
3. Implement Mission Control and Crisis Mode, then reusable timeline/recovery/report views using the same computed data. Replanning is a transparent greedy heuristic, not a proven global optimum. Recommendations explain worker or time changes.
4. Add local manager review, source/uncertainty details, optional aggregate CSV input, reduced-motion behavior, responsive layouts, meaningful engine tests, and production build checks.

## Evidence and guardrails

- Aircraft, employee identities, tasks, and disruptions are synthetic. Airport operations context does not establish FBO workload.
- Baseline, disrupted-original, and recovery candidates use the same demand realization for the comparison at issue.
- Exact worker assignments obey department qualification, shift boundaries, breaks, and non-overlap. Uncovered work remains visible.
- Fixed staffing means a recovery may improve task coverage without reducing labor cost. Report actual results, including zero or worse improvements.
- No actual dispatch, worker notification, sensitive passenger information, or aircraft movement control.
- Browser inspection was blocked in this turn by Computer Use's inability to verify Chrome's current URL. Do not claim visual walkthrough completion; use build, pure-engine, and HTTP checks and disclose the remaining limitation.

## Implemented and checked

- Readability update: persistent light/dark theme switch in the top bar; light default, saved palette applied before first paint. Light surfaces, navy text, darker status/chart colors, and portal/timeline coverage. Contrast and saved-theme initialization have targeted checks.

- Mission Control and Crisis Mode are functional, with shared timeline, task inspector, recovery explanations, local manager review, CSV input.
- Migrated to Next.js 16 App Router, Tailwind, official shadcn/ui source components, and Recharts. Static export is copied to the existing desktop asset directory.
- Eleven frontend tests pass: CSV validation, deterministic fixtures, qualification/shift/break/non-overlap constraints, fixed-original crisis evaluation, frozen past work, infeasible full absence, configurable task rules, and upload limits.
- Thirty-eight backend regression tests pass for the retained weekly planner.
- TypeScript and final Next.js production/static export pass. Local HTTP response is 200 and includes the new Mission Control, Crisis Mode navigation, and synthetic-data labels.
- Manual visual/mobile walkthrough remains unverified because of the Computer Use block. Task-level FastAPI integration and full-week employee constraints remain separate future work; the local demo never claims those are connected.
