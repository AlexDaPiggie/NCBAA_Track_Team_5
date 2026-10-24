'use client';

import {useMemo,useState} from 'react';
import {Bar,BarChart,CartesianGrid,ResponsiveContainer,Tooltip as ChartTooltip,XAxis,YAxis} from 'recharts';
import {CheckCheck,ChevronDown,Download,Info,TriangleAlert} from 'lucide-react';
import {Badge} from '@/components/ui/badge';
import {Button} from '@/components/ui/button';
import {Card,CardContent} from '@/components/ui/card';
import {Tabs,TabsList,TabsTrigger} from '@/components/ui/tabs';
import {buildWeeklyStaffingPlan,SHIFT_BLOCKS,TEAM_NAMES,type WeeklyCase,type WeeklyMetrics,type WeeklyRoster} from '@/lib/weekly-planner';
import {buildWeeklyReview,type WeeklyReview} from '@/lib/weekly-review';
import {WeeklyProposedSchedule,WeeklyShortageChart,WeeklyStaffingChanges} from './weekly-proposal-review';
import {WeeklyMetricHelp} from './weekly-metric-help';
import type {DemandLevel,Team} from '@/lib/operations';

const money=(value:number)=>new Intl.NumberFormat('en-US',{style:'currency',currency:'USD',maximumFractionDigits:0}).format(value);
const number=(value:number)=>new Intl.NumberFormat('en-US',{maximumFractionDigits:1}).format(value);
const signedNumber=(value:number)=>`${value>0?'+':''}${number(value)}`;
const signedMoney=(value:number)=>`${value>0?'+':value<0?'−':''}${money(Math.abs(value))}`;
const LEVELS:DemandLevel[]=['Low','Medium','High'];
const TEAMS:Team[]=['ramp','fuel','service'];
type Decision={status:'approved'|'rejected';manager:string;notes:string;timestamp:string;selectedLevel:DemandLevel;scheduleReviewed:boolean;metrics:WeeklyMetrics;roster:WeeklyRoster;assumptions:unknown};

function ScenarioSelector({level,onSelect,plan}:{level:DemandLevel;onSelect:(value:DemandLevel)=>void;plan:ReturnType<typeof buildWeeklyStaffingPlan>}){
  return <section className="ops-week-step ops-week-scenario-step" aria-labelledby="weekly-step-scenario">
    <h2 id="weekly-step-scenario">Event demand</h2>
    <div className="ops-week-scenario-options">{LEVELS.map(item=><button key={item} type="button" className={`ops-week-scenario ${item===level?'selected':''}`} aria-pressed={item===level} aria-label={`${item} demand: ${plan.cases[item].demand.aircraft} aircraft`} onClick={()=>onSelect(item)}><b>{item}</b><small>{number(plan.cases[item].demand.aircraft)} aircraft</small></button>)}</div>
    <span className="ops-week-period">8–14 Feb 2027</span><Badge className="ops-status ops-status-amber" variant="outline"><span/>SYNTHETIC DATA</Badge>
  </section>;
}

