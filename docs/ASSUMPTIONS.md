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

## Dataset created

The reproducible starter CSVs are in `data/processed/`; regenerate them with `python -m demand.build_dataset`. They currently contain synthetic data only. FAA OPSNET and TAF were identified as possible public airport-traffic context sources, but not as FBO workload data. The TAF download connection was refused from this environment, so no FAA numerical values have been copied into the dataset.

## Synthetic MVP assumptions (configurable, not aviation guidance)

- Demand is represented in hourly buckets over seven consecutive days.
- The Stage 2 model response additionally groups each complete 168-hour profile into 42 consecutive four-hour blocks. Aircraft, passenger, and fuel-request counts are summed from the four source hours. Four-hour required staffing is estimated from total block workload divided by 240 minutes times the configured utilization, rounded up and bounded by the existing department minimum. This is an average-capacity estimate and can conceal peaks inside a block; hourly requirements remain the finer-grained view. The block profile inherits its source provenance and remains synthetic or proxy-based as labeled.
- Synthetic arrivals generate service tasks using configurable task-type mix and estimated task duration.
- The website now builds synthetic department rosters with 6-, 8-, or 12-hour shifts, configurable break duration, weekly hour cap, and minimum rest gap. The synthetic pool is capped at 30 workers per department; unmet shift slots are reported. Workers are assumed available and qualified for one department. Real names, employee availability, skill differences, fatigue, labor-law rules, and overtime premiums are not modeled.
- Ordinary demand uses a synthetic 1.00 multiplier. Event demand uses low/medium/high demo multipliers of 1.15, 1.4, and 1.7, plus the user-set demand multiplier; the scenario factors are fixed in the model and are not official forecasts.
- The ordinary/event comparison and staffing peaks are computed from the same synthetic hourly profile and configured service assumptions. They do not represent observed LA traffic.
- The stress test applies a configurable synthetic arrival increase, longer service times, and call-outs during the same selected time window to both baseline and event rosters. This is a capacity estimate, not a queue replay under breaks or a real disruption record.
- Any labor cost is an illustrative configurable rate, not a wage claim.
- Forecast metrics use a held-out synthetic test period; they do not establish real-world predictive accuracy.
- Names and identifiers in fixtures are fictional. No passenger details or actual employee data are collected.

## Unverified with aviation experts

FBO task catalog and task times; role and qualification requirements; local staffing practices; fatigue, break, rest, and overtime rules; event-week traffic magnitude and timing; whether any particular site has relevant historical data. Validate with an FBO manager before operational use. The prototype is not for operational deployment.

## Stage 6 impact metric definitions

- Impact compares the ordinary-demand roster left unchanged (the naive baseline) with the event-demand roster under the same event forecast and configured disruption. Both are synthetic planning estimates.
- A four-hour block counts as understaffed if any of its hourly samples has a positive uncovered position gap. A severe-gap block has a peak hourly gap of at least three positions.
- Modeled labor-cost delta is event-roster estimated labor cost minus ordinary-roster estimated labor cost. It is not actual payroll or the cost of real staffing actions.
- Coverage change is proposed coverage percentage minus baseline coverage percentage. Cost per coverage percentage point is reported only when coverage improves; it is modeled incremental cost divided by the positive coverage change.
- Delay-risk proxy is 10 assumed minutes for each uncovered Ramp Operations seat-hour. The coefficient is illustrative and unvalidated; this is not an aircraft delay forecast.
- Overtime, part-time offers, reserve call-ins, and reserve efficiency are not currently produced by the roster API and remain unavailable rather than inferred.
- No LAX 2022 arrivals file with verifiable source metadata is present in the checkout. Current impact outputs inherit selected synthetic or disclosed JFK-proxy demand provenance.
