import test from 'node:test';
import assert from 'node:assert/strict';
import {buildWeeklyStaffingPlan,SHIFT_BLOCKS,TEAM_WAGES} from '../src/lib/weekly-planner.ts';

const plan=buildWeeklyStaffingPlan(42);

test('weekly plan is deterministic and covers ordinary plus all three event cases',()=>{
  assert.deepEqual(plan,buildWeeklyStaffingPlan(42));
  assert.equal(plan.ordinaryRoster.days.length,7);
  assert.deepEqual(Object.keys(plan.cases),['Low','Medium','High']);
  assert.ok(plan.ordinary.aircraft>0);
  assert.ok(plan.cases.Low.demand.aircraft<=plan.cases.Medium.demand.aircraft);
  assert.ok(plan.cases.Medium.demand.aircraft<=plan.cases.High.demand.aircraft);
});

test('ordinary and recommended rosters face the same demand inside each event case',()=>{
  for(const level of ['Low','Medium','High']){
    const scenario=plan.cases[level];
    assert.equal(scenario.baseline.aircraft,scenario.demand.aircraft);
    assert.equal(scenario.recommended.aircraft,scenario.demand.aircraft);
    assert.equal(scenario.baseline.demandSeatHours,scenario.recommended.demandSeatHours);
    assert.equal(scenario.baseline.coveragePercent,scenario.baseline.demandSeatHours?Math.round(1000*scenario.baseline.coveredSeatHours/scenario.baseline.demandSeatHours)/10:100);
  }
});

test('synthetic workers keep one team, one shift per day, weekly limits, and rest gaps',()=>{
  const all=[...plan.ordinaryRoster.assignments,...plan.cases.High.recommendedRoster.assignments];
  for(const roster of [plan.ordinaryRoster,plan.cases.Low.recommendedRoster,plan.cases.Medium.recommendedRoster,plan.cases.High.recommendedRoster]){
    const workers=new Map();
    for(const shift of roster.assignments){
      const previous=workers.get(shift.workerId)??[];
      previous.push(shift);workers.set(shift.workerId,previous);
      assert.ok(shift.end-shift.start===8);
      assert.ok(shift.breakEnd-shift.breakStart===.5);
    }
    for(const shifts of workers.values()){
      shifts.sort((a,b)=>a.start-b.start);
      assert.ok(shifts.reduce((sum,shift)=>sum+shift.paidHours,0)<=40);
      assert.equal(new Set(shifts.map(shift=>shift.day)).size,shifts.length);
      assert.ok(shifts.every((shift,index)=>index===0||shift.start-shifts[index-1].end>=8));
      assert.equal(new Set(shifts.map(shift=>shift.team)).size,1);
    }
  }
  assert.ok(all.length>0);
  assert.deepEqual(SHIFT_BLOCKS.map(shift=>shift.key),['00-08','08-16','16-24']);
});

test('labor cost equals scheduled paid hours at the configured illustrative rates',()=>{
  for(const roster of [plan.ordinaryRoster,...Object.values(plan.cases).map(item=>item.recommendedRoster)]){
    const expected=roster.assignments.reduce((sum,shift)=>sum+shift.paidHours*TEAM_WAGES[shift.team],0);
    assert.equal(roster.paidHours,roster.assignments.reduce((sum,shift)=>sum+shift.paidHours,0));
    assert.equal(roster.laborCost,expected);
  }
});

test('daily roster rows retain scheduled, required, and unfilled seats per team and shift',()=>{
  for(const roster of [plan.ordinaryRoster,plan.cases.High.recommendedRoster]){
    assert.equal(roster.days.length,7);
    for(const day of roster.days)for(const team of ['ramp','fuel','service'])for(const shift of SHIFT_BLOCKS){
      const row=day.seats[team][shift.key];
      assert.equal(row.scheduled+row.unfilled,row.required);
      assert.ok(row.scheduled>=0&&row.unfilled>=0);
    }
  }
});
