import {createMission,applyCrisis,scheduleTasks,evaluateOriginal,noCrisis,type Mission,type Schedule,type Crisis,type Week,type DemandLevel,type UploadedCount,type TaskRules,type Worker} from './operations';

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
  recover(input){const mission=applyCrisis(input.mission,input.crisis);const fixed=evaluateOriginal(mission,input.original,input.crisis);return scheduleTasks(mission,input.crisis,fixed);},
};
export {noCrisis};
