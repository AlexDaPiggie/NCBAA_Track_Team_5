/** Read-only explanation of the existing weekly roster calculation. */
import {SHIFT_BLOCKS,TEAM_NAMES,TEAM_WAGES,WEEK_DAYS,type ShiftKey,type WeeklyCase,type WeeklyShiftAssignment} from './weekly-planner.ts';
import type {Team} from './operations.ts';

const TEAMS=Object.keys(TEAM_NAMES) as Team[];
const round1=(value:number)=>Math.round(value*10)/10;
export type WeeklySlotReview={key:string;day:number;dayLabel:string;shift:ShiftKey;team:Team;requiredPeakSeats:number;currentSeats:number;proposedSeats:number;shiftDelta:number;requiredStaffHours:number;currentCoveredStaffHours:number;proposedCoveredStaffHours:number;currentShortStaffHours:number;proposedShortStaffHours:number;currentCost:number;proposedCost:number;costDelta:number;currentAssignments:WeeklyShiftAssignment[];proposedAssignments:WeeklyShiftAssignment[]};
export type WeeklyDayShortage={day:number;label:string;current:number;proposed:number};
export type WeeklyReview={slots:WeeklySlotReview[];changes:WeeklySlotReview[];days:WeeklyDayShortage[];roleShiftDeltas:Record<Team,number>;addedShifts:number;removedShifts:number;netShifts:number;incrementalCost:number};

export function buildWeeklyReview(scenario:WeeklyCase):WeeklyReview{
  const currentSlots=new Map(scenario.baseline.slots.map(slot=>[`${slot.day}-${slot.shift}-${slot.team}`,slot]));
  const proposedSlots=new Map(scenario.recommended.slots.map(slot=>[`${slot.day}-${slot.shift}-${slot.team}`,slot]));
  const slots:WeeklySlotReview[]=[];
  for(let day=0;day<WEEK_DAYS.length;day++)for(const shift of SHIFT_BLOCKS)for(const team of TEAMS){
    const key=`${day}-${shift.key}-${team}`,current=currentSlots.get(key),proposed=proposedSlots.get(key);
    if(!current||!proposed)throw new Error(`Missing evaluated staffing slot ${key}`);
    const currentSeats=scenario.baselineRoster.days[day].seats[team][shift.key].scheduled;
    const proposedSeats=scenario.recommendedRoster.days[day].seats[team][shift.key].scheduled;
    const currentAssignments=scenario.baselineRoster.assignments.filter(item=>item.day===day&&item.shift===shift.key&&item.team===team);
    const proposedAssignments=scenario.recommendedRoster.assignments.filter(item=>item.day===day&&item.shift===shift.key&&item.team===team);
    const currentCost=currentAssignments.reduce((sum,item)=>sum+item.paidHours*TEAM_WAGES[team],0);
    const proposedCost=proposedAssignments.reduce((sum,item)=>sum+item.paidHours*TEAM_WAGES[team],0);
    slots.push({key,day,dayLabel:WEEK_DAYS[day],shift:shift.key,team,requiredPeakSeats:scenario.recommendedRoster.days[day].seats[team][shift.key].required,
      currentSeats,proposedSeats,shiftDelta:proposedSeats-currentSeats,requiredStaffHours:current.demandSeatHours,
      currentCoveredStaffHours:current.coveredSeatHours,proposedCoveredStaffHours:proposed.coveredSeatHours,
      currentShortStaffHours:current.uncoveredSeatHours,proposedShortStaffHours:proposed.uncoveredSeatHours,
      currentCost,proposedCost,costDelta:proposedCost-currentCost,currentAssignments,proposedAssignments});
  }
  const changes=slots.filter(slot=>slot.shiftDelta!==0);
  const days=WEEK_DAYS.map((label,day)=>({day,label,current:round1(slots.filter(slot=>slot.day===day).reduce((sum,slot)=>sum+slot.currentShortStaffHours,0)),
    proposed:round1(slots.filter(slot=>slot.day===day).reduce((sum,slot)=>sum+slot.proposedShortStaffHours,0))}));
  const roleShiftDeltas={} as Record<Team,number>;
  for(const team of TEAMS)roleShiftDeltas[team]=changes.filter(slot=>slot.team===team).reduce((sum,slot)=>sum+slot.shiftDelta,0);
  const addedShifts=changes.reduce((sum,slot)=>sum+Math.max(0,slot.shiftDelta),0);
  const removedShifts=changes.reduce((sum,slot)=>sum+Math.max(0,-slot.shiftDelta),0);
  return {slots,changes,days,roleShiftDeltas,addedShifts,removedShifts,netShifts:addedShifts-removedShifts,
    incrementalCost:changes.reduce((sum,slot)=>sum+slot.costDelta,0)};
}
