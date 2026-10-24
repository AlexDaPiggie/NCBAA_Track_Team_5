# CrewPilot AI brainstorm

## Organizer constraints and evidence

The NCBAA slide deck asks Track 1 teams to prepare an FBO for the seven-day window around Super Bowl LXI week in Los Angeles, select exactly one operational pressure point, model using public or synthetic data, and document assumptions. It calls for ordinary-week versus Super Bowl demand, low/medium/high preparation scenarios, impact and forecast accuracy, uncertainty, privacy, and human authority. AI provides planning support only; no movement authority; no sensitive passenger data. The deck does not publish staffing policies, a dataset, deadline, or scoring weights; those remain unknown. Source: `docs/Aviation Tracks.pdf`, slides “The Intelligent FBO,” “From forecast to field plan,” and “Human in command.”

## Product variations

Scores are qualitative for this hackathon (1 low, 5 high), not measured market findings.

| Concept | Operational pain | Novelty vs existing software | Judging appeal | 48-hour feasibility | Data need | Safety |
|---|---:|---:|---:|---:|---|---|
| A. Event-week staffing stress tester | 5 | 3 | 5 | 4 | Synthetic hourly arrivals/tasks, roles/skills, shifts and absences | 5 |
| B. Day-of call-out replacement matcher | 4 | 2 | 4 | 3 | Real employee skills, availability, labor rules and contact workflow | 2 |
| C. Shift demand forecast dashboard | 4 | 2 | 3 | 5 | Historical task/arrival data or synthetic series | 5 |

### A. Event-week staffing stress tester — recommended

A manager compares ordinary-week coverage to a seven-day event scenario, picks low/medium/high demand, then injects a traffic surge or staff call-outs. The app recomputes coverage for both the baseline and recommendation against the same demand and disruption. It reports uncovered workload, overtime, labor hours/cost (if configured), and why the proposed schedule changed. This speaks directly to the organizer’s requested workflow and supports a clear live demo. Existing operations products already provide traffic visibility and staffing-planning support: FlightBridge says upcoming traffic can inform staffing/equipment planning ([FlightBridge FBO Operations](https://home.flightbridge.com/solutions/fbo-operations)); Aerosimple describes shift scheduling and staffing-gap visibility ([Aerosimple Shift Management](https://www.aerosimple.com/solutions/shift-management)). Novelty is therefore a hypothesis about the interactive, explainable scenario comparison, not a verified market gap. No performance improvement is established until our same-scenario comparison runs.

### B. Call-out replacement matcher

Suggest qualified available staff to cover an open shift. This addresses immediate supervisor work, but needs credible employee data, availability, overtime/rest policies, and possibly notifications. Those are unprovided and sensitive. A safe hackathon version can use synthetic workers and manager-only review, but it risks feeling like a narrow roster tool and may imply dispatch. Exclude from the MVP.

### C. Demand forecast dashboard

Forecast hourly service workload from prior weeks and show uncertainty bands. Easiest to implement and validate with a held-out synthetic week, but without a coverage plan it does not complete the organizer’s forecast-to-field-plan workflow. Existing products already surface upcoming traffic and staffing visibility. Use forecast as one component, not the whole product.

## Recommendation

Build A: **CrewPilot AI — Super Bowl FBO Staffing Stress Tester**. Keep scope to FBO staffing. The MVP should demonstrate a transparent demand model, fair baseline/proposed comparison, explicit configurable workforce constraints, disruption recomputation, and manager approval. Use deterministic synthetic fixtures and label every result synthetic. Do not use generative AI for optimization; an explainable deterministic scheduler is more credible in 48 hours. Treat all labor constraints as configurable demo assumptions pending review by an FBO staffing expert.

## Claims and limits

- Documented fact: the organizer wants one focus, and staffing is an allowed focus.
- Documented fact: the organizer asks for a seven-day Super Bowl week plan, ordinary-week comparison, three demand levels, impact measurement, uncertainty and human authority.
- Product-page evidence: some existing aviation/FBO tools advertise traffic-informed staffing or shift management. This does not establish feature parity or market coverage.
- Assumption: hourly synthetic arrival demand can stand in for task workload after configurable service-time multipliers.
- Hypothesis: interactive disruption comparison is a useful differentiator; validate with judges/mentors.
- Unverified: staffing roles, qualifications, break rules, maximum hours, rest periods, costs, FBO task durations, and any actual event-week demand. No aviation staffing expert has validated these assumptions.
- Safety: planning recommendations only. A manager reviews and approves; no dispatch, movement authorization, or passenger data.

## Full-day mission replay decision

The track asks for a seven-day Super Bowl planning window. It does not require a specific daily operating window. Extending the selected-day replay to 24 hours addresses overnight staffing gaps while keeping the focus on staffing.

| Option | Operational pain | Novelty | Judging fit | 48-hour feasibility | Data need | Safety / risk |
|---|---|---|---|---|---|---|
| A. Full-day replay with three fixed shifts | Covers overnight gaps and late service | Moderate; makes the existing stress test more complete | Strong; shows full-day coverage | High; reuse task and disruption model | Synthetic 24-hour profile and shift assumptions | Safe if assumptions stay labeled; low-medium risk |
| B. Show 24-hour demand, keep 12:00–20:00 staffing | Leaves overnight coverage unknown | Low | Weak; demand and capacity use different windows | High | Same as current | Misleading comparison; medium risk |
| C. Build a rolling multi-day roster with rotating shifts | Models handoffs, carryover, and rest across dates | Moderate | Strong but broader | Low; requires a new roster and optimizer | Multi-day worker availability and validated rules | More safety and validation work; high risk |

**Decision: Option A.** Use 00:00–24:00 arrivals and capacity, with fixed 00:00–08:00, 08:00–16:00, and 16:00–24:00 synthetic shifts. Fixed daily shifts give each fictional worker 16 hours between shifts. Carry late services through 02:00 the next day so deadlines after midnight can still receive qualified crew. Keep 14:00 as the reproducible disruption checkpoint. These are prototype assumptions, not verified VNY operating or labor rules. A full rotating seven-day employee roster remains a separate planning view.