function RosterComparison({scenario,review}:{scenario:WeeklyCase;review:WeeklyReview}){
  const current=scenario.baseline,proposed=scenario.recommended;
  const rows=[
    {key:'coverage',label:'Work coverage',current:`${number(current.coveragePercent)}%`,proposed:`${number(proposed.coveragePercent)}%`,change:`${signedNumber(proposed.coveragePercent-current.coveragePercent)} pp`,help:'Covered staffing hours ÷ required staffing hours. Both rosters face the same selected event demand. This does not predict service delays.'},
    {key:'workers',label:'Workers',current:number(current.workers),proposed:number(proposed.workers),change:signedNumber(proposed.workers-current.workers),help:'Distinct fictional workers across the week. Rosters are generated independently; the difference is a staffing requirement, not a named employee transfer.'},
    {key:'shifts',label:'8-hour shifts',current:number(current.shifts),proposed:number(proposed.shifts),change:signedNumber(proposed.shifts-current.shifts),help:`${review.addedShifts} added shifts minus ${review.removedShifts} removed shifts. Each shift position is one worker for eight paid hours.`},
    {key:'shortage',label:'Staff-hours short',current:number(current.uncoveredSeatHours),proposed:number(proposed.uncoveredSeatHours),change:signedNumber(proposed.uncoveredSeatHours-current.uncoveredSeatHours),help:'Hourly staffing need minus available staff after breaks, summed across all roles and seven days. One missing worker for one hour equals one staff-hour short.'},
    {key:'cost',label:'Labor cost',current:money(current.laborCost),proposed:money(proposed.laborCost),change:signedMoney(proposed.laborCost-current.laborCost),help:'Scheduled paid hours × assumed role wage. Change is the incremental weekly labor cost. Paid breaks included; benefits and premiums excluded.'},
  ];
  return <Card className="ops-week-recommendation ops-week-summary"><CardContent><div className="ops-week-table-scroll"><table className="ops-week-summary-table"><caption className="sr-only">Current and recommended rosters under {scenario.level.toLowerCase()} event demand</caption><thead><tr><th scope="col"><span className={`ops-week-gap-status ${current.uncoveredSeatHours>0?'risk':'good'}`}>{current.uncoveredSeatHours>0?'Coverage gap':'Covered'}</span></th><th scope="col">Current roster</th><th scope="col">Recommended</th><th scope="col">Change</th></tr></thead><tbody>{rows.map(row=><tr key={row.key} className={`ops-week-summary-${row.key}`}><th scope="row"><span>{row.label}<WeeklyMetricHelp label={row.label}>{row.help}</WeeklyMetricHelp></span></th><td>{row.current}</td><td className={row.key==='shortage'&&proposed.uncoveredSeatHours>0?'risk':''}>{row.proposed}</td><td>{row.change}</td></tr>)}</tbody></table></div><div className="ops-week-model-status"><span>Heuristic · no optimality guarantee</span><WeeklyMetricHelp label="Planning method">Fixed staffing rules and greedy worker assignment. Full method and constraints are in Methodology &amp; assumptions.</WeeklyMetricHelp></div></CardContent></Card>;
}

function RosterTable({roster,requiredRoster,aircraftByDay}:{roster:WeeklyRoster;requiredRoster:WeeklyRoster;aircraftByDay:number[]}){
  return <div className="ops-week-table-scroll" tabIndex={0} aria-label="Scrollable daily staffing roster">
    <table className="ops-week-table"><thead><tr><th rowSpan={2}>Day</th><th rowSpan={2}>Aircraft</th>{TEAMS.map(team=><th key={team} colSpan={3}>{TEAM_NAMES[team]}</th>)}</tr><tr>{TEAMS.flatMap(team=>SHIFT_BLOCKS.map(shift=><th key={`${team}-${shift.key}`}>{shift.label}</th>))}</tr></thead>
      <tbody>{roster.days.map(day=><tr key={day.day}><th>{day.label}</th><td>{aircraftByDay[day.day]}</td>{TEAMS.flatMap(team=>SHIFT_BLOCKS.map(shift=>{const scheduled=day.seats[team][shift.key].scheduled,required=requiredRoster.days[day.day].seats[team][shift.key].required,short=Math.max(0,required-scheduled);return <td key={`${team}-${shift.key}`} className={short?'ops-week-shortfall':''}>{scheduled}<small> / {required}</small>{short>0&&<em>Short {short}</em>}</td>;}))}</tr>)}</tbody>
    </table>
  </div>;
}

