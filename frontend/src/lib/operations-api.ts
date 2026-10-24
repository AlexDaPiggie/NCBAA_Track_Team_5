import {createMission,applyCrisis,scheduleTasks,evaluateOriginal,metricsFor,createProposedWorkers,noHires,noCrisis,type Mission,type Schedule,type Crisis,type Week,type DemandLevel,type UploadedCount,type TaskRules,type Worker,type Team,type HireCounts} from './operations.ts';

/** DTOs for a future task-level FastAPI adapter. Existing weekly API remains separate. */
export type MissionRequest = {week:Week;level:DemandLevel;day:number;seed:number;upload?:{name:string;rows:UploadedCount[]};rules?:TaskRules;workers?:Worker[]};
export type MissionResponse = {mission:Mission;original:Schedule;provenance:{kind:'synthetic'|'uploaded';independentlyValidated:false;algorithm:string}};
export type CrisisRequest = {mission:Mission;original:Schedule;crisis:Crisis};
export type CrisisResponse = {mission:Mission;originalUnderCrisis:Schedule};
export interface OperationsProvider {
  loadMission(input:MissionRequest):MissionResponse;
  simulateCrisis(input:CrisisRequest):CrisisResponse;
  recover(input:CrisisRequest):Schedule;
}
export interface OperationsHttpClient {
  loadMission(input:MissionRequest):Promise<MissionResponse>;
  simulateCrisis(input:CrisisRequest):Promise<CrisisResponse>;
  recover(input:CrisisRequest):Promise<Schedule>;
}
export const demoOperations:OperationsProvider = {
  loadMission(input){const mission=createMission(input.week,input.level,input.day,input.seed,input.upload,input.rules,input.workers);return {mission,original:scheduleTasks(mission),provenance:{kind:mission.source,independentlyValidated:false,algorithm:'Deterministic earliest-deadline greedy assignment'}};},
  simulateCrisis(input){const mission=applyCrisis(input.mission,input.crisis);return {mission,originalUnderCrisis:evaluateOriginal(mission,input.original,input.crisis)};},
  recover(input){const mission=applyCrisis(input.mission,input.crisis);const fixed=evaluateOriginal(mission,input.original,input.crisis);fixed.metrics=metricsFor(fixed.results,mission.workers.filter(worker=>!worker.proposed));return scheduleTasks(mission,input.crisis,fixed);},
};
export function recommendRecoveryHeadcount(mission:Mission,original:Schedule,crisis:Crisis):{counts:HireCounts;fullyCovered:Record<Team,boolean>}{
  const counts={...noHires},fullyCovered={} as Record<Team,boolean>,affected=applyCrisis(mission,crisis);
  for(const team of ['ramp','fuel','service'] as Team[]){
    let bestCovered=-1,bestCount=0,taskCount=affected.tasks.filter(task=>task.team===team).length;
    fullyCovered[team]=taskCount===0;
    for(let count=0;count<=20&&!fullyCovered[team];count++){
      const added=createProposedWorkers(mission,{...noHires,[team]:count});
      const candidateMission={...mission,workers:[...mission.workers,...added]};
      const candidate=demoOperations.recover({mission:candidateMission,original,crisis});
      const roleResults=candidate.results.filter(result=>result.task.team===team);
      const covered=roleResults.filter(result=>result.assignment).length;
      if(covered>bestCovered){bestCovered=covered;bestCount=count;}
      if(covered===taskCount){counts[team]=count;fullyCovered[team]=true;}
    }
    if(!fullyCovered[team])counts[team]=bestCount;
  }
  return {counts,fullyCovered};
}
export {noCrisis};
