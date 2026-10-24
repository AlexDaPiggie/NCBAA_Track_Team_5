# Guided staffing planner rebuild

Superseded by the user's subsequent dark command-center request. See `docs/COMMAND_CENTER_PLAN.md` for current implementation scope. CSV and backend validation work from this plan remain useful.

## Accepted requirements

- The Intelligent FBO track; staffing is the only operational focus.
- Four guided steps: demand, staffing plan, disruption test, manager review.
- Light aviation design: white, navy, blue; plain language and responsive layouts.
- Open with a ready synthetic Super Bowl demo; optional ordinary-week CSV upload.
- Replace the current website experience. Retain the working Python scheduling engine.

## Product variations considered

| Variation | Operational pain / novelty | Judging appeal | Feasibility and data | Safety / 48-hour risk |
| --- | --- | --- | --- | --- |
| Guided event-week planner (selected) | Makes the forecast-to-staffing decision understandable. Workflow novelty unverified. | Clear beginning, disruption, comparison, decision. | Existing engine plus hourly baseline CSV; practical within current stack. | Draft recommendations; moderate UI work, bounded data schema. |
| Single operations dashboard | Fast for experienced supervisors; similar to existing products. | Many outputs compete for attention. | Easiest build; same synthetic inputs. | Can confuse capacity with real authority; low build risk, high clarity risk. |
| Separate judge demo and manager workspace | Tailored explanation but duplicates paths. Novelty unverified. | Strong presentation potential. | Two experiences to maintain; same data required. | More state and test surface; high execution risk. |

Recommend the guided planner: every step answers one manager question, uses calculated outputs, and supports a short live pitch. Existing brainstorm/research notes document vendor capabilities; no new market gap is claimed.

## Data contract

CSV contains exactly 168 hourly rows for one ordinary week: `hour,aircraft,passengers,fuel_requests`. Hour is 0–167, unique and complete. Other columns, nonfinite values, negatives, and oversized inputs are rejected. Counts are aggregates; no names or passenger identities. Uploaded counts are not independently verified. Event factors remain assumptions. Upload does not train a model or establish forecast accuracy. Workforce, qualification, and availability assumptions remain synthetic.

## Build phases

1. Support validated uploaded baseline counts throughout forecast, scenarios, staffing comparison, and decision records. Preserve deterministic defaults and existing APIs.
2. Replace frontend with typed components and one visual system. Add source selection, CSV validation/template, daily demand comparison, editable workforce assumptions, legible roster, disruption controls, clear comparisons, approval and exports.
3. Check synthetic and imported paths, invalid inputs, consistent scenarios, stale-result invalidation, keyboard/mobile layout, and approval. Run backend tests and production build. Update README, API/data notes, assumptions, and demo script.

## Guardrails and limits

- Seven-day Super Bowl LXI context; illustrative 8–14 February 2027 window, not organizer-prescribed dates.
- Ordinary and proposed rosters face the same selected event demand and disruption.
- Coverage means required concurrent worker-hours covered; not observed queue delay.
- Show unfilled shifts and remaining gaps without promising full coverage.
- Synthetic forecast holdout score remains available and clearly labeled.
- Manager approval saves a local planning record only.
