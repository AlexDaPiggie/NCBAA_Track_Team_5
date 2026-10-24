# CrewPilot AI command-center demo

Rehearse about three minutes. Track 1 does not specify a pitch length in the supplied PDF.

## Mission Control — 45 seconds

“An FBO preparing for Super Bowl week needs to connect aircraft demand with qualified staffing. CrewPilot shows that operation in one place: arrivals, work coverage, available crew, and uncovered services.”

Keep Super Bowl week, medium case, Saturday, fixed seed. Show the full-day demand/capacity chart from 00:00 to 24:00, including the default 14:00 mission marker and three shift groups. In Mission Control, open **Service Timeline** details and click a task block.

“Every service is tied to a fictional aircraft. Each assignment checks the required qualification, service deadline, shift, break, and worker overlap. This is labeled synthetic data, not live airport traffic.”

## Simulator — 50 seconds

Choose **Stacked disruption**, adjust simulation time if useful, and click **Run Simulator**.

“Four unexpected aircraft arrive. Two ramp workers call out. The next three expected arrivals shift by 45 minutes. We keep original assignments fixed so you can see the failure points.”

Show the crisis banner, before/after table, changed available crew, delayed arrivals, and red timeline conflicts. Select **Show details** on the crisis timeline to open Mission Control's Service Timeline and its uncovered-task queue. Read only the values calculated by the current run.

## Recovery — 50 seconds

Open **Recovery Planner**. Show current coverage, uncovered services, crew, cost, and task timeline. Click **Plan recovery**, then **View proposed plan**.

“Now a transparent scheduling heuristic reassigns eligible crew and service times. It preserves feasible work already underway. These explanations show what changed and which checks passed.”

Compare covered tasks and remaining gaps under the same affected workload. Show the added staff cost. Do not promise complete coverage or a global optimum.

## Human decision — 25 seconds

“CrewPilot recommends. A manager reviews remaining gaps and approves or rejects. This creates a browser-local planning record and a downloadable snapshot. It never sends assignments to employees or authorizes aircraft movement.”

For test-only demonstration use “Demo manager” and notes “Synthetic replay; not an operational instruction.”

In Recovery Planner, show the recommended additional Ramp, Fuel, and Customer Service counts. Change one count to show the candidate coverage, remaining tasks, assignments, and full-shift cost recalculate. Point out any role still short after the 20-worker search limit. Switch demand cases and return to show that this page session remembers each scenario. The proposed workers are hypothetical; approval does not hire or notify anyone.

## Seven-day staffing plan — 45 seconds

Open **7-Day Staffing Plan** at Medium demand. Show the current/proposed summary and the visible seven-day shortage chart. Point to the largest gap day, then expand one recommended day/shift/role change to show its required coverage, current/proposed coverage, remaining shortage, and cost. Note any removed shifts as well as additions. Use the metric help icons for definitions; detailed rules are under **Methodology & assumptions**. Open **Proposed schedule** to inspect fictional worker IDs and break times before confirming review and recording a manager decision.

“These are calculated from the same fixed-seed synthetic aircraft and task assumptions. Fixed rules staff each shift to peak hourly need; a greedy assignment rule fills positions within hours and rest limits. This is not a global optimization or a claim of minimum cost. Both plans face the same event demand. Shift changes and costs reconcile with the summary. A manager reviews the actual proposed shifts before approving; the decision records locally and nothing is dispatched.”

## Impact and close — 10 seconds

Then open Impact Report if time allows. Its ordinary/event comparison is still a selected-day task replay. The LAX airline arrivals chart is historical context only, not FBO demand or a forecast. No real forecast accuracy is claimed.

“Our goal is to make staffing gaps visible before the event, test the consequences, and give the manager an explainable recovery candidate.”

## Before presenting

- Run `npm.cmd run dev` in `frontend`; the default local task demo needs no API.
- Reset disruption and choose Saturday / event week / medium demand.
- Check data labels, task inspector, crisis changes, candidate constraints, remaining gaps, and manager review.
- Use only computed current-run results. No preset improvement percentages.
- Current visual walkthrough remains unverified because Computer Use was blocked by URL verification.

## Task-first view

Start the timeline in Tasks mode. Point to one aircraft service and open its inspector to show the qualified crew. A two-person job appears once. Use Show uncovered only after triggering a crisis; switch to Crew only when explaining breaks, absences, or worker overlap.
