'use client';

import {Fragment,useState} from 'react';
import {Bar,BarChart,CartesianGrid,ResponsiveContainer,Tooltip,XAxis,YAxis} from 'recharts';
import {ChevronDown,TriangleAlert} from 'lucide-react';
import {Card,CardContent} from '@/components/ui/card';
import {TEAM_NAMES,TEAM_WAGES,WEEK_DAYS,type WeeklyShiftAssignment} from '@/lib/weekly-planner';
import type {WeeklyReview,WeeklySlotReview} from '@/lib/weekly-review';
import {WeeklyMetricHelp} from './weekly-metric-help';

const number=(value:number)=>new Intl.NumberFormat('en-US',{maximumFractionDigits:1}).format(value);
const money=(value:number)=>new Intl.NumberFormat('en-US',{style:'currency',currency:'USD',maximumFractionDigits:0}).format(value);
const signedMoney=(value:number)=>`${value>0?'+':value<0?'−':''}${money(Math.abs(value))}`;
const signed=(value:number)=>`${value>0?'+':''}${number(value)}`;
const clock=(hour:number)=>`${String(Math.floor(hour%24)).padStart(2,'0')}:${String(Math.round((hour%1)*60)).padStart(2,'0')}`;

function AssignmentList({assignments}:{assignments:WeeklyShiftAssignment[]}){
  if(!assignments.length)return <p>No staff scheduled.</p>;
  return <ul className="ops-week-assignment-list">{assignments.map(item=><li key={item.workerId}><b>{item.workerId}</b><span>{clock(item.start)}–{item.end%24===0?'24:00':clock(item.end)} · break {clock(item.breakStart)}–{clock(item.breakEnd)}</span></li>)}</ul>;
}

export function WeeklyShortageChart({review}:{review:WeeklyReview}){
  const worst=[...review.days].sort((a,b)=>b.current-a.current)[0];
  return <Card className="ops-week-shortage-card"><CardContent>
    <div className="ops-week-section-heading"><h3>Daily shortage<WeeklyMetricHelp label="Daily shortage">Uncovered staff-hours after breaks, using the same event demand for both rosters. Lower is better.</WeeklyMetricHelp></h3><span>{worst.current>0?`Peak: ${worst.label} · ${number(worst.current)}h`:'No current gap'}</span></div>
    <div className="ops-week-shortage-legend"><span className="current">Current</span><span className="proposed">Proposed</span><small>staff-hours short</small></div>
    <div className="ops-week-shortage-chart" role="img" aria-label={review.days.map(day=>`${day.label}: current ${day.current}, proposed ${day.proposed} uncovered staff-hours`).join('; ')}><ResponsiveContainer width="100%" height="100%"><BarChart data={review.days} margin={{top:8,right:8,left:-22,bottom:0}}><CartesianGrid vertical={false} stroke="var(--chart-grid)" strokeDasharray="3 4"/><XAxis dataKey="label" axisLine={false} tickLine={false} tick={{fill:'var(--chart-axis)',fontSize:10}}/><YAxis axisLine={false} tickLine={false} tick={{fill:'var(--chart-axis)',fontSize:10}}/><Tooltip contentStyle={{background:'var(--chart-tooltip)',border:'1px solid var(--chart-tooltip-border)',borderRadius:8,fontSize:11,color:'var(--foreground)'}}/><Bar dataKey="current" name="Current: staff-hours short" fill="var(--chart-conflict)" radius={[3,3,0,0]}/><Bar dataKey="proposed" name="Proposed: staff-hours short" fill="var(--chart-capacity)" radius={[3,3,0,0]}/></BarChart></ResponsiveContainer></div>
  </CardContent></Card>;
}

function ChangeDetails({row}:{row:WeeklySlotReview}){
  return <div className="ops-week-change-detail">
    <p><b>Peak need: {row.requiredPeakSeats} staff.</b> {row.shiftDelta>0?`Add ${row.shiftDelta} positions to the current ${row.currentSeats}.`:`Remove ${Math.abs(row.shiftDelta)} surplus positions from the current ${row.currentSeats}.`}</p>
    <div className="ops-week-coverage-detail"><div><span>Required coverage</span><b>{number(row.requiredStaffHours)} staff-hours</b><small>{row.requiredPeakSeats} staff at the busiest hour</small></div><div><span>Current coverage</span><b>{number(row.currentCoveredStaffHours)} staff-hours</b><small>{number(row.currentShortStaffHours)} staff-hours short</small></div><div><span>Proposed coverage</span><b>{number(row.proposedCoveredStaffHours)} staff-hours</b><small>{number(row.proposedShortStaffHours)} staff-hours still short</small></div><div><span>Estimated labor change</span><b>{signedMoney(row.costDelta)}</b><small>{money(row.currentCost)} → {money(row.proposedCost)} · {money(TEAM_WAGES[row.team])}/paid hour</small></div></div>
    {row.proposedShortStaffHours>0&&<p className="ops-week-change-warning">{number(row.proposedShortStaffHours)} staff-hours still uncovered after breaks.</p>}
    <div className="ops-week-assignment-compare"><details><summary>Current positions ({row.currentSeats})</summary><AssignmentList assignments={row.currentAssignments}/></details><details><summary>Proposed positions ({row.proposedSeats})</summary><AssignmentList assignments={row.proposedAssignments}/></details></div>
  </div>;
}

