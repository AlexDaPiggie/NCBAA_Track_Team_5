/** Fixed-seed, synthetic seven-day staffing comparison for the browser demo. */
import {createMission,defaultTaskRules,type DemandLevel,type Team,type Week} from './operations.ts';

export const WEEK_DAYS=['Mon 08','Tue 09','Wed 10','Thu 11','Fri 12','Sat 13','Sun 14'] as const;
export const SHIFT_BLOCKS=[
  {key:'00-08',label:'00–08',start:0,end:8},
  {key:'08-16',label:'08–16',start:8,end:16},
  {key:'16-24',label:'16–24',start:16,end:24},
] as const;
export type ShiftKey=typeof SHIFT_BLOCKS[number]['key'];
export const TEAM_NAMES:Record<Team,string>={ramp:'Ramp',fuel:'Fuel',service:'Customer service'};
export const TEAM_WAGES:Record<Team,number>={ramp:32,fuel:35,service:26};
const MINIMUMS:Record<Team,number>={ramp:2,fuel:1,service:1};
const UTILIZATION=.8,SHIFT_HOURS=8,MAX_WEEKLY_HOURS=40,MIN_REST_HOURS=8,BREAK_HOURS=.5,WORKER_POOL_SIZE=50;
const TEAMS:Team[]=['ramp','fuel','service'];
const round1=(n:number)=>Math.round(n*10)/10;

type HourlyNeeds=Record<Team,number[]>;
export type WeeklySeatRow={required:number;scheduled:number;unfilled:number};
export type WeeklyDayPlan={day:number;label:string;aircraft:number;seats:Record<Team,Record<ShiftKey,WeeklySeatRow>>};
export type WeeklyShiftAssignment={workerId:string;team:Team;day:number;shift:ShiftKey;start:number;end:number;breakStart:number;breakEnd:number;paidHours:number};
export type WeeklyRoster={days:WeeklyDayPlan[];assignments:WeeklyShiftAssignment[];workers:number;shifts:number;paidHours:number;laborCost:number;unfilledShifts:number};
export type WeeklySlotMetrics={day:number;shift:ShiftKey;team:Team;demandSeatHours:number;coveredSeatHours:number;uncoveredSeatHours:number};
export type WeeklyMetrics={aircraft:number;demandSeatHours:number;coveredSeatHours:number;uncoveredSeatHours:number;coveragePercent:number;peakUncoveredSeats:number;workers:number;shifts:number;paidHours:number;laborCost:number;unfilledShifts:number;slots:WeeklySlotMetrics[];teams:Record<Team,{demandSeatHours:number;coveredSeatHours:number;uncoveredSeatHours:number;coveragePercent:number;peakUncoveredSeats:number;workers:number;shifts:number;paidHours:number;laborCost:number;unfilledShifts:number}>};
export type WeeklyCase={level:DemandLevel;demand:WeeklyMetrics;demandAircraftByDay:number[];baseline:WeeklyMetrics;recommended:WeeklyMetrics;baselineRoster:WeeklyRoster;recommendedRoster:WeeklyRoster};
export type WeeklyStaffingPlan={ordinary:WeeklyMetrics;ordinaryRoster:WeeklyRoster;cases:Record<DemandLevel,WeeklyCase>;assumptions:{seed:number;source:string;window:string;serviceRules:typeof defaultTaskRules;minimumSeats:Record<Team,number>;utilization:number;shiftHours:number;maxWeeklyHours:number;minimumRestHours:number;breakMinutes:number;wages:Record<Team,number>;planningRule:string;costRule:string}};

function emptyNeeds():HourlyNeeds{return {ramp:Array(168).fill(0),fuel:Array(168).fill(0),service:Array(168).fill(0)};}

function createNeeds(week:Week,level:DemandLevel,seed:number){
  const needs=emptyNeeds(),aircraftByDay:number[]=[];
  for(let day=0;day<7;day++){
    const mission=createMission(week,level,day,seed);
    aircraftByDay.push(mission.aircraft.length);
    for(const task of mission.tasks){
      const localHour=Math.min(23,Math.max(0,Math.floor(task.earliest/60)));
      needs[task.team][day*24+localHour]+=task.duration*task.crewRequired/60;
    }
  }
  const required:HourlyNeeds=emptyNeeds();
  for(const team of TEAMS)for(let hour=0;hour<168;hour++){
    const workload=needs[team][hour];
    required[team][hour]=workload>0?Math.max(MINIMUMS[team],Math.ceil(workload/UTILIZATION)):0;
  }
  return {required,aircraftByDay};
}

