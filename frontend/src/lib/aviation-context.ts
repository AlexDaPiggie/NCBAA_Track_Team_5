/** Airport-wide context only. These counts do not drive the FBO staffing model. */
export type HourlyAirportArrivals = {hour:number;arrivals:number};

export const laxSuperBowl2022Context = {
  airport:'LAX',
  periodStart:'2022-02-07',
  periodEnd:'2022-02-13',
  source:'U.S. DOT Bureau of Transportation Statistics (BTS), Airline On-Time Performance',
  sourceUrl:'https://transtats.bts.gov/DL_SelectFields.aspx?QO_fu146_anzr=b0-gvzr&gnoyr_VQ=FGK',
  usage:'reference-only',
  description:'Recorded large-carrier commercial arrivals at LAX, grouped by local arrival hour across the 2022 Super Bowl week.',
  limitations:'Airport-wide airline traffic only. Not general aviation, FBO visits, FBO service requests, worker demand, or a forecast for 2027. Passenger and fuel work are not present in this data.',
  filter:'Destination LAX; flight dates February 7–13, 2022; non-cancelled, non-diverted flights with a valid actual arrival time.',
  arrivals:[
    {hour:0,arrivals:50},{hour:1,arrivals:17},{hour:2,arrivals:2},{hour:3,arrivals:1},
    {hour:4,arrivals:5},{hour:5,arrivals:40},{hour:6,arrivals:82},{hour:7,arrivals:169},
    {hour:8,arrivals:243},{hour:9,arrivals:235},{hour:10,arrivals:139},{hour:11,arrivals:253},
    {hour:12,arrivals:216},{hour:13,arrivals:209},{hour:14,arrivals:169},{hour:15,arrivals:141},
    {hour:16,arrivals:148},{hour:17,arrivals:249},{hour:18,arrivals:194},{hour:19,arrivals:179},
    {hour:20,arrivals:271},{hour:21,arrivals:192},{hour:22,arrivals:169},{hour:23,arrivals:129},
  ] satisfies HourlyAirportArrivals[],
};

export const laxSuperBowl2022TotalArrivals=laxSuperBowl2022Context.arrivals.reduce((total,row)=>total+row.arrivals,0);
