import type {MissionRequest} from './operations-api.ts';
import {noCrisis,noHires,stackedCrisis,type Crisis,type HireCounts,type ReviewRecord} from './operations.ts';

export type RecoverySession = {
  draftCrisis:Crisis;
  applied:Crisis;
  recoveryRequested:boolean;
  hireCounts:HireCounts;
  recommendedHeadcounts:HireCounts|null;
  fullyCoveredRoles:Record<'ramp'|'fuel'|'service',boolean>|null;
  manager:string;
  notes:string;
  review:ReviewRecord|null;
};
export type RecoveryWorkspace = {config:MissionRequest;sessions:Record<string,RecoverySession>};

// Include all inputs, including CSV contents, service rules and worker availability.
function canonical(value:unknown):unknown {
  if(Array.isArray(value))return value.map(canonical);
  if(value&&typeof value==='object')return Object.fromEntries(Object.entries(value).filter(([,v])=>v!==undefined).sort(([a],[b])=>a.localeCompare(b)).map(([k,v])=>[k,canonical(v)]));
  return value;
}
export function scenarioKey(config:MissionRequest){return JSON.stringify(canonical(config));}
function newSession():RecoverySession {
  return {draftCrisis:structuredClone(stackedCrisis),applied:structuredClone(noCrisis),recoveryRequested:false,hireCounts:{...noHires},recommendedHeadcounts:null,fullyCoveredRoles:null,manager:'',notes:'',review:null};
}
export function createWorkspace(config:MissionRequest):RecoveryWorkspace {
  return {config,sessions:{[scenarioKey(config)]:newSession()}};
}
export function currentSession(workspace:RecoveryWorkspace){return workspace.sessions[scenarioKey(workspace.config)];}
export function patchSession(workspace:RecoveryWorkspace,update:Partial<RecoverySession>):RecoveryWorkspace {
  const key=scenarioKey(workspace.config);
  return {...workspace,sessions:{...workspace.sessions,[key]:{...workspace.sessions[key],...update}}};
}
export function switchScenario(workspace:RecoveryWorkspace,config:MissionRequest):RecoveryWorkspace {
  const key=scenarioKey(config);
  if(key===scenarioKey(workspace.config))return workspace;
  return {config,sessions:workspace.sessions[key]?workspace.sessions:{...workspace.sessions,[key]:newSession()}};
}
export function applyDisruption(workspace:RecoveryWorkspace):RecoveryWorkspace {
  const session=currentSession(workspace);
  const key=(crisis:Crisis)=>JSON.stringify(canonical({...crisis,absentWorkerIds:[...crisis.absentWorkerIds].sort()}));
  if(key(session.applied)===key(session.draftCrisis))return workspace;
  return patchSession(workspace,{applied:structuredClone(session.draftCrisis),recoveryRequested:false,recommendedHeadcounts:null,fullyCoveredRoles:null,review:null});
}
