/** Deterministic synthetic operations replay. This is a planning model, not dispatch. */
import {laxArrivalProfiles} from './lax-arrivals.ts';


export type Team = 'ramp' | 'fuel' | 'service';
export type Week = 'normal' | 'event';
export type DemandLevel = 'Low' | 'Medium' | 'High';
export type Window = {start:number;end:number};
export type Worker = {id:string;name:string;team:Team;qualification:string;shift:Window;break:Window;hourlyRate:number;proposed?:boolean};
export type Aircraft = {id:string;type:string;eta:number;passengers:number;fuelService:boolean;stand:string;unexpected?:boolean;delayMinutes?:number};
export type ServiceTask = {id:string;aircraftId:string;team:Team;label:string;earliest:number;deadline:number;duration:number;crewRequired:number};
export type Assignment = {taskId:string;workerIds:string[];start:number;end:number};
export type TaskResult = {task:ServiceTask;assignment:Assignment|null;previous?:Assignment;reason:string};
export type Crisis = {extraArrivals:number;absentWorkerIds:string[];arrivalDelayMinutes:number;delayedFlightCount:number;simulationTime?:number};
export type TaskRules = Record<Team,{label:string;duration:number;crewRequired:number;startOffset:number;deadlineOffset:number}>;
export const defaultTaskRules:TaskRules={ramp:{label:'Arrival assistance',duration:35,crewRequired:2,startOffset:5,deadlineOffset:75},service:{label:'Guest assistance',duration:15,crewRequired:1,startOffset:0,deadlineOffset:55},fuel:{label:'Fuel service',duration:40,crewRequired:1,startOffset:15,deadlineOffset:115}};
export type Mission = {week:Week;level:DemandLevel;day:number;seed:number;workers:Worker[];aircraft:Aircraft[];tasks:ServiceTask[];rules:TaskRules;source:'synthetic'|'uploaded';sourceName:string};
export type Metrics = {tasks:number;coveredTasks:number;uncoveredTasks:number;coveragePercent:number;requiredWorkerHours:number;uncoveredWorkerHours:number;laborCost:number;reassignedTasks:number};
export type Schedule = {results:TaskResult[];metrics:Metrics};
export type RecoveryChange = {taskId:string;aircraftId:string;label:string;before:string;after:string;reason:string};
export type HireCounts = Record<Team,number>;
export type ReviewRecord = {id:string;status:'approved'|'rejected';manager:string;notes:string;timestamp:string;mission:Pick<Mission,'week'|'level'|'day'|'seed'|'source'|'sourceName'>;crisis:Crisis;metrics:Metrics;hiringPlan:{counts:HireCounts;incrementalPerShift:number;weeklyIfRepeated:number};assignments:Assignment[];snapshot:{modelVersion:string;aircraft:Aircraft[];workers:Worker[];tasks:ServiceTask[];originalMetrics:Metrics}};
export type UploadedCount = {hour:number;aircraft:number;passengers:number;fuel_requests:number};
export const START=0, END=1440, SERVICE_END=1560, NOW=840;
export const teamLabels:Record<Team,string>={ramp:'Ramp operations',fuel:'Fuel service',service:'Customer service'};
export const noCrisis:Crisis={extraArrivals:0,absentWorkerIds:[],arrivalDelayMinutes:0,delayedFlightCount:3,simulationTime:NOW};
export const stackedCrisis:Crisis={extraArrivals:4,absentWorkerIds:['R-03','R-04'],arrivalDelayMinutes:45,delayedFlightCount:3};
export function simulationMinute(crisis:Crisis=noCrisis){return Math.max(START,Math.min(END,crisis.simulationTime??NOW));}
export function clock(minute:number){
  const day=Math.floor(minute/1440),inDay=minute-day*1440;
  const hour=Math.floor(inDay/60),minutes=Math.round(inDay%60);
  const time=day&&inDay===0?`${String(day*24).padStart(2,'0')}:00`:`${String(hour).padStart(2,'0')}:${String(minutes).padStart(2,'0')}`;
  return day&&inDay!==0?`${time} +${day}d`:time;
}
export function rng(seed:number){let state=seed>>>0;return ()=>{state=(1664525*state+1013904223)>>>0;return state/4294967296;};}
const overlap=(a:Window,b:Window)=>a.start<b.end&&b.start<a.end;