export function WeeklyStaffingChanges({review}:{review:WeeklyReview}){
  const [expanded,setExpanded]=useState<string|null>(null);
  const remaining=review.slots.filter(row=>row.proposedShortStaffHours>0);
  return <Card className="ops-week-changes"><CardContent>
    <div className="ops-week-section-heading"><h3>Shift changes</h3><span>{review.addedShifts} added · {review.removedShifts} removed</span></div>
    <div className="ops-week-role-deltas">{Object.entries(review.roleShiftDeltas).map(([team,delta])=><span key={team}>{TEAM_NAMES[team as keyof typeof TEAM_NAMES]} <b>{signed(delta)} shifts</b></span>)}</div>
    {remaining.length>0&&<div className="ops-week-compact-gaps">{remaining.map(row=><span key={row.key}><TriangleAlert size={14}/><b>{number(row.proposedShortStaffHours)}h remains</b> · {row.dayLabel} · {row.shift.replace('-','–')} · {TEAM_NAMES[row.team]}<WeeklyMetricHelp label="Remaining shortage">{row.proposedSeats<row.requiredPeakSeats?'Peak staffing positions remain unfilled.':'Peak headcount is staffed, but modeled breaks leave uncovered workload.'}</WeeklyMetricHelp></span>)}</div>}
    <div className="ops-week-table-scroll" tabIndex={0} aria-label="Recommended staffing changes"><table className="ops-week-change-table"><thead><tr><th>Shift / role</th><th>Staff<WeeklyMetricHelp label="Staff comparison">Current → proposed workers in this 8-hour shift.</WeeklyMetricHelp></th><th>Δ shifts</th><th>Short h<WeeklyMetricHelp label="Shortage comparison">Current → proposed uncovered staff-hours after breaks.</WeeklyMetricHelp></th><th>Δ labor<WeeklyMetricHelp label="Labor change">Proposed shift wage cost minus current shift wage cost.</WeeklyMetricHelp></th><th><span className="sr-only">Details</span></th></tr></thead>{WEEK_DAYS.map((label,day)=>{
      const rows=review.changes.filter(row=>row.day===day);
      return <tbody key={day}><tr className="ops-week-day-group"><th colSpan={6}>{label}{!rows.length&&<span>No changes</span>}</th></tr>{rows.map(row=><Fragment key={row.key}><tr><th><b>{row.shift.replace('-','–')}</b><span>{TEAM_NAMES[row.team]}</span></th><td>{row.currentSeats} → <b>{row.proposedSeats}</b></td><td><span className={`ops-week-shift-delta ${row.shiftDelta>0?'added':'removed'}`}>{row.shiftDelta>0?'Add':'Remove'} {Math.abs(row.shiftDelta)}</span></td><td>{number(row.currentShortStaffHours)} → <b>{number(row.proposedShortStaffHours)}</b></td><td>{signedMoney(row.costDelta)}</td><td><button type="button" className="ops-week-detail-button" aria-label={`${expanded===row.key?'Close':'Details for'} ${row.dayLabel} ${row.shift} ${TEAM_NAMES[row.team]}`} aria-expanded={expanded===row.key} aria-controls={`weekly-change-${row.key}`} onClick={()=>setExpanded(expanded===row.key?null:row.key)}>{expanded===row.key?'Close':'Details'}<ChevronDown size={13}/></button></td></tr>{expanded===row.key&&<tr id={`weekly-change-${row.key}`}><td colSpan={6}><ChangeDetails row={row}/></td></tr>}</Fragment>)}</tbody>})}<tfoot><tr><th colSpan={2}>Net change</th><td>{signed(review.netShifts)} shifts</td><td/><td>{signedMoney(review.incrementalCost)}</td><td/></tr></tfoot></table></div>
  </CardContent></Card>;
}

export function WeeklyProposedSchedule({review,onOpened}:{review:WeeklyReview;onOpened:()=>void}){
  return <details className="ops-week-disclosure ops-week-proposed-schedule" onToggle={event=>{if(event.currentTarget.open)onOpened();}}><summary><span><b>Proposed schedule</b></span><ChevronDown size={17}/></summary><div className="ops-week-schedule-content"><div className="ops-week-table-scroll" tabIndex={0} aria-label="Full proposed shift schedule"><table className="ops-week-change-table"><thead><tr><th>Day</th><th>Shift</th><th>Role</th><th>Staff / need<WeeklyMetricHelp label="Schedule staffing">Scheduled positions / staff needed in the busiest hour of this shift.</WeeklyMetricHelp></th><th>Labor</th><th>Workers &amp; breaks</th></tr></thead><tbody>{review.slots.filter(row=>row.proposedSeats>0||row.requiredPeakSeats>0).map(row=><tr key={row.key}><th>{row.dayLabel}</th><td>{row.shift.replace('-','–')}</td><td>{TEAM_NAMES[row.team]}</td><td>{row.proposedSeats} / {row.requiredPeakSeats}</td><td>{money(row.proposedCost)}</td><td><details><summary>{row.proposedAssignments.length} shift positions</summary><AssignmentList assignments={row.proposedAssignments}/></details></td></tr>)}</tbody></table></div></div></details>;
}
