# Website redesign plan

## Goal

Make CrewPilot easier to understand and demo. Keep the focus on FBO staffing for the seven-day Super Bowl week window.

## Product options considered

1. **Staffing command center:** show the seven-day workflow, ordinary and event demand, shift coverage, disruptions, comparison, and manager review. Best match for the track. Feasible with the current app.
2. **Forecast-first dashboard:** focus on demand charts and forecast scores. Easy to scan, but does not explain how a manager turns demand into a staffing plan.
3. **Roster editor:** focus on shifts and worker constraints. Useful, but assumptions and synthetic data can look like real labor policy without strong explanation.

## Decision

Use option 1. It maps to the organizer's workflow and uses the existing simulation, roster, disruption, and approval features. Keep all results labeled as demo estimates. The app has no verified Los Angeles FBO demand or expert-checked staffing rules. No performance claim until confirmed by same-scenario results.

## Design and build tasks

1. Reorganize the page around clear steps: set demand, build and stress-test rosters, compare, review.
2. Add a short project explanation and visible limits near the top.
3. Apply the De Anza Chatbot visual reference: soft pink gradients, translucent surfaces, serif display headings, rounded cards, and subtle motion.
4. Keep mobile layout, keyboard focus, and reduced-motion support.
5. Build the frontend and run existing backend tests. Do not change the API or scheduling model in this redesign.
