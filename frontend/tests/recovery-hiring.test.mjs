import test from 'node:test';
import assert from 'node:assert/strict';
import {demoOperations,recommendRecoveryHeadcount} from '../src/lib/operations-api.ts';
import {createProposedWorkers,estimatedHireShiftCost,noCrisis,stackedCrisis} from '../src/lib/operations.ts';

const {mission,original}=demoOperations.loadMission({week:'event',level:'Medium',day:5,seed:42});

test('proposed workers add exactly the modeled shift cost and do not change original cost',()=>{
  const added=createProposedWorkers(mission,{ramp:2,fuel:1,service:1});
  assert.equal(added.length,4);
  assert.equal(new Set(added.map(worker=>worker.id)).size,4);
  assert.ok(added.every(worker=>worker.proposed));
  const cost=added.reduce((sum,worker)=>sum+worker.hourlyRate*9,0);
  assert.equal(estimatedHireShiftCost(added),cost);
  const baseline=demoOperations.recover({mission,original,crisis:stackedCrisis});
  const candidate=demoOperations.recover({mission:{...mission,workers:[...mission.workers,...added]},original,crisis:stackedCrisis});
  assert.equal(candidate.metrics.laborCost-baseline.metrics.laborCost,cost);
  assert.equal(demoOperations.simulateCrisis({mission,original,crisis:stackedCrisis}).originalUnderCrisis.metrics.laborCost,baseline.metrics.laborCost);
});

test('recommended headcounts reproduce reported role coverage',()=>{
  const {counts,fullyCovered}=recommendRecoveryHeadcount(mission,original,noCrisis);
  const added=createProposedWorkers(mission,counts);
  const candidate=demoOperations.recover({mission:{...mission,workers:[...mission.workers,...added]},original,crisis:noCrisis});
  for(const team of ['ramp','fuel','service']){
    assert.ok(counts[team]>=0&&counts[team]<=20);
    const role=candidate.results.filter(result=>result.task.team===team);
    if(fullyCovered[team])assert.ok(role.every(result=>result.assignment),`${team} marked covered`);
  }
});
