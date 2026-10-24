import test from 'node:test';
import assert from 'node:assert/strict';
import {buildWeeklyStaffingPlan,TEAM_WAGES} from '../src/lib/weekly-planner.ts';
import {buildWeeklyReview} from '../src/lib/weekly-review.ts';

const plan=buildWeeklyStaffingPlan(42);

test('daily and shift coverage explain the same demand and totals as weekly metrics',()=>{
  for(const scenario of Object.values(plan.cases)){
    const review=buildWeeklyReview(scenario);
    assert.equal(review.slots.length,7*3*3);
    assert.equal(review.days.reduce((sum,day)=>sum+day.current,0),scenario.baseline.uncoveredSeatHours);
    assert.equal(review.days.reduce((sum,day)=>sum+day.proposed,0),scenario.recommended.uncoveredSeatHours);
    assert.equal(review.slots.reduce((sum,slot)=>sum+slot.requiredStaffHours,0),scenario.baseline.demandSeatHours);
    assert.equal(review.slots.reduce((sum,slot)=>sum+slot.currentCoveredStaffHours,0),scenario.baseline.coveredSeatHours);
    assert.equal(review.slots.reduce((sum,slot)=>sum+slot.proposedCoveredStaffHours,0),scenario.recommended.coveredSeatHours);
    assert.equal(review.slots.reduce((sum,slot)=>sum+slot.currentSeats,0),scenario.baseline.shifts);
    assert.equal(review.slots.reduce((sum,slot)=>sum+slot.proposedSeats,0),scenario.recommended.shifts);
    assert.equal(review.slots.reduce((sum,slot)=>sum+slot.currentCost,0),scenario.baseline.laborCost);
    assert.equal(review.slots.reduce((sum,slot)=>sum+slot.proposedCost,0),scenario.recommended.laborCost);
    assert.equal(new Set(review.slots.flatMap(slot=>slot.proposedAssignments.map(item=>item.workerId))).size,scenario.recommended.workers);
    assert.equal(new Set(review.slots.flatMap(slot=>slot.currentAssignments.map(item=>item.workerId))).size,scenario.baseline.workers);
    for(const slot of review.slots){
      assert.equal(slot.requiredStaffHours,slot.currentCoveredStaffHours+slot.currentShortStaffHours);
      assert.equal(slot.requiredStaffHours,slot.proposedCoveredStaffHours+slot.proposedShortStaffHours);
      assert.equal(slot.proposedAssignments.length,slot.proposedSeats);
      assert.equal(slot.proposedCost,slot.proposedAssignments.reduce((sum,item)=>sum+item.paidHours*TEAM_WAGES[item.team],0));
    }
  }
});

test('every proposed shift addition, removal, and dollar difference reconciles with the summary',()=>{
  for(const scenario of Object.values(plan.cases)){
    const review=buildWeeklyReview(scenario);
    assert.equal(review.netShifts,scenario.recommended.shifts-scenario.baseline.shifts);
    assert.equal(review.addedShifts-review.removedShifts,review.netShifts);
    assert.equal(review.incrementalCost,scenario.recommended.laborCost-scenario.baseline.laborCost);
    assert.equal(Object.values(review.roleShiftDeltas).reduce((sum,delta)=>sum+delta,0),review.netShifts);
    assert.equal(review.addedShifts,review.changes.reduce((sum,row)=>sum+Math.max(0,row.shiftDelta),0));
    assert.equal(review.removedShifts,review.changes.reduce((sum,row)=>sum+Math.max(0,-row.shiftDelta),0));
    assert.equal(review.changes.reduce((sum,row)=>sum+row.shiftDelta,0),review.netShifts);
    assert.equal(review.changes.reduce((sum,row)=>sum+row.costDelta,0),review.incrementalCost);
  }
});