export function createWorkers():Worker[]{
  const names=['M. Chen','J. Rivera','A. Brooks','S. Patel','T. Morgan','D. Kim','R. Taylor','C. Ellis','L. Davis','K. Nguyen','P. Wilson','J. Thompson'];
  const teams:Team[]=['ramp','ramp','fuel','service','ramp','ramp','fuel','service','ramp','ramp','fuel','service'];
  const shiftStarts=[0,480,960];
  const index={ramp:0,fuel:0,service:0};
  return teams.map((team,i)=>{
    const shiftStart=shiftStarts[Math.floor(i/4)],breakStart=shiftStart+240+(i%4)*15;
    return {id:`${team==='ramp'?'R':team==='fuel'?'F':'C'}-${String(++index[team]).padStart(2,'0')}`,name:names[i],team,
      qualification:team==='ramp'?'Synthetic ramp qualification':team==='fuel'?'Synthetic fuel-service qualification':'Synthetic customer-service qualification',
      shift:{start:shiftStart,end:shiftStart+480},break:{start:breakStart,end:breakStart+30},hourlyRate:team==='ramp'?32:team==='fuel'?35:26};
  });
}
export const noHires:HireCounts={ramp:0,fuel:0,service:0};
export function createProposedWorkers(mission:Mission,counts:HireCounts):Worker[]{
  return (['ramp','fuel','service'] as Team[]).flatMap((team,teamIndex)=>{
    const template=mission.workers.find(worker=>worker.team===team);
    if(!template)return [];
    return Array.from({length:Math.max(0,Math.min(20,Math.floor(counts[team]||0)))},(_,i)=>{
      const shiftStart=[0,480,960][(i+teamIndex)%3],breakStart=shiftStart+240+((i+teamIndex)%4)*15;
      return {id:`PLAN-${team.toUpperCase()}-${String(i+1).padStart(2,'0')}`,name:`Proposed ${teamLabels[team]} hire ${i+1}`,team,
        qualification:template.qualification,shift:{start:shiftStart,end:shiftStart+480},break:{start:breakStart,end:breakStart+30},hourlyRate:template.hourlyRate,proposed:true};
    });
  });
}
export function estimatedHireShiftCost(workers:Worker[]){
  return workers.reduce((sum,worker)=>sum+(worker.shift.end-worker.shift.start)/60*worker.hourlyRate,0);
}
export function tasksForAircraft(aircraft:Aircraft[],rules:TaskRules=defaultTaskRules):ServiceTask[]{
  return aircraft.flatMap(a=>(['ramp','service',...(a.fuelService?['fuel']:[])] as Team[]).map(team=>{
    const rule=rules[team];
    return {id:`${a.id}-${team==='ramp'?'R':team==='fuel'?'F':'C'}`,aircraftId:a.id,team,label:rule.label,earliest:a.eta+rule.startOffset,deadline:a.eta+rule.deadlineOffset,duration:rule.duration,crewRequired:rule.crewRequired};
  }));
}
export function createMission(week:Week='event',level:DemandLevel='Medium',day=5,seed=42,uploaded?:{name:string;rows:UploadedCount[]},rules:TaskRules=defaultTaskRules,workers:Worker[]=createWorkers()):Mission{
  for(const rule of Object.values(rules))if(!Number.isFinite(rule.duration)||rule.duration<5||rule.duration>120||!Number.isInteger(rule.crewRequired)||rule.crewRequired<1||rule.crewRequired>6||!Number.isFinite(rule.startOffset)||rule.startOffset<0||!Number.isFinite(rule.deadlineOffset)||rule.deadlineOffset<rule.startOffset+rule.duration)throw new Error('Invalid task rules: use 5–120 minute tasks, 1–6 qualified crew, and a service window that fits the task.');
  const random=rng(seed+day*101),factor=week==='event'?{Low:1.15,Medium:1.4,High:1.7}[level]:1;
  let aircraft:Aircraft[]=[];
  const types=['Gulfstream G650','Challenger 350','Citation Latitude','Phenom 300'];
  if(uploaded){
    const selected=uploaded.rows.filter(r=>Math.floor(r.hour/24)===day);
    const count=Math.round(selected.reduce((sum,r)=>sum+r.aircraft*factor,0));
    if(count>80)throw new Error('This task-replay demo supports up to 80 aircraft in the selected 24-hour day. Reduce the uploaded counts or event factor.');
    let carry=0;
    for(const row of selected){
      const expected=row.aircraft*factor+carry,n=Math.floor(expected);carry=expected-n;
      for(let j=0;j<n;j++)aircraft.push({id:`DEMO-${String(101+aircraft.length)}`,type:types[aircraft.length%4],eta:(row.hour%24)*60+Math.floor((j+.5)*60/n),
        passengers:Math.max(0,Math.round(row.passengers/Math.max(1,row.aircraft))),fuelService:random()<Math.min(1,row.fuel_requests/Math.max(.001,row.aircraft)),stand:`A${aircraft.length%6+1}`});
    }
  }else{
    const count=Math.round(17*[.8,.85,.9,1,1.1,1.2,1.05][day]*factor);
    const weights=Array.from({length:24},(_,hour)=>.2+.8*(.5+.5*Math.cos((hour-14)*Math.PI/12)));
    const weightTotal=weights.reduce((sum,weight)=>sum+weight,0);
    let carry=0;
    for(let hour=0;hour<24;hour++){
      const expected=count*weights[hour]/weightTotal+carry,n=Math.floor(expected);carry=expected-n;
      for(let j=0;j<n;j++){
        const minute=Math.max(0,Math.min(59,Math.floor((j+.5)*60/n+(random()-.5)*8)));
        aircraft.push({id:`DEMO-${101+aircraft.length}`,type:types[aircraft.length%4],eta:hour*60+minute,
          passengers:3+Math.floor(random()*7),fuelService:random()<.7,stand:`A${aircraft.length%6+1}`});
      }
    }
  }
  aircraft.sort((a,b)=>a.eta-b.eta||a.id.localeCompare(b.id));
  return {week,level,day,seed,workers,aircraft,tasks:tasksForAircraft(aircraft,rules),rules,source:uploaded?'uploaded':'synthetic',sourceName:uploaded?.name??'Fixed-seed synthetic FBO scenario'};
}
export function applyCrisis(original:Mission,crisis:Crisis):Mission{
  const now=simulationMinute(crisis);
  const delayed=new Set(original.aircraft.filter(a=>a.eta>=now).slice(0,crisis.delayedFlightCount).map(a=>a.id));
  const aircraft=original.aircraft.map(a=>({...a,eta:a.eta+(delayed.has(a.id)?crisis.arrivalDelayMinutes:0),delayMinutes:delayed.has(a.id)?crisis.arrivalDelayMinutes:0}));
  for(let i=0;i<crisis.extraArrivals;i++)aircraft.push({id:`SURGE-${i+1}`,type:i%2?'Citation Latitude':'Gulfstream G650',eta:now+10+i*10,passengers:6,fuelService:true,stand:`B${i%3+1}`,unexpected:true,delayMinutes:0});
  aircraft.sort((a,b)=>a.eta-b.eta||a.id.localeCompare(b.id));
  return {...original,aircraft,tasks:tasksForAircraft(aircraft,original.rules)};
}
export function maxSafeArrivalDelay(mission:Mission,crisis:Crisis,limit=120,step=15){
  const now=simulationMinute(crisis);
  const selected=new Set(mission.aircraft.filter(a=>a.eta>=now).slice(0,crisis.delayedFlightCount).map(a=>a.id));
  const tasks=mission.tasks.filter(task=>selected.has(task.aircraftId));
  if(!tasks.length)return limit;
  const availableDelay=Math.min(limit,...tasks.map(task=>SERVICE_END-task.earliest-task.duration));
  return Math.max(0,step*Math.floor(availableDelay/step));
}
export function crisisCreatesOutOfScopeTasks(mission:Mission,crisis:Crisis){
  const now=simulationMinute(crisis),before=new Map(mission.tasks.map(task=>[task.id,task]));
  return applyCrisis(mission,crisis).tasks.some(task=>{
    const original=before.get(task.id),crisisAffected=!original||task.earliest!==original.earliest;
    return crisisAffected&&(task.earliest<now||task.earliest+task.duration>SERVICE_END);
  });
}
export function workerAvailable(worker:Worker,window:Window,crisis:Crisis=noCrisis){
  const firstDay=Math.floor(window.start/1440)-1,lastDay=Math.floor(window.end/1440)+1;
  let inShift=false,onBreak=false;
  for(let day=firstDay;day<=lastDay;day++){
    const offset=day*1440,shift={start:offset+worker.shift.start,end:offset+worker.shift.end};
    if(window.start>=shift.start&&window.end<=shift.end)inShift=true;
    if(overlap(window,{start:offset+worker.break.start,end:offset+worker.break.end}))onBreak=true;
  }
  return inShift&&!onBreak&&!(crisis.absentWorkerIds.includes(worker.id)&&overlap(window,{start:simulationMinute(crisis),end:SERVICE_END}));
}
export function metricsFor(results:TaskResult[],workers:Worker[],previous?:Schedule):Metrics{
  const required=results.reduce((n,r)=>n+r.task.duration*r.task.crewRequired,0);
  const uncovered=results.filter(r=>!r.assignment).reduce((n,r)=>n+r.task.duration*r.task.crewRequired,0);
  const before=new Map(previous?.results.map(r=>[r.task.id,r.assignment])??[]);
  return {tasks:results.length,coveredTasks:results.filter(r=>r.assignment).length,uncoveredTasks:results.filter(r=>!r.assignment).length,
    coveragePercent:required?Math.round(1000*(required-uncovered)/required)/10:100,
    requiredWorkerHours:Math.round(required/6)/10,uncoveredWorkerHours:Math.round(uncovered/6)/10,
    laborCost:workers.reduce((n,w)=>n+(w.shift.end-w.shift.start)/60*w.hourlyRate,0),
    reassignedTasks:results.filter(r=>{const b=before.get(r.task.id);return b&&r.assignment&&(b.start!==r.assignment.start||b.workerIds.join()!==r.assignment.workerIds.join());}).length};
}
export function scheduleTasks(mission:Mission,crisis:Crisis=noCrisis,previous?:Schedule):Schedule{
  const now=simulationMinute(crisis);
  const booked=new Map(mission.workers.map(w=>[w.id,[] as Assignment[]]));
  const frozen=new Map<string,TaskResult>();
  if(previous)for(const result of previous.results){
    if(result.assignment&&result.assignment.start<now){
      frozen.set(result.task.id,result);
      for(const id of result.assignment.workerIds)booked.get(id)?.push(result.assignment);
    }
  }
  const ordered=[...mission.tasks].sort((a,b)=>a.deadline-b.deadline||a.earliest-b.earliest||a.id.localeCompare(b.id));
  const results=ordered.map(task=>{
    if(frozen.has(task.id))return {...frozen.get(task.id)!,task};
    const qualified=mission.workers.filter(w=>w.team===task.team);
    const earliest=5*Math.ceil(Math.max(task.earliest,previous?now:START)/5);
    let assignment:Assignment|null=null;
    for(let start=earliest;start+task.duration<=task.deadline;start+=5){
      const window={start,end:start+task.duration};
      const available=qualified.filter(w=>workerAvailable(w,window,crisis)&&!booked.get(w.id)!.some(a=>overlap(a,window)))
        .sort((a,b)=>booked.get(a.id)!.reduce((n,v)=>n+v.end-v.start,0)-booked.get(b.id)!.reduce((n,v)=>n+v.end-v.start,0)||a.id.localeCompare(b.id));
      if(available.length>=task.crewRequired){
        assignment={taskId:task.id,workerIds:available.slice(0,task.crewRequired).map(w=>w.id),...window};
        for(const id of assignment.workerIds)booked.get(id)!.push(assignment);
        break;
      }
    }
    return {task,assignment,reason:assignment?'Qualified crew available within the service window.':'No qualified crew available before the service deadline.'};
  });
  return {results,metrics:metricsFor(results,mission.workers,previous)};
}
export function evaluateOriginal(mission:Mission,original:Schedule,crisis:Crisis):Schedule{
  const assignments=new Map(original.results.map(r=>[r.task.id,r.assignment]));
  const results=mission.tasks.map(task=>{
    const previous=assignments.get(task.id)??undefined;
    let reason='Original assignment remains feasible.';
    if(!previous)reason=task.aircraftId.startsWith('SURGE')?'Unexpected arrival has no original crew assignment.':'Task was already uncovered in the original plan.';
    else if(previous.start<task.earliest||previous.end>task.deadline)reason='Arrival delay moved the aircraft outside its assigned service slot.';
    else if(previous.workerIds.some(id=>!workerAvailable(mission.workers.find(w=>w.id===id)!,previous,crisis)))reason='Assigned crew is unavailable during the service window.';
    const feasible=reason==='Original assignment remains feasible.';
    return {task,assignment:feasible?previous!:null,previous,reason};
  });
  return {results,metrics:metricsFor(results,mission.workers)};
}
export function recoveryChanges(before:Schedule,after:Schedule):RecoveryChange[]{
  const prior=new Map(before.results.map(r=>[r.task.id,r]));
  return after.results.flatMap(result=>{
    if(!result.assignment)return [];
    const old=prior.get(result.task.id),a=result.assignment;
    if(old?.assignment&&old.assignment.start===a.start&&old.assignment.workerIds.join()===a.workerIds.join())return [];
    return [{taskId:result.task.id,aircraftId:result.task.aircraftId,label:result.task.label,
      before:old?.assignment?`${old.assignment.workerIds.join(' + ')} · ${clock(old.assignment.start)}`:'Uncovered',
      after:`${a.workerIds.join(' + ')} · ${clock(a.start)}`,
      reason:old?.assignment?`Recomputed at ${clock(a.start)} with ${result.task.crewRequired} qualified ${teamLabels[result.task.team].toLowerCase()} crew. Shift, break and overlap checks passed; feasible in-progress work retained.`:`${old?.reason??'Task needed crew.'} Reassigned to qualified, available crew; shift, break and overlap checks passed.`}];
  });
}
function crewDemandInWindow(mission:Mission,start:number,end:number){
  return mission.tasks.reduce((n,t)=>n+(overlap({start:t.earliest,end:t.earliest+t.duration},{start,end})?t.crewRequired:0),0);
}
export function capacitySeries(mission:Mission,crisis:Crisis=noCrisis){
  return Array.from({length:52},(_,i)=>{
    const start=START+i*30,end=start+30;
    const demand=crewDemandInWindow(mission,start,end);
    const capacity=mission.workers.filter(w=>workerAvailable(w,{start:start+14,end:start+15},crisis)).length;
    return {time:clock(start),minute:start,demand,capacity};
  });
}
export function observedLaxArrivalSeries(day:number){
  return laxArrivalProfiles[day].halfHours.map((arrivals,index)=>{
    const minute=index*30;
    return {time:clock(minute),minute,arrivals};
  });
}
export function arrivalDemandSeries(day:number){
  const profile=laxArrivalProfiles[day];
  return Array.from({length:17},(_,i)=>{
    const start=12*60+i*30,end=start+30;
    const arrivals=profile.halfHours[24+i];
    let demand=0;
    for(let flight=0;flight<arrivals;flight++){
      const eta=start+Math.floor((flight+.5)*30/arrivals);
      for(const task of [
        {start:eta+5,end:eta+40,crew:2},
        {start:eta,end:eta+15,crew:1},
        {start:eta+15,end:eta+55,crew:.7},
      ]){
        if(overlap({start:task.start,end:task.end},{start,end}))demand+=task.crew;
      }
    }
    return {time:clock(start),minute:start,arrivals,demand:Math.round(demand*10)/10};
  });
}
export function operationalRisk(metrics:Metrics){return metrics.uncoveredTasks===0?'low':metrics.uncoveredTasks/Math.max(1,metrics.tasks)>.15?'high':'watch';}
