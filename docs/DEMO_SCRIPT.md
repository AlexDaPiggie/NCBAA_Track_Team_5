# CrewPilot AI command-center demo

Rehearse about three minutes. Track 1 does not specify a pitch length in the supplied PDF.

## Mission Control — 45 seconds

“An FBO preparing for Super Bowl week needs to connect aircraft demand with qualified staffing. CrewPilot shows that operation in one place: arrivals, work coverage, available crew, and uncovered services.”

Keep Super Bowl week, medium case, Saturday, fixed seed. Show the demand/capacity chart and arrival-service feed. Click a timeline block.

“Every service is tied to a fictional aircraft. Each assignment checks the required qualification, service deadline, shift, break, and worker overlap. This is labeled synthetic data, not live airport traffic.”

## Crisis Mode — 50 seconds

Choose **Stacked disruption** and click **Trigger disruption**.

“Four unexpected aircraft arrive. Two ramp workers call out. The next three expected arrivals shift by 45 minutes. We keep original assignments fixed so you can see the failure points.”

Show the crisis banner, before/after table, changed available crew, delayed arrivals, red timeline conflicts and uncovered-task queue. Read only the values calculated by the current run.

## Recovery — 50 seconds

Click **Calculate recovery candidate**.

“Now a transparent scheduling heuristic reassigns eligible crew and service times. It preserves feasible work already underway. These explanations show what changed and which checks passed.”

Compare covered tasks and remaining gaps under exactly the same affected workload. Point out that allocated labor cost is unchanged because the workforce is unchanged. Do not promise complete coverage or a global optimum.

## Human decision — 25 seconds

“CrewPilot recommends. A manager reviews remaining gaps and approves or rejects. This creates a browser-local planning record and a downloadable snapshot. It never sends assignments to employees or authorizes aircraft movement.”

For test-only demonstration use “Demo manager” and notes “Synthetic replay; not an operational instruction.”

## Impact and close — 10 seconds

Show Impact Report if time permits: ordinary-week and Super Bowl-week selected-day comparisons. State that this daily replay does not implement a full seven-day employee roster or establish real forecast accuracy. The retained FastAPI weekly model is a separate integration step.

“Our goal is to make staffing gaps visible before the event, test the consequences, and give the manager an explainable recovery candidate.”

## Before presenting

- Run `npm.cmd run dev` in `frontend`; the default local task demo needs no API.
- Reset disruption and choose Saturday / event week / medium demand.
- Check data labels, task inspector, crisis changes, candidate constraints, remaining gaps, and manager review.
- Use only computed current-run results. No preset improvement percentages.
- Current visual walkthrough remains unverified because Computer Use was blocked by URL verification.
