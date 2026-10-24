import test from 'node:test';
import assert from 'node:assert/strict';
import {createWorkspace,currentSession,patchSession,switchScenario,applyDisruption,scenarioKey} from '../src/lib/recovery-workspace.ts';
import {demoOperations} from '../src/lib/operations-api.ts';
import {defaultTaskRules,createWorkers,noCrisis,stackedCrisis} from '../src/lib/operations.ts';
import {sampleDemand} from '../src/demand-csv.ts';

const config={week:'event',level:'Low',day:5,seed:42};
function candidate(workspace){
  const {mission,original}=demoOperations.loadMission(workspace.config);
  return demoOperations.recover({mission,original,crisis:currentSession(workspace).applied});
}

test('Low → Medium → High → Low restores independent recovery and disruption sessions',()=>{
  let workspace=applyDisruption(createWorkspace(config));
  workspace=patchSession(workspace,{recoveryRequested:true,manager:'Demo reviewer',notes:'Review ramp gaps'});
  const low=currentSession(workspace),lowResult=candidate(workspace);
  workspace=switchScenario(workspace,{...config,level:'Medium'});
  assert.equal(currentSession(workspace).recoveryRequested,false);
  assert.deepEqual(currentSession(workspace).applied,noCrisis);
  workspace=patchSession(workspace,{recoveryRequested:true});
  const medium=currentSession(workspace);
  workspace=switchScenario(workspace,{...config,level:'High'});
  assert.equal(currentSession(workspace).recoveryRequested,false);
  workspace=switchScenario(workspace,{...config});
  assert.deepEqual(currentSession(workspace),low);
  assert.deepEqual(candidate(workspace),lowResult);
  workspace=switchScenario(workspace,{...config,level:'Medium'});
  assert.deepEqual(currentSession(workspace),medium);
});

test('same inputs are a no-op; changed date, source, rules, or crew cannot inherit a candidate',()=>{
  let workspace=patchSession(createWorkspace(config),{recoveryRequested:true});
  assert.equal(switchScenario(workspace,{seed:42,day:5,level:'Low',week:'event',upload:undefined}),workspace);
  const workers=createWorkers();
  const variations=[{...config,day:4},{...config,week:'normal'},{...config,seed:7},
    {...config,upload:{name:'counts.csv',rows:sampleDemand()}},
    {...config,rules:{...defaultTaskRules,ramp:{...defaultTaskRules.ramp,duration:20}}},
    {...config,workers:workers.map((w,i)=>i===0?{...w,shift:{...w.shift,end:1100}}:w)}];
  for(const next of variations){
    workspace=switchScenario(workspace,next);
    assert.equal(currentSession(workspace).recoveryRequested,false);
    workspace=switchScenario(workspace,config);
    assert.equal(currentSession(workspace).recoveryRequested,true);
  }
  const rows=sampleDemand(),changed=rows.map((r,i)=>i===0?{...r,aircraft:r.aircraft+1}:r);
  assert.notEqual(scenarioKey({...config,upload:{name:'same.csv',rows}}),scenarioKey({...config,upload:{name:'same.csv',rows:changed}}));
});

test('reapplying an identical disruption retains recovery and approval; changed conditions invalidate both',()=>{
  let workspace=applyDisruption(createWorkspace(config));
  const {mission,original}=demoOperations.loadMission(config),schedule=candidate(workspace);
  const review={id:'demo-review',status:'approved',manager:'Demo reviewer',notes:'',timestamp:'2026-10-23T12:00:00Z',
    mission:{week:mission.week,level:mission.level,day:mission.day,seed:mission.seed,source:mission.source,sourceName:mission.sourceName},
    crisis:stackedCrisis,metrics:schedule.metrics,assignments:schedule.results.flatMap(r=>r.assignment?[r.assignment]:[]),
    snapshot:{modelVersion:'task-replay-v1',aircraft:mission.aircraft,workers:mission.workers,tasks:mission.tasks,originalMetrics:original.metrics}};
  workspace=patchSession(workspace,{recoveryRequested:true,review});
  workspace=patchSession(workspace,{draftCrisis:{...stackedCrisis,absentWorkerIds:[...stackedCrisis.absentWorkerIds].reverse()}});
  assert.equal(applyDisruption(workspace),workspace);
  assert.deepEqual(currentSession(workspace).review,review);
  for(const update of [{extraArrivals:5},{absentWorkerIds:['R-03']},{arrivalDelayMinutes:60},{delayedFlightCount:4}]){
    const changed=applyDisruption(patchSession(workspace,{draftCrisis:{...stackedCrisis,...update}}));
    assert.equal(currentSession(changed).recoveryRequested,false);
    assert.equal(currentSession(changed).review,null);
  }
  const other=switchScenario(workspace,{...config,level:'High'});
  assert.equal(currentSession(other).review,null);
  assert.deepEqual(currentSession(switchScenario(other,config)).review,review);
});
