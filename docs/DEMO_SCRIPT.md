# Demo script — CrewPilot AI

**Target length:** 3 minutes for rehearsal. The Track 1 slides do not state a pitch duration; confirm with organizers. Track 2 explicitly mentions a 3-minute pitch.

## 0:00–0:25 — Problem and guardrails

“An FBO manager has to prepare staffing for an event week without knowing exactly when workload will peak. CrewPilot is a staffing planning aid: it uses synthetic data today, makes its assumptions visible, and leaves every schedule decision with the manager.”

## 0:25–0:55 — Baseline versus event week

Show the ordinary synthetic week next to the seven-day event cases. Switch among low, medium, and high. Point to the held-out forecast error on the Demand page and say it measures generated data only, not FBO accuracy.

## 0:55–1:35 — Proposed coverage

Show hourly workload and required staff seats. Open Shift Planner, keep the visible synthetic shift assumptions, and build baseline and event rosters. Point out that shifts obey the configured weekly cap and rest gap, with staggered breaks. Mention that workforce rules and wages are assumptions, not validated aviation policy.

## 1:35–2:20 — Disruption stress test

Open Stress Test. Keep two call-outs, a 50% arrival surge, and a 25% service delay. Run the comparison and show uncovered seat-hours for both rosters under the same event demand and disruption. If the 30-worker synthetic pool cannot fill a shift, show the unfilled slots plainly.

## 2:20–2:45 — Human approval

Show the roster as pending. A manager can approve or reject it with notes. State: “CrewPilot never dispatches staff, authorizes aircraft movement, or handles passenger information.”

## 2:45–3:00 — Close

“CrewPilot turns an uncertain event forecast into a staffing plan the manager can inspect, stress-test, and approve. The next step is validating task and workforce assumptions with an FBO operations expert.”

## Demo checklist

- Reset to fixed seed before presenting.
- Verify ordinary/event and low/medium/high labels are visible.
- Confirm the disruption affects baseline and proposal equally.
- Use only metrics produced by the current run.
- Keep synthetic label and approval-pending state visible.
- Have a screenshot/recording fallback if the live environment fails.