function makeRoster(demand:ReturnType<typeof createNeeds>,prefix:string):WeeklyRoster{
  const assignments:WeeklyShiftAssignment[]=[],days:WeeklyDayPlan[]=[],workersByTeam:Record<Team,{id:string;hours:number;lastEnd:number;days:Set<number>}[]>={ramp:[],fuel:[],service:[]};
  let unfilledShifts=0;
  for(let day=0;day<7;day++){
    const seatsByTeam={} as WeeklyDayPlan['seats'];
    for(const team of TEAMS){
      seatsByTeam[team]={} as Record<ShiftKey,WeeklySeatRow>;
      for(const shift of SHIFT_BLOCKS){
        const absoluteStart=day*24+shift.start,absoluteEnd=day*24+shift.end;
        const hourly=demand.required[team].slice(day*24+shift.start,day*24+shift.end);
        const target=Math.max(0,...hourly);
        const workers=workersByTeam[team];
        let scheduled=0;
        for(let seat=0;seat<target;seat++){
          const eligible=workers.filter(worker=>worker.hours+SHIFT_HOURS<=MAX_WEEKLY_HOURS
            &&absoluteStart-worker.lastEnd>=MIN_REST_HOURS&&!worker.days.has(day))
            .sort((a,b)=>a.hours-b.hours||a.id.localeCompare(b.id));
          let worker=eligible[0];
          if(!worker){
            if(workers.length>=WORKER_POOL_SIZE){unfilledShifts++;continue;}
            worker={id:`${prefix}-${team.toUpperCase()}-${String(workers.length+1).padStart(3,'0')}`,hours:0,lastEnd:-MIN_REST_HOURS,days:new Set<number>()};
            workers.push(worker);
          }
          worker.hours+=SHIFT_HOURS;worker.lastEnd=absoluteEnd;worker.days.add(day);scheduled++;
          const breakStart=absoluteStart+3.5+(seat%4)*.5;
          assignments.push({workerId:worker.id,team,day,shift:shift.key,start:absoluteStart,end:absoluteEnd,
            breakStart,breakEnd:breakStart+BREAK_HOURS,paidHours:SHIFT_HOURS});
        }
        seatsByTeam[team][shift.key]={required:target,scheduled,unfilled:target-scheduled};
      }
    }
    days.push({day,label:WEEK_DAYS[day],aircraft:demand.aircraftByDay[day],seats:seatsByTeam});
  }
  const paidHours=assignments.reduce((sum,item)=>sum+item.paidHours,0);
  const laborCost=assignments.reduce((sum,item)=>sum+item.paidHours*TEAM_WAGES[item.team],0);
  return {days,assignments,workers:TEAMS.reduce((sum,team)=>sum+workersByTeam[team].length,0),
    shifts:assignments.length,paidHours,laborCost:round1(laborCost),unfilledShifts};
}

