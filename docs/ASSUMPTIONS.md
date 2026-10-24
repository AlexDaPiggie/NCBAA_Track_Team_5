# Assumptions and evidence ledger

## Organizer-documented facts

- Track 1 is “The Intelligent FBO” for Business / General Aviation.
- Prepare an FBO for the seven-day window around Super Bowl week in Los Angeles.
- Choose one operational pressure point and model it with public or synthetic data; document every assumption.
- Compare ordinary week with Super Bowl week demand; recommend low, medium, and high demand preparation; show forecast accuracy and resource improvements.
- AI is planning support only, has no movement authority, and must explain uncertainty and assumptions. Protect passenger privacy; do not use sensitive passenger data.
- LA 2028 Olympics adaptation is optional stretch scope.

Source: `docs/Aviation Tracks.pdf` (slides 3–6). The slides do not specify exact staffing rules, source data, deadlines, Track 1 pitch duration, or numeric judging weights; these are unknown.

## Product research checked 2026-10-23

- FlightBridge’s FBO operations page says upcoming traffic visibility can support staffing and equipment planning: https://home.flightbridge.com/solutions/fbo-operations
- Aerosimple’s shift management page advertises scheduling/deployment and staffing-gap visibility: https://www.aerosimple.com/solutions/shift-management
- FAA material found in search concerns FAA air traffic operations, not FBO employees. It must not be generalized into FBO staffing policy: https://www.faa.gov/regulations_policies/orders_notices/index.cfm/go/document.information/documentID/1045657

These sources show adjacent existing capabilities, not a comprehensive competitor survey, independent validation, or proof of a gap. Differentiation remains a hypothesis.

## Local aviation context checked 2026-10-23

