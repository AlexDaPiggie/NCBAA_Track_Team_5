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

## Current task-replay command center

- The dark Next.js website uses a deterministic synthetic TypeScript provider. It is not live airport telemetry or a connected task-level FastAPI service.
- The chosen day is replayed within a seven-day event context. Full-week hour/rest rules are not evaluated by this daily replay. The retained weekly Python model is separate.
- Nine fictional workers have one qualification each, 11:30–20:30 shifts, and staggered paid 30-minute breaks. No real employee availability or identity data are used.
- Ramp assistance defaults to 35 minutes with two qualified workers; customer service 15 minutes with one; fuel service 40 minutes with one. These are configurable fixture rules, not verified FBO task standards.
- Calls-outs begin at 14:00. Arrival delays move the next three expected flights and their service windows. Extra aircraft create additional tasks. The original plan remains fixed until a separate recovery is requested.
- Recovery is an earliest-deadline greedy heuristic with five-minute start increments. Qualified crew, shifts, breaks, service windows, and non-overlap are checked; feasible work already underway is retained. No global optimum is claimed.
- Work coverage weights task duration by simultaneous crew required. Risk thresholds are assumed: no uncovered tasks = low, up to 15% uncovered = watch, greater than 15% = high.
- Allocated labor cost is fixed by the roster and paid hours, so no savings are invented when tasks move. All calculated remaining gaps remain visible.
- Review records are saved locally in the browser, include the generated mission snapshot, and can be downloaded. They do not dispatch workers.

## Retained weekly model assumptions (configurable, not aviation guidance)

- Demand is represented in hourly buckets over seven consecutive days.
- The website uses an illustrative Monday–Sunday window, 8–14 February 2027. These exact window dates are a product choice, not an organizer requirement.
- Generated demand includes passenger-count and fuel-request assumptions; uploaded files can supply their own aggregate counts. Configurable task durations translate each service type into staff workload.
- The website builds synthetic department rosters with 6-, 8-, or 12-hour shifts, configurable break duration, weekly hour cap, minimum rest gap, and worker pool size. Unfilled slots are reported. Workers are assumed available and qualified for one department. Real names, employee availability, skill differences, fatigue, labor-law rules, and overtime premiums are not modeled.
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