function evaluate(demand:ReturnType<typeof createNeeds>,roster:WeeklyRoster):WeeklyMetrics{
  const teams={} as WeeklyMetrics['teams'],slots:WeeklySlotMetrics[]=[];
  for(const team of TEAMS){
    let demandSeatHours=0,coveredSeatHours=0,uncoveredSeatHours=0,peakUncoveredSeats=0,shifts=0,paidHours=0,workers=new Set<string>(),unfilledShifts=0;
    const teamSlots:WeeklySlotMetrics[]=Array.from({length:7},(_,day)=>SHIFT_BLOCKS.map(shift=>({day,shift:shift.key,team,demandSeatHours:0,coveredSeatHours:0,uncoveredSeatHours:0}))).flat();
    for(let index=0;index<168;index++){
      const day=Math.floor(index/24),hour=index%24;
      const assignments=roster.assignments.filter(item=>item.team===team&&item.day===day&&item.start<=index&&item.end>index);
      const breakLoss=assignments.reduce((sum,item)=>sum+Math.max(0,Math.min(hour+1,item.breakEnd%24)-Math.max(hour,item.breakStart%24)),0);
      const available=Math.max(0,assignments.length-breakLoss),required=demand.required[team][index],gap=Math.max(0,required-available);
      const covered=Math.min(required,available),slot=teamSlots[day*SHIFT_BLOCKS.length+Math.floor(hour/8)];
      demandSeatHours+=required;coveredSeatHours+=covered;uncoveredSeatHours+=gap;peakUncoveredSeats=Math.max(peakUncoveredSeats,Math.ceil(gap));
      slot.demandSeatHours+=required;slot.coveredSeatHours+=covered;slot.uncoveredSeatHours+=gap;
    }
    slots.push(...teamSlots.map(slot=>({...slot,demandSeatHours:round1(slot.demandSeatHours),coveredSeatHours:round1(slot.coveredSeatHours),uncoveredSeatHours:round1(slot.uncoveredSeatHours)})));
    for(const item of roster.assignments.filter(item=>item.team===team)){shifts++;paidHours+=item.paidHours;workers.add(item.workerId);}
    for(const row of roster.days)for(const item of Object.values(row.seats[team]))unfilledShifts+=item.unfilled;
    const laborCost=paidHours*TEAM_WAGES[team];
    teams[team]={demandSeatHours:round1(demandSeatHours),coveredSeatHours:round1(coveredSeatHours),uncoveredSeatHours:round1(uncoveredSeatHours),
      coveragePercent:demandSeatHours?round1(100*coveredSeatHours/demandSeatHours):100,peakUncoveredSeats,workers:workers.size,shifts,paidHours,laborCost:round1(laborCost),unfilledShifts};
  }
  const demandSeatHours=TEAMS.reduce((sum,team)=>sum+teams[team].demandSeatHours,0),coveredSeatHours=TEAMS.reduce((sum,team)=>sum+teams[team].coveredSeatHours,0),uncoveredSeatHours=TEAMS.reduce((sum,team)=>sum+teams[team].uncoveredSeatHours,0);
  return {aircraft:demand.aircraftByDay.reduce((sum,count)=>sum+count,0),demandSeatHours:round1(demandSeatHours),coveredSeatHours:round1(coveredSeatHours),uncoveredSeatHours:round1(uncoveredSeatHours),
    coveragePercent:demandSeatHours?round1(100*coveredSeatHours/demandSeatHours):100,peakUncoveredSeats:Math.max(...TEAMS.map(team=>teams[team].peakUncoveredSeats)),
    workers:TEAMS.reduce((sum,team)=>sum+teams[team].workers,0),shifts:TEAMS.reduce((sum,team)=>sum+teams[team].shifts,0),paidHours:TEAMS.reduce((sum,team)=>sum+teams[team].paidHours,0),
    laborCost:round1(TEAMS.reduce((sum,team)=>sum+teams[team].laborCost,0)),unfilledShifts:TEAMS.reduce((sum,team)=>sum+teams[team].unfilledShifts,0),slots,teams};
}

export function buildWeeklyStaffingPlan(seed=42):WeeklyStaffingPlan{
  const ordinaryDemand=createNeeds('normal','Medium',seed),ordinaryRoster=makeRoster(ordinaryDemand,'BASE');
  const ordinary=evaluate(ordinaryDemand,ordinaryRoster);
  const cases={} as Record<DemandLevel,WeeklyCase>;
  for(const level of ['Low','Medium','High'] as const){
    const eventDemand=createNeeds('event',level,seed),recommendedRoster=makeRoster(eventDemand,`EVENT-${level.toUpperCase()}`);
    const baseline=evaluate(eventDemand,ordinaryRoster),recommended=evaluate(eventDemand,recommendedRoster);
    cases[level]={level,demand:evaluate(eventDemand,recommendedRoster),demandAircraftByDay:eventDemand.aircraftByDay,baseline,recommended,baselineRoster:ordinaryRoster,recommendedRoster};
  }
  return {ordinary,ordinaryRoster,cases,assumptions:{seed,source:'Fixed-seed synthetic arrivals, task requests, and fictional workers.',window:'February 8–14, 2027, local demo week.',serviceRules:defaultTaskRules,
    minimumSeats:MINIMUMS,utilization:UTILIZATION,shiftHours:SHIFT_HOURS,maxWeeklyHours:MAX_WEEKLY_HOURS,minimumRestHours:MIN_REST_HOURS,breakMinutes:BREAK_HOURS*60,wages:TEAM_WAGES,
    planningRule:'For each day and 8-hour shift, staff to the peak hourly workload requirement. Assign one qualified synthetic worker to one shift per day; enforce 40 weekly hours and 8 hours between shifts.',
    costRule:'Scheduled paid shift hours × illustrative hourly rate. Breaks are assumed paid; premiums and benefits are excluded.'}};
}
