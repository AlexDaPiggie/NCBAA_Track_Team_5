# LA aviation data research

Checked 2026-10-23. Primary sources only.

## Verified facts

- Super Bowl LXI is scheduled for **February 14, 2027 at SoFi Stadium in Inglewood, California**. This gives a known game date and venue; the organizer brief still defines the planning horizon as a seven-day window without specifying its start/end dates. Sources: [NFL important dates](https://operations.nfl.com/calendar-events/nfl-important-dates/) and [NFL announcement](https://www.nfl.com/news/los-angeles-to-host-super-bowl-lxi-in-2027).
- FAA OPSNET is the FAA's official source for air traffic operations and delay data. Airport operations count airport arrivals/departures and local operations reported by towers; airport counts do not include overflights. Public, finalized monthly data are available about 20 days after month end. [FAA OPSNET overview](https://aspmhelp.faa.gov/index/Operations_Network_(OPSNET).html)
- OPSNET reports can be selected by airport identifier and date range, grouped by date, local hour, or quarter hour, and downloaded as Excel. Its airport-operations view can show itinerant/local and IFR/VFR categories; its documentation also describes an itinerant breakdown for air carrier, air taxi, general aviation, and military operations. Recent daily data requires a login; the public release is monthly finalized data. [FAA OPSNET manual](https://aspmhelp.faa.gov/index/OPSNET_Manual.html)
- LAWA's [Van Nuys Airport information page](https://www.lawa.org/groups-and-divisions/asset-management/asset-managements/vny-airport-information) links to airport traffic volume, based-aircraft, aircraft-operations history, and fuel-delivery statistics. These are useful local context but are not documented there as FBO labor or service-task records.
- LAWA's [VNY Q2 2025 quarterly report](https://www.lawa.org/sites/lawa/files/2025-09/VNY%202q25_%2020250916_Quarterly%20Report2.pdf) reports 47,501 total aircraft operations, including 39,552 general aviation operations. This historical quarter is included only as a local context anchor in the website; it does not calibrate the February 2027 staffing forecast.
- LAWA's [VNY WebTrak description](https://www.lawa.org/lawa-environment/noise-management/van-nuys/vny-internet-flight-tracking-system) says its FAA National Offload Program radar tracks include aircraft type, altitude, origin/destination, and flight identification. VNY and Burbank flights are identified separately from regional transit. Live data can be delayed up to 60 minutes; historical replay is available up to 90 days. The page does not document a public bulk-download API.

## Data limits for this project

- Airport operations are traffic counts, not FBO arrivals, fuel requests, passenger-service jobs, or worker hours. VNY is a relevant LA general-aviation context source, but its counts include operations that may create no FBO work, such as local pattern activity. This is an inference from what OPSNET counts and what FBO workload measures.
- OPSNET is promising for an airport-specific hourly/quarter-hourly traffic pattern, but the report is an interactive export and finalized monthly data lag. It does not provide Super Bowl LXI forecasts or FBO staffing history.
- VNY WebTrak can help inspect recent local aircraft patterns, but its documented 90-day replay window cannot supply historical patterns for the February 2027 event during this October 2026 research. LAWA does not document an export endpoint on the information page.
- LAX airline passenger/flight statistics should not be used as a stand-in for FBO or private-aviation demand. The current JFK airline-departure proxy is even less local and should stay optional and clearly labeled.
- Public source values, once downloaded, still need a documented airport, time-zone, date range, field definition, coverage gaps, and license/terms check before inclusion in fixtures.

## Recommendation

1. Keep synthetic data as the default for the event-week forecast, service-task mix, and employee roster. The future event has no observed FBO workload record to train on.
2. If adding public context, export OPSNET airport operations for VNY (and optionally BUR or HHR only if their airport identifiers and data availability are confirmed in the FAA interface). Use date plus local hour/quarter hour and the general-aviation itinerant category when available. Label it **airport operations context**, never FBO task demand.
3. Do not use LAWA aggregate fuel-delivery stats in the staffing model; they are not the selected operational focus and do not describe staff workload at hourly resolution.
4. Ask an FBO manager to validate the task mix, task durations, staffing roles, qualification requirements, availability, and shift assumptions. No public source found here validates those values.

## Aviation expert review questions

- Which staff roles and qualifications cover the routine FBO tasks we model?
- What tasks are triggered by an arrival, and what task durations or concurrency assumptions are realistic?
- Which shift lengths, break patterns, minimum rest, and weekly-hour constraints should be configurable for a planning demo? Which are site policy versus applicable rules?
- What is the appropriate relationship between airport operations and FBO service requests at the selected airport, and what should not be inferred?
- Which disruption scenarios matter most to an FBO manager: call-outs, arrival clustering, departure delay, weather, or another factor?
- Which measures are useful to a manager: uncovered task-hours, waiting time, labor hours, staffing cost, or schedule changes?

No aviation expert has reviewed the current assumptions. Do not present them as FBO policy or actual LA operations.
