import test from 'node:test';
import assert from 'node:assert/strict';
import {createMission,scheduleTasks,applyCrisis,evaluateOriginal,stackedCrisis,START,END} from '../src/lib/operations.ts';
import {groupTaskTimeline} from '../src/lib/task-timeline.ts';

test('each task appears once even when its assignment needs two workers',()=>{
  const mission=createMission(),schedule=scheduleTasks(mission);
  const groups=groupTaskTimeline(schedule.results,START,END);
  const items=groups.flatMap(group=>group.lanes.flat());
  assert.equal(items.length,schedule.results.length);
  assert.equal(new Set(items.map(item=>item.result.task.id)).size,items.length);
  const twoCrew=schedule.results.find(r=>r.assignment?.workerIds.length===2);
  assert.equal(items.filter(item=>item.result.task.id===twoCrew.task.id).length,1);
  assert.deepEqual(groups.map(group=>group.team),['ramp','fuel','service']);
});
test('overlapping services are placed in separate display lanes',()=>{
  const mission=createMission(),schedule=scheduleTasks(mission);
  for(const group of groupTaskTimeline(schedule.results,START,END)){
    for(const lane of group.lanes)for(let i=1;i<lane.length;i++)assert.ok(lane[i-1].layoutEnd<=lane[i].start);
    assert.equal(group.count,group.lanes.flat().length);
  }
});
test('uncovered tasks show requested work and retain conflict reasons and crew requirements',()=>{
  const mission=createMission(),original=scheduleTasks(mission),affected=applyCrisis(mission,stackedCrisis);
  const fixed=evaluateOriginal(affected,original,stackedCrisis);
  const uncovered=fixed.results.filter(r=>!r.assignment);
  const groups=groupTaskTimeline(uncovered,START,END),items=groups.flatMap(group=>group.lanes.flat());
  assert.equal(groups.reduce((n,g)=>n+g.uncovered,0),uncovered.length);
  for(const item of items){
    assert.equal(item.result.assignment,null);
    assert.equal(item.start,Math.max(START,item.result.task.earliest));
    assert.ok(item.result.reason);assert.ok(item.result.task.crewRequired>0);
  }
});
