# Demo script — CrewPilot AI

**Target length:** 3 minutes for rehearsal. The Track 1 slides do not state a pitch duration; confirm with organizers. Track 2 explicitly mentions a 3-minute pitch.

## 0:00–0:25 — Problem and guardrails

“An FBO manager has to prepare staffing for an event week without knowing exactly when workload will peak. CrewPilot is a staffing planning aid: it uses synthetic data today, makes its assumptions visible, and leaves every schedule decision with the manager.”

## 0:25–0:55 — Baseline versus event week

Open **Baseline vs Event Week**. Show the ordinary profile, selected event case, hourly chart, and 42 four-hour demand blocks. Explain that the default is synthetic; the optional JFK pattern is airline proxy data, not LAX or business-aviation observations.

## 0:55–1:35 — Proposed coverage

Open **Gap Heatmap** and inspect the four-hour grid. State that this integration currently covers three departments; the requested seven-zone role matrix is not connected yet. Then open **Recommended Plan**, keep the synthetic shift assumptions, and build baseline and event rosters. Mention that workforce rules and wages are assumptions, not validated aviation policy.

## 1:35–2:20 — Disruption stress test

Open **Scenario Comparison** to show low, medium, and high demand. Build the selected roster, then compare coverage, uncovered blocks, severe gaps, modeled labor-cost change, and the illustrative ramp delay-risk proxy against the unchanged ordinary-week schedule under the same event demand and disruption. Action hours and reserve counts are not modeled. The delay-risk proxy is an assumed indicator, not a delay forecast.

## 2:20–2:45 — Human approval

On **Recommended Plan**, show the roster review. A manager can approve or reject it with notes. Open **Assumptions & Safety** and state: “CrewPilot never dispatches staff, authorizes aircraft movement, or handles passenger information.”

## 2:45–3:00 — Close

“CrewPilot turns an uncertain event forecast into a staffing plan the manager can inspect, stress-test, and approve. The next step is validating task and workforce assumptions with an FBO operations expert.”

## Demo checklist

- Reset to fixed seed before presenting.
- Verify ordinary/event and low/medium/high labels are visible.
- Confirm the disruption affects baseline and proposal equally.
- Point out that the scenario comparison uses the same event demand and disruption for both rosters; explain the delay-risk proxy assumption.
- Use only metrics produced by the current run.
- Keep synthetic label and approval-pending state visible.
- Have a screenshot/recording fallback if the live environment fails.
