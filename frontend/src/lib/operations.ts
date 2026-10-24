/** Deterministic synthetic operations replay. This is a planning model, not dispatch. */
export type Team = 'ramp' | 'fuel' | 'service';
export type Week = 'normal' | 'event';
export type DemandLevel = 'Low' | 'Medium' | 'High';
export type Window = {start:number;end:number};
export type Worker = {id:string;name:string;team:Team;qualification:string;shift:Window;break:Window;hourlyRate:number};
export type Aircraft = {id:string;type:string;eta:number;passengers:number;fuelService:boolean;stand:string;unexpected?:boolean;delayMinutes?:number};
export type ServiceTask = {id:string;aircraftId:string;team:Team;label:string;earliest:number;deadline:number;duration:number;crewRequired:number};
export type Assignment = {taskId:string;workerIds:string[];start:number;end:number};
export type TaskResult = {task:ServiceTask;assignment:Assignment|null;previous?:Assignment;reason:string};
export type Crisis = {extraArrivals:number;absentWorkerIds:string[];arrivalDelayMinutes:number;delayedFlightCount:number};
export type TaskRules = Record<Team,{label:string;duration:number;crewRequired:number;startOffset:number;deadlineOffset:number}>;
export const defaultTaskRules:TaskRules={ramp:{label:'Arrival assistance',duration:35,crewRequired:2,startOffset:5,deadlineOffset:75},service:{label:'Guest assistance',duration:15,crewRequired:1,startOffset:0,deadlineOffset:55},fuel:{label:'Fuel service',duration:40,crewRequired:1,startOffset:15,deadlineOffset:115}};
export type Mission = {week:Week;level:DemandLevel;day:number;seed:number;workers:Worker[];aircraft:Aircraft[];tasks:ServiceTask[];rules:TaskRules;source:'synthetic'|'uploaded';sourceName:string};
export type Metrics = {tasks:number;coveredTasks:number;uncoveredTasks:number;coveragePercent:number;requiredWorkerHours:number;uncoveredWorkerHours:number;laborCost:number;reassignedTasks:number};
export type Schedule = {results:TaskResult[];metrics:Metrics};
export type RecoveryChange = {taskId:string;aircraftId:string;label:string;before:string;after:string;reason:string};
export type ReviewRecord = {id:string;status:'approved'|'rejected';manager:string;notes:string;timestamp:string;mission:Pick<Mission,'week'|'level'|'day'|'seed'|'source'|'sourceName'>;crisis:Crisis;metrics:Metrics;assignments:Assignment[];snapshot:{modelVersion:string;aircraft:Aircraft[];workers:Worker[];tasks:ServiceTask[];originalMetrics:Metrics}};
export type UploadedCount = {hour:number;aircraft:number;passengers:number;fuel_requests:number};
export const START=720, END=1230, NOW=840;
export const teamLabels:Record<Team,string>={ramp:'Ramp operations',fuel:'Fuel service',service:'Customer service'};
export const noCrisis:Crisis={extraArrivals:0,absentWorkerIds:[],arrivalDelayMinutes:0,delayedFlightCount:3};
export const stackedCrisis:Crisis={extraArrivals:4,absentWorkerIds:['R-03','R-04'],arrivalDelayMinutes:45,delayedFlightCount:3};
export function clock(minute:number){return `${String(Math.floor(minute/60)).padStart(2,'0')}:${String(Math.round(minute%60)).padStart(2,'0')}`;}
export function rng(seed:number){let state=seed>>>0;return ()=>{state=(1664525*state+1013904223)>>>0;return state/4294967296;};}
const overlap=(a:Window,b:Window)=>a.start<b.end&&b.start<a.end;

