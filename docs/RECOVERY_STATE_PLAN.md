# Recovery scenario retention

Keep the established staffing demo and scheduling algorithm. The defect is that changing the event case deletes the only recovery state, preventing comparison when returning to a previously calculated case.

1. Keep independent in-memory sessions keyed by all mission inputs (day, week, event level, seed, uploaded counts, optional service rules and workforce).
2. Restore disruption controls, applied conditions, recovery status, manager notes and review together. A new scenario starts without a calculated candidate. Reapplying unchanged disruption inputs retains the candidate; changed applied conditions invalidate its candidate and review.
3. Verify round trips, changed inputs, isolation of approvals, unchanged disruption reapplication and the rendered Recovery Planner. Run frontend tests and TypeScript checks.

No new workforce, scheduling algorithm, backend integration or browser persistence is added. Refreshing clears the session history. Candidate schedules remain deterministic recalculations of exactly the restored inputs; no performance or operational validity claim is added.
