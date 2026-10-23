# Local UI integration of main b2f5b8e

## Scope and decision

Preserve the compact local UI and integrate the incoming ordinary/event demand comparison, synthetic shift planner, disruption test and roster approval APIs. No commits, pushes or operational staffing actions are authorized by this work.

Reviewed `AGENTS.md`, all 12 pages of `docs/Aviation Tracks.pdf`, the existing brainstorm (three product alternatives), MVP plan, assumptions ledger, demo script and redesign plan. `PROJECT_SPEC.md` is not present in this checkout. The existing recommended staffing stress tester remains the focus. This is integration of an established plan, not a new product or framework migration.

Retain the existing compact command-center approach: five core screens plus one combined **Shifts & Stress** screen. Keep the forecast-first and roster-only alternatives documented in BRAINSTORM.md; neither replaces the manager-led end-to-end workflow. Do not add a large introductory panel or default-open technical tables. The optional workflow explanation can remain expandable.

## Implementation phases

1. Back up and verify the four local UI files; fast-forward to incoming main without creating a commit. Preserve the friend's backend, documents and API contracts.
2. Restore the compact UI. Show ordinary/event demand together and make all three event scenarios available in an expandable comparison.
3. Connect one compact shift/stress screen to `/api/staffing-plan`, with settings, two coverage/cost cards and filtered roster details. Explain missing staff-hours in plain English. Keep these capacity estimates separate from queue simulation waits.
4. Extend the existing single review screen to approve/reject either a coverage option or the generated event roster, using the correct endpoint and exact input snapshot. Invalidate roster review after settings change.
5. Build, run existing tests plus focused new API checks, and verify both UI workflows in a native preview using isolated decision records. Leave the combined preview open for review.

## Limits to preserve

Worker availability and qualifications are synthetic assumptions. The roster evaluation estimates coverage; it is not a shift-aware queue replay. Do not display it as measured wait improvement. Scenario factors are demo assumptions, not confidence intervals. Forecast modes remain separately labeled. No passenger identities, dispatch, movement authority or automatic decisions.

The separate unfinished shift-engine upgrade in the parent workspace is not copied over the friend's `backend/scheduling.py`.