export function createWorkers():Worker[]{
  const names=['M. Chen','J. Rivera','A. Brooks','S. Patel','T. Morgan','D. Kim','R. Taylor','C. Ellis','L. Davis'];
  const teams:Team[]=['ramp','ramp','ramp','ramp','ramp','fuel','fuel','service','service'];
  const breaks=[780,810,900,930,960,870,990,840,900];
  const index={ramp:0,fuel:0,service:0};
  return teams.map((team,i)=>({id:`${team==='ramp'?'R':team==='fuel'?'F':'C'}-${String(++index[team]).padStart(2,'0')}`,name:names[i],team,
    qualification:team==='ramp'?'Synthetic ramp qualification':team==='fuel'?'Synthetic fuel-service qualification':'Synthetic customer-service qualification',
    shift:{start:690,end:1230},break:{start:breaks[i],end:breaks[i]+30},hourlyRate:team==='ramp'?32:team==='fuel'?35:26}));
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
    const selected=uploaded.rows.filter(r=>Math.floor(r.hour/24)===day&&r.hour%24>=12&&r.hour%24<20);
    const count=Math.round(selected.reduce((sum,r)=>sum+r.aircraft*factor,0));
    if(count>80)throw new Error('This task-replay demo supports up to 80 aircraft in the selected eight-hour window. Reduce the uploaded counts or event factor.');
    let carry=0;
    for(const row of selected){
      const expected=row.aircraft*factor+carry,n=Math.floor(expected);carry=expected-n;
      for(let j=0;j<n;j++)aircraft.push({id:`DEMO-${String(101+aircraft.length)}`,type:types[aircraft.length%4],eta:(row.hour%24)*60+Math.floor((j+.5)*60/n),
        passengers:Math.max(0,Math.round(row.passengers/Math.max(1,row.aircraft))),fuelService:random()<Math.min(1,row.fuel_requests/Math.max(.001,row.aircraft)),stand:`A${aircraft.length%6+1}`});
    }
  }else{
    const count=Math.round(17*[.8,.85,.9,1,1.1,1.2,1.05][day]*factor);
    aircraft=Array.from({length:count},(_,i)=>{
      const f=(i+.5)/count;
      const eta=5*Math.round((START+15+f*420+25*Math.sin(f*Math.PI*2)+(random()-.5)*12)/5);
      return {id:`DEMO-${101+i}`,type:types[i%4],eta,passengers:3+Math.floor(random()*7),fuelService:random()<.7,stand:`A${i%6+1}`};
    });
  }
  aircraft.sort((a,b)=>a.eta-b.eta||a.id.localeCompare(b.id));
  return {week,level,day,seed,workers,aircraft,tasks:tasksForAircraft(aircraft,rules),rules,source:uploaded?'uploaded':'synthetic',sourceName:uploaded?.name??'Fixed-seed synthetic FBO scenario'};
}
export function applyCrisis(original:Mission,crisis:Crisis):Mission{
  const delayed=new Set(original.aircraft.filter(a=>a.eta>=NOW).slice(0,crisis.delayedFlightCount).map(a=>a.id));
  const aircraft=original.aircraft.map(a=>({...a,eta:a.eta+(delayed.has(a.id)?crisis.arrivalDelayMinutes:0),delayMinutes:delayed.has(a.id)?crisis.arrivalDelayMinutes:0}));
  for(let i=0;i<crisis.extraArrivals;i++)aircraft.push({id:`SURGE-${i+1}`,type:i%2?'Citation Latitude':'Gulfstream G650',eta:NOW+10+i*10,passengers:6,fuelService:true,stand:`B${i%3+1}`,unexpected:true,delayMinutes:0});
  aircraft.sort((a,b)=>a.eta-b.eta||a.id.localeCompare(b.id));
  return {...original,aircraft,tasks:tasksForAircraft(aircraft,original.rules)};
}
export function workerAvailable(worker:Worker,window:Window,crisis:Crisis=noCrisis){
  return window.start>=worker.shift.start&&window.end<=worker.shift.end&&!overlap(window,worker.break)&&
    !(crisis.absentWorkerIds.includes(worker.id)&&overlap(window,{start:NOW,end:END}));
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
  const booked=new Map(mission.workers.map(w=>[w.id,[] as Assignment[]]));
  const frozen=new Map<string,TaskResult>();
  if(previous)for(const result of previous.results){
    if(result.assignment&&result.assignment.start<NOW){
      frozen.set(result.task.id,result);
      for(const id of result.assignment.workerIds)booked.get(id)?.push(result.assignment);
    }
  }
  const ordered=[...mission.tasks].sort((a,b)=>a.deadline-b.deadline||a.earliest-b.earliest||a.id.localeCompare(b.id));
  const results=ordered.map(task=>{
    if(frozen.has(task.id))return {...frozen.get(task.id)!,task};
    const qualified=mission.workers.filter(w=>w.team===task.team);
    const earliest=5*Math.ceil(Math.max(task.earliest,previous?NOW:START)/5);
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
export function capacitySeries(mission:Mission,crisis:Crisis=noCrisis){
  return Array.from({length:17},(_,i)=>{
    const start=START+i*30,end=start+30;
    const demand=mission.tasks.reduce((n,t)=>n+(overlap({start:t.earliest,end:t.earliest+t.duration},{start,end})?t.crewRequired:0),0);
    const capacity=mission.workers.filter(w=>workerAvailable(w,{start:start+14,end:start+15},crisis)).length;
    return {time:clock(start),minute:start,demand,capacity};
  });
}
export function operationalRisk(metrics:Metrics){return metrics.uncoveredTasks===0?'low':metrics.uncoveredTasks/Math.max(1,metrics.tasks)>.15?'high':'watch';}
