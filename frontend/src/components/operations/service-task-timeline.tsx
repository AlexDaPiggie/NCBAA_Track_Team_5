'use client';

import {Check,PlaneLanding,TriangleAlert} from 'lucide-react';
import {Tooltip,TooltipContent,TooltipTrigger} from '@/components/ui/tooltip';
import {START,SERVICE_END,NOW,clock,teamLabels,type TaskResult} from '@/lib/operations';
import {groupTaskTimeline} from '@/lib/task-timeline';

const left=(minute:number)=>`${(minute-START)/(SERVICE_END-START)*100}%`;
function SimulationTimeMarker({tabbable,minute}:{tabbable:boolean;minute:number}){
  const label=`Simulation time: ${clock(minute)} PST`;
  return <Tooltip delayDuration={100}><TooltipTrigger asChild><button type="button" className="ops-now-line ops-now-marker" style={{left:left(minute)}} aria-label={label} tabIndex={tabbable?0:-1}/></TooltipTrigger><TooltipContent side="top" sideOffset={5}>{label}</TooltipContent></Tooltip>;
}
export function ServiceTaskTimeline({results,onSelect,recoveryStatus=false,simulationTime=NOW}:{results:TaskResult[];onSelect:(result:TaskResult)=>void;recoveryStatus?:boolean;simulationTime?:number}){
  const groups=groupTaskTimeline(results,START,SERVICE_END);
  if(!results.length)return <div className="ops-task-empty"><Check size={18}/><p>No tasks match this filter.</p></div>;
  return <div className="ops-timeline-scroll" tabIndex={0} aria-label="Service tasks grouped by task type"><div className="ops-timeline ops-task-view">
    {groups.map(group=><section className={`ops-task-group ${group.team}`} key={group.team} aria-label={group.label}>
      <div className="ops-task-group-heading"><span><PlaneLanding size={15}/><b>{group.label}</b><small>{teamLabels[group.team]}</small></span><div>{group.count} jobs <i/> {group.count-group.uncovered} covered {group.uncovered>0&&<><i/><strong><TriangleAlert size={11}/>{group.uncovered} uncovered</strong></>}</div></div>
      <div className="ops-timeline-head"><span>SERVICE TASK / PARALLEL JOBS</span><div>{[0,240,480,720,960,1200,1440,1560].map(minute=><span key={minute} style={{left:left(minute)}}>{clock(minute)}</span>)}</div></div>
      {group.lanes.map((lane,index)=><div className="ops-timeline-row ops-service-lane" key={index}><div className="ops-worker-label ops-service-lane-label"><span className="ops-task-lane-number">{String(index+1).padStart(2,'0')}</span><div><b>Parallel jobs</b><small>{lane.length} aircraft services · lane {index+1}</small></div></div><div className="ops-time-track"><SimulationTimeMarker tabbable={index===0} minute={simulationTime}/>{lane.map(({result,start,end})=>{
        const status=!result.assignment?'conflict':recoveryStatus?'recovered':result.assignment.end<=simulationTime?'complete':'assigned';
        const aircraftNumber=result.task.aircraftId.replace('DEMO-','').replace('SURGE-','S');
        return <Tooltip key={result.task.id}><TooltipTrigger asChild><button className={`ops-task-block ops-service-task-block ${status} ${group.team}`} style={{left:left(start),width:`${(end-start)/(SERVICE_END-START)*100}%`}} onClick={()=>onSelect(result)} aria-label={`${result.task.aircraftId}, ${result.task.label}, ${result.assignment?'assigned':'uncovered'}, ${clock(start)} to ${clock(end)}, ${result.task.crewRequired} crew required`}><span>{aircraftNumber}</span></button></TooltipTrigger><TooltipContent><b>{result.task.aircraftId} · {result.task.label}</b><br/>{result.assignment?'Assigned':'Requested work'}: {clock(start)}–{clock(end)}<br/>{result.assignment?(recoveryStatus?'Covered by candidate':`Crew: ${result.assignment.workerIds.join(' + ')}`):`UNCOVERED: ${result.reason}`}<br/>{result.task.crewRequired} crew required · finish by {clock(result.task.deadline)}</TooltipContent></Tooltip>;
      })}</div></div>)}
    </section>)}
  </div></div>;
}
