import type {TaskResult,Team} from './operations';

export type TaskTimelineItem={result:TaskResult;start:number;end:number;layoutEnd:number};
export type TaskTimelineGroup={team:Team;label:string;count:number;uncovered:number;lanes:TaskTimelineItem[][]};

/** Visual lanes separate overlapping jobs. They do not imply a crew assignment. */
export function groupTaskTimeline(results:TaskResult[],windowStart:number,windowEnd:number):TaskTimelineGroup[]{
  return (['ramp','fuel','service'] as Team[]).flatMap(team=>{
    const tasks=results.filter(result=>result.task.team===team);
    if(!tasks.length)return [];
    const items=tasks.map(result=>{
      // Uncovered bars show requested work, rather than pretending an assignment exists.
      const start=result.assignment?.start??result.task.earliest;
      const end=result.assignment?.end??start+result.task.duration;
      return {result,start:Math.max(windowStart,start),end:Math.min(windowEnd,end),layoutEnd:Math.max(end,start+36)+3};
    }).filter(item=>item.end>item.start).sort((a,b)=>a.start-b.start||a.end-b.end||a.result.task.id.localeCompare(b.result.task.id));
    const lanes:TaskTimelineItem[][]=[];
    for(const item of items){
      const lane=lanes.find(lane=>lane[lane.length-1].layoutEnd<=item.start);
      if(lane)lane.push(item);else lanes.push([item]);
    }
    return [{team,label:tasks[0].task.label,count:tasks.length,uncovered:tasks.filter(t=>!t.assignment).length,lanes}];
  });
}