export function WeeklyStaffingPlan(){
  const plan=useMemo(()=>buildWeeklyStaffingPlan(42),[]);
  const [selected,setSelected]=useState<DemandLevel>('Medium');
  const [rosterKind,setRosterKind]=useState<'baseline'|'recommended'>('recommended');
  const [scheduleOpened,setScheduleOpened]=useState(false),[scheduleReviewed,setScheduleReviewed]=useState(false);
  const [manager,setManager]=useState(''),[notes,setNotes]=useState(''),[decision,setDecision]=useState<Decision|null>(null),[message,setMessage]=useState('');
  const activeCase=plan.cases[selected];
  const review=useMemo(()=>buildWeeklyReview(activeCase),[activeCase]);
  const shownRoster=rosterKind==='baseline'?activeCase.baselineRoster:activeCase.recommendedRoster;
  const arrivals=plan.ordinaryRoster.days.map((day,index)=>({day:day.label,ordinary:day.aircraft,event:activeCase.recommendedRoster.days[index].aircraft}));
  const recommended=activeCase.recommended;
  function selectCase(level:DemandLevel){if(level===selected)return;setSelected(level);setDecision(null);setMessage('');setScheduleOpened(false);setScheduleReviewed(false);}
  function saveDecision(status:'approved'|'rejected'){
    if(!manager.trim()||(status==='approved'&&!scheduleReviewed))return;
    const record:Decision={status,manager:manager.trim(),notes,timestamp:new Date().toISOString(),selectedLevel:selected,scheduleReviewed,metrics:recommended,roster:activeCase.recommendedRoster,assumptions:plan.assumptions};
    try{localStorage.setItem('crewpilot-weekly-staffing-review',JSON.stringify(record));setDecision(record);setMessage(`${selected} demand plan ${status}. Decision saved in this browser only.`);}
    catch{setDecision(record);setMessage('Browser storage unavailable. Decision is visible until you leave this page.');}
  }
  function downloadDecision(){if(!decision)return;const blob=new Blob([JSON.stringify(decision,null,2)],{type:'application/json'}),url=URL.createObjectURL(blob),anchor=document.createElement('a');anchor.href=url;anchor.download='crewpilot-weekly-staffing-review.json';anchor.click();URL.revokeObjectURL(url);}

  return <div className="ops-weekly-plan ops-week-decision-page">
    <ScenarioSelector level={selected} onSelect={selectCase} plan={plan}/>

    <div className="ops-week-decision-grid">
      <RosterComparison scenario={activeCase} review={review}/>
      <WeeklyShortageChart review={review}/>
    </div>

    <WeeklyStaffingChanges key={selected} review={review}/>

    <details className="ops-week-disclosure ops-week-daily"><summary><span><b>Daily breakdown</b></span><ChevronDown size={17}/></summary><div className="ops-week-breakdown-grid">
      <Card><CardContent><div className="ops-week-subheading"><h3>Aircraft by day</h3></div><div className="ops-week-chart-key"><span>Ordinary week</span><span>{selected} event week</span></div><div className="ops-week-chart" role="img" aria-label={`${selected} case synthetic aircraft counts by day compared with ordinary-week baseline`}><ResponsiveContainer width="100%" height="100%"><BarChart data={arrivals} margin={{top:10,right:10,left:-25,bottom:0}}><CartesianGrid vertical={false} stroke="var(--chart-grid)" strokeDasharray="3 4"/><XAxis dataKey="day" axisLine={false} tickLine={false} tick={{fill:'var(--chart-axis)',fontSize:10}}/><YAxis axisLine={false} tickLine={false} tick={{fill:'var(--chart-axis)',fontSize:10}}/><ChartTooltip contentStyle={{background:'var(--chart-tooltip)',border:'1px solid var(--chart-tooltip-border)',borderRadius:8,fontSize:11,color:'var(--foreground)'}}/><Bar dataKey="ordinary" name="Ordinary week" fill="var(--chart-capacity)" radius={[3,3,0,0]}/><Bar dataKey="event" name={`${selected} event week`} fill="var(--chart-demand)" radius={[3,3,0,0]}/></BarChart></ResponsiveContainer></div></CardContent></Card>
      <Card><CardContent><div className="ops-week-subheading"><h3>Shift matrix<WeeklyMetricHelp label="Shift matrix">Scheduled staff / peak staff needed for the selected event case. Short marks an uncovered position.</WeeklyMetricHelp></h3></div><div className="ops-week-roster-toggle"><Tabs value={rosterKind} onValueChange={value=>setRosterKind(value as 'baseline'|'recommended')}><TabsList aria-label="Choose roster for daily matrix"><TabsTrigger value="baseline">Current roster</TabsTrigger><TabsTrigger value="recommended">Event-ready roster</TabsTrigger></TabsList></Tabs></div><RosterTable roster={shownRoster} requiredRoster={activeCase.recommendedRoster} aircraftByDay={activeCase.demandAircraftByDay}/></CardContent></Card>
    </div></details>

    <details className="ops-week-disclosure ops-week-assumptions"><summary><span><b>Methodology &amp; assumptions</b></span><ChevronDown size={17}/></summary><div className="ops-assumption-grid"><div><b>Scheduling method</b><p>Fixed staffing rules followed by greedy assignment. Task crew-hours are grouped into their service-window opening hour; each 8-hour shift is staffed to its busiest hour, using 80% target utilization. Eligible workers are assigned by hours worked, then ID. No global optimality or minimum-cost guarantee.</p></div><div><b>Demand and workload</b><p>Fixed seed 42. Event multipliers: Low 1.15×, Medium 1.4×, High 1.7×. Event attendance is not an aircraft-demand input. Ramp: 35 minutes × 2 crew. Guest assistance: 15 minutes × 1. Fuel: 40 minutes × 1 on 70% of aircraft.</p></div><div><b>Roster and cost rules</b><p>One team per worker; one shift per day; 40 paid hours per week; 8 hours between shifts; staggered paid 30-minute breaks. Cost = paid hours × assumed wage: ramp $32, fuel $35, customer service $26. Benefits and premiums excluded.</p></div><div><b>Comparison limits</b><p>Both rosters face the same selected event demand. Coverage includes break losses. Worker IDs are independently generated; changes describe positions, not employee transfers. Results are modeled estimates, not measured FBO performance or service-delay forecasts.</p></div></div></details>
    <WeeklyProposedSchedule key={`schedule-${selected}`} review={review} onOpened={()=>setScheduleOpened(true)}/>
    <Card className="ops-week-approval-card ops-week-final-approval"><CardContent>
      <div className="ops-week-decision-heading"><h2>Manager decision</h2><span>{selected} proposal · {recommended.shifts} shifts · {money(recommended.laborCost)}</span></div>
      <label className="ops-week-review-confirm"><input type="checkbox" checked={scheduleReviewed} disabled={!scheduleOpened||!!decision} onChange={event=>setScheduleReviewed(event.target.checked)}/><span>I reviewed this proposed schedule.{!scheduleOpened&&<small>Open Proposed schedule above to enable review.</small>}</span></label>
      <div className="ops-week-final-fields"><label className="ops-week-input">Manager name<input value={manager} maxLength={100} onChange={event=>{setManager(event.target.value);setDecision(null);setMessage('');}} placeholder="Enter your name"/></label><label className="ops-week-input">Notes <span>Optional</span><textarea value={notes} maxLength={2000} onChange={event=>{setNotes(event.target.value);setDecision(null);setMessage('');}} placeholder="Add a note about this decision"/></label></div>
      <div className="ops-week-decision-actions"><Button onClick={()=>saveDecision('approved')} disabled={!manager.trim()||!scheduleReviewed||!!decision}><CheckCheck size={15}/>{decision?.status==='approved'?'Approved':`Approve ${selected.toLowerCase()}-demand plan`}</Button><Button variant="outline" onClick={()=>saveDecision('rejected')} disabled={!manager.trim()||!!decision}><TriangleAlert size={15}/>{decision?.status==='rejected'?'Rejected':'Reject plan'}</Button>{decision&&<Button variant="ghost" onClick={downloadDecision}><Download size={14}/>Download record</Button>}</div>
      {message&&<p className="ops-week-decision-message" role="status"><Info size={14}/>{message}</p>}
    </CardContent></Card>
  </div>;
}