- LAWA's Van Nuys Airport Q2 2025 quarterly report records 47,501 aircraft operations, including 39,552 general aviation operations. This is airport traffic context only; it is not FBO service demand, staffing data, or a Super Bowl forecast. [LAWA VNY Q2 2025 report](https://www.lawa.org/sites/lawa/files/2025-09/VNY%202q25_%2020250916_Quarterly%20Report2.pdf).
- FAA OPSNET provides airport operations and distinguishes general aviation categories. It does not identify FBO service jobs or employee hours. [OPSNET overview](https://aspmhelp.faa.gov/index/Operations_Network_(OPSNET).html), [airport operations data dictionary](https://aspmhelp.faa.gov/index/Airport_Operations__Data_Download_Dictionary.html).
- Super Bowl LXI is scheduled for February 14, 2027 at SoFi Stadium in Inglewood. The organizer brief does not define the seven-day window dates. [NFL important dates](https://operations.nfl.com/calendar-events/nfl-important-dates/).

## Dataset created

The synthetic fixtures and model artifact are in `backend/data/`. Regenerate fixtures with `python -m backend.model` and generated training history/model with `python -m backend.training`. The guided site defaults to synthetic data. Optional uploaded ordinary-week counts replace the ordinary demand profile and are not independently verified. Event factors and workforce rules remain assumptions. FAA sources provide airport traffic context, not FBO workload labels; no FAA counts train the default model.

## Historical LAX reference added

- The Impact Report includes an hourly distribution of 3,502 valid large-carrier LAX arrivals recorded February 7–13, 2022, during Super Bowl LVI week. The source and filter are documented in `docs/DATA_SOURCES.md` and the fixture is in `frontend/src/lib/aviation-context.ts`.
- This is commercial-airline airport traffic. It is displayed as historical timing context only. It does not feed forecast, aircraft, FBO service-task, or staffing calculations. It is not an estimate of business aviation or FBO activity and does not forecast Super Bowl LXI in 2027.
- BTS provides local actual arrival times. The fixture filters non-cancelled, non-diverted flights to LAX with valid actual arrival times, then groups arrivals by hour. Daily flight-date totals are not shown as arrival-date truth.

## Current task-replay command center

- The dark Next.js website uses a deterministic synthetic TypeScript provider. It is not live airport telemetry or a connected task-level FastAPI service.
- The chosen day is replayed within a seven-day event context. Full-week hour/rest rules are not evaluated by this daily replay. The browser's new seven-day staffing plan is a separate calculation.
- Twelve fictional workers have one qualification each and cover three fixed eight-hour shifts: 00:00–08:00, 08:00–16:00, and 16:00–24:00. Each shift has two ramp workers, one fuel worker, and one customer-service worker, with staggered paid 30-minute breaks. Fixed shifts repeat daily, leaving 16 hours off between shifts. No real employee availability or identity data are used.
- Ramp assistance defaults to 35 minutes with two qualified workers; customer service 15 minutes with one; fuel service 40 minutes with one. These are configurable fixture rules, not verified FBO task standards.
- The selected-day replay covers arrivals and staffing from 00:00 to 24:00. The synthetic arrival curve has an assumed overnight low and afternoon peak; it is not fitted to VNY traffic. Simulator time defaults to 14:00 PST and can be changed in 15-minute steps. The selected time applies when the manager runs the simulation; it sets when call-outs begin and unexpected arrivals start, and which expected arrivals may be delayed. Arrival delays move the next three expected flights and their service windows. Extra aircraft create additional tasks. Late arrivals may have service tasks finish through 02:00 the next day; the repeating 00:00–08:00 crew provides that boundary coverage. A safety check caps delays and blocks affected work past 02:00. The original plan remains fixed until a separate recovery is requested.
- Recovery is an earliest-deadline greedy heuristic with five-minute start increments. Qualified crew, shifts, breaks, service windows, and non-overlap are checked; feasible work already underway is retained. No global optimum is claimed.
- Work coverage weights task duration by simultaneous crew required. Risk thresholds are assumed: no uncovered tasks = low, up to 15% uncovered = watch, greater than 15% = high.
- Recovery Planner adds hypothetical role-qualified workers to the candidate only. The disrupted original keeps its roster and cost. Incremental cost and all remaining gaps stay visible.
- Recovery recommendations exclude gaps whose service window has already expired at the selected simulation time. Those gaps remain visible in Mission Control; they are not presented as recoverable by adding staff after their deadline or the 02:00 service cutoff.
- Proposed workers use the selected role qualification, one of the three fixed eight-hour shifts, and a staggered 30-minute paid break. Cost uses the assumed hourly rate. The weekly estimate repeats the same shift and headcount seven times; taxes, overtime, benefits, and hiring costs are excluded.
- Proposed hires are not verified as available for an active incident. A manager must validate qualifications, availability, cost, and the candidate before operational use.
- The starting recommendation searches 0–20 added workers per role with the same scheduler and disruption. It chooses the smallest count with full role task coverage, or the count covering the most tasks within that limit. This bounded heuristic is not a global cost optimum.
- Review records are saved locally in the browser, include the generated mission snapshot, and can be downloaded. They do not dispatch workers.

## Current browser seven-day staffing plan

- Uses fixed-seed synthetic ordinary and event demand across February 8–14, 2027. Low, medium, and high event multipliers are 1.15, 1.4, and 1.7. These are assumptions, not forecasts.
- Synthetic aircraft and service tasks are generated by the same task-replay fixture. Full task workload is assigned to the hour its service window opens. Required seats use an 80% utilization target and assumed minimums of two ramp, one fuel, and one customer-service seat when that team has work.
- For each date and 8-hour shift, the roster is planned to the peak hourly seat requirement. Shifts are 00–08, 08–16, and 16–24; shifts with no modeled demand are not staffed.
- Fictional workers have one team qualification, a maximum 40 paid hours per week, at least 8 hours between shifts, one shift per day, and staggered 30-minute breaks. The pool limit is 50 workers per team. Week-boundary rest and all real labor rules are not modeled.
- Coverage is covered seat-hours divided by required seat-hours. The ordinary roster and each event roster are both evaluated against that event case's same demand. The proposed event roster may cost more; no savings or guaranteed improvement is asserted.
- Labor cost is paid shift hours times assumed hourly wage ($32 ramp, $35 fuel, $26 customer service). Breaks count as paid hours. Benefits, premiums, and actual payroll rules are excluded.
- Manager approve/reject records are stored locally in browser storage and can be downloaded. They do not contact employees.
- Algorithm audit: the browser weekly planner uses fixed peak-demand staffing rules followed by greedy assignment (eligible workers sorted by hours worked, then ID). It has no objective function, solver, or guarantee of a globally optimal or lowest-cost roster. Current and proposed worker IDs are independently generated; the comparison describes staffing positions, not employee transfers.
- The shortage chart and expanded change rows use the same hourly evaluator as weekly coverage, including break losses. Day/shift/role totals reconcile to weekly staffing hours, shift counts, and labor cost. All additions and reductions are included in the net change.
- Approval follows proposal review. The manager must open the full proposed schedule and confirm review for the selected scenario before approval is enabled. The saved record includes the proposed roster and review confirmation.

## Retained weekly model assumptions (configurable, not aviation guidance)

- Demand is represented in hourly buckets over seven consecutive days.
- The website uses an illustrative Monday–Sunday window, 8–14 February 2027. These exact window dates are a product choice, not an organizer requirement.
- Generated demand includes passenger-count and fuel-request assumptions; uploaded files can supply their own aggregate counts. Configurable task durations translate each service type into staff workload.
- The optional FastAPI weekly planner builds synthetic department rosters with 6-, 8-, or 12-hour shifts, configurable break duration, weekly hour cap, minimum rest gap, and worker pool size. Unfilled slots are reported. Workers are assumed available and qualified for one department. Real names, employee availability, skill differences, fatigue, labor-law rules, and overtime premiums are not modeled.
- For each date and shift, the weekly planner uses the peak hourly seat requirement in that shift. Estimated labor cost is calculated from scheduled worker hours multiplied by the configured hourly rate. Breaks count as paid hours by assumption; benefits, premiums, and actual payroll rules are not included.
- Ordinary demand uses a synthetic 1.00 multiplier. Event demand uses editable low/medium/high factors (defaults 1.15, 1.4, and 1.7), plus the user-set demand multiplier. These are demo assumptions, not official forecasts.
- Illustrative hourly wage rates are editable by department. They are not wage estimates or claims about a particular FBO.
- Per-department minimum on-duty staff and utilization target are editable. Defaults (one customer-service seat, two ramp seats, one fuel-service seat; 80% utilization) are demo settings, not verified requirements. The legacy queue API still accepts wait targets, but the new guided site compares roster capacity rather than queue waiting time.
- The ordinary/event comparison and staffing peaks are computed from the same synthetic hourly profile and configured service assumptions. They do not represent observed LA traffic.
- The stress test applies a configurable synthetic arrival increase, longer service times, and call-outs during the same selected time window to both baseline and event rosters. This is a capacity estimate, not a queue replay under breaks or a real disruption record.
- Any labor cost is an illustrative configurable rate, not a wage claim.
- Forecast metrics use a held-out synthetic test period; they do not establish real-world predictive accuracy.
- A single uploaded ordinary week is not a trained forecast or holdout evaluation. The site reports no accuracy score for uploads. Original CSV files are not saved; decision records include supplied counts and source filename.
- Names and identifiers in fixtures are fictional. No passenger details or actual employee data are collected.

## Unverified with aviation experts

FBO task catalog and task times; role and qualification requirements; local staffing practices; fatigue, break, rest, and overtime rules; event-week traffic magnitude and timing; whether any particular site has relevant historical data. Validate with an FBO manager before operational use. The prototype is not for operational deployment.
