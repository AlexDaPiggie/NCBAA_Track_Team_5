import test from 'node:test';
import assert from 'node:assert/strict';
import {createMission,applyCrisis,scheduleTasks,evaluateOriginal,recoveryChanges,workerAvailable,noCrisis,stackedCrisis,NOW,defaultTaskRules,arrivalDemandSeries} from '../src/lib/operations.ts';
import {laxArrivalProfiles} from '../src/lib/lax-arrivals.ts';
import {sampleDemand} from '../src/demand-csv.ts';

function checkConstraints(mission,schedule,crisis){
  const byWorker=new Map(mission.workers.map(w=>[w.id,[]]));
  for(const r of schedule.results){
    if(!r.assignment)continue;
    const a=r.assignment;
    assert.equal(a.workerIds.length,r.task.crewRequired);
    assert.equal(new Set(a.workerIds).size,r.task.crewRequired);
    assert.ok(a.start>=r.task.earliest);
    assert.ok(a.end<=r.task.deadline);
    assert.equal(a.end-a.start,r.task.duration);
    for(const id of a.workerIds){
      const worker=mission.workers.find(w=>w.id===id);
      assert.equal(worker.team,r.task.team);
      assert.ok(workerAvailable(worker,a,crisis));
      byWorker.get(id).push(a);
    }
  }
  for(const tasks of byWorker.values()){
    tasks.sort((a,b)=>a.start-b.start);
    for(let i=1;i<tasks.length;i++)assert.ok(tasks[i-1].end<=tasks[i].start,'one worker cannot perform overlapping tasks');
  }
}
test('normal and event fixtures are deterministic, with eligible assignments',()=>{
  const event=createMission(),normal=createMission('normal');
  assert.deepEqual(event,createMission());
  assert.equal(normal.source,'synthetic');
  assert.ok(event.aircraft.length>normal.aircraft.length);
  checkConstraints(event,scheduleTasks(event),noCrisis);
});
test('arrival-demand chart buckets arrivals and modeled crew demand into half-hour windows',()=>{
  const mission=createMission();
  const originalMission=structuredClone(mission);
  const series=arrivalDemandSeries(mission.day);
  assert.equal(series.length,17);
  assert.equal(series[0].time,'12:00');
  assert.equal(series.at(-1).time,'20:00');
  assert.deepEqual(series.map(row=>row.arrivals),laxArrivalProfiles[mission.day].halfHours.slice(24,41));
  assert.equal(series.reduce((sum,row)=>sum+row.arrivals,0),laxArrivalProfiles[mission.day].halfHours.slice(24,41).reduce((sum,n)=>sum+n,0));
  assert.deepEqual(mission,originalMission);
  assert.ok(series.some(row=>row.demand>0));
});
test('crisis adds aircraft, shifts arrival windows, and retains original assignments',()=>{
  const mission=createMission(),original=scheduleTasks(mission),affected=applyCrisis(mission,stackedCrisis);
  assert.equal(affected.aircraft.length,mission.aircraft.length+4);
  assert.equal(affected.aircraft.filter(a=>a.delayMinutes===45).length,3);
  const fixed=evaluateOriginal(affected,original,stackedCrisis);
  const originalById=new Map(original.results.map(r=>[r.task.id,r.assignment]));
  for(const r of fixed.results)if(r.assignment)assert.deepEqual(r.assignment,originalById.get(r.task.id));
  assert.ok(fixed.results.some(r=>!r.assignment&&r.reason.includes('arrival')));
  assert.ok(fixed.metrics.uncoveredTasks>=original.metrics.uncoveredTasks);
  assert.equal(fixed.metrics.laborCost,original.metrics.laborCost);
});
test('recovery is calculated on the same tasks, obeys constraints, and preserves feasible past work',()=>{
  const mission=createMission(),original=scheduleTasks(mission),affected=applyCrisis(mission,stackedCrisis);
  const fixed=evaluateOriginal(affected,original,stackedCrisis),candidate=scheduleTasks(affected,stackedCrisis,fixed);
  assert.deepEqual(candidate,scheduleTasks(affected,stackedCrisis,fixed));
  checkConstraints(affected,candidate,stackedCrisis);
  assert.equal(candidate.metrics.tasks,fixed.metrics.tasks);
  assert.equal(candidate.metrics.requiredWorkerHours,fixed.metrics.requiredWorkerHours);
  assert.equal(candidate.metrics.laborCost,fixed.metrics.laborCost);
  for(const r of fixed.results)if(r.assignment&&r.assignment.start<NOW){
    assert.deepEqual(candidate.results.find(c=>c.task.id===r.task.id).assignment,r.assignment);
  }
  assert.ok(recoveryChanges(fixed,candidate).every(c=>c.reason.length>20));
});
test('complete absence leaves future tasks uncovered instead of inventing recovery',()=>{
  const mission=createMission(),original=scheduleTasks(mission);
  const crisis={...noCrisis,absentWorkerIds:mission.workers.map(w=>w.id)};
  const affected=applyCrisis(mission,crisis),fixed=evaluateOriginal(affected,original,crisis),candidate=scheduleTasks(affected,crisis,fixed);
  assert.ok(candidate.results.filter(r=>r.task.earliest>=NOW).every(r=>!r.assignment));
  assert.ok(candidate.metrics.uncoveredTasks>0);
});
test('sample CSV can drive every day/case without exceeding task-replay limits',()=>{
  for(let day=0;day<7;day++)for(const level of ['Low','Medium','High']){
    const mission=createMission('event',level,day,42,{name:'sample.csv',rows:sampleDemand()});
    assert.equal(mission.source,'uploaded');assert.ok(mission.aircraft.length<=80);
  }
});
test('task assumptions change actual workload and are retained through a crisis',()=>{
  const rules={...defaultTaskRules,ramp:{...defaultTaskRules.ramp,duration:20}};
  const mission=createMission('event','Medium',5,42,undefined,rules);
  assert.ok(scheduleTasks(mission).metrics.requiredWorkerHours<scheduleTasks(createMission()).metrics.requiredWorkerHours);
  assert.ok(applyCrisis(mission,stackedCrisis).tasks.filter(t=>t.team==='ramp').every(t=>t.duration===20));
  assert.throws(()=>createMission('event','Medium',5,42,undefined,{...rules,ramp:{...rules.ramp,crewRequired:0}}),/Invalid task rules/);
});
