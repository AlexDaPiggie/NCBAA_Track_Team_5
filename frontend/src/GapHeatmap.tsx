import {useState} from 'react';
import type {Result} from './plannerTypes';
import './gap-heatmap.css';

const departments=['Passenger Services','Ramp Operations','Fuel Services'];
type Requirement=Result['requirements'][number];
type Breakdown={department:string;required:number;staff:number;gap:number};
type Block={day:number;start:number;hour:number;activity:number;gap:number;ready:boolean;breakdown:Breakdown[]};

function makeBlocks(result:Result,staffing:Record<string,number>,filter:string):Block[]{
 const byHour=new Map<string,Requirement>(result.requirements.map(row=>[`${row.hour}:${row.department}`,row]));
 const chosen=filter==='All departments'?departments:[filter];
 return Array.from({length:42},(_,index)=>{
  const start=index*4,day=Math.floor(start/24);
  const activity=result.forecast.slice(start,start+4).reduce((sum,row)=>sum+row.aircraft,0);
  let best:Block|null=null;
  for(let hour=start;hour<start+4;hour++){
   const rows=chosen.map(department=>{
    const requirement=byHour.get(`${hour}:${department}`);
    const staff=staffing[department]??0;
    return {department,required:requirement?.required??0,staff,gap:Math.max(0,(requirement?.required??0)-staff)};
   });
   const ready=chosen.every(department=>byHour.has(`${hour}:${department}`));
   const gap=rows.reduce((sum,row)=>sum+row.gap,0);
   const candidate={day,start,hour,activity,gap,ready,breakdown:rows};
   if(!best||(ready&&(!best.ready||gap>best.gap||(gap===best.gap&&rows.reduce((sum,row)=>sum+row.required,0)>best.breakdown.reduce((sum,row)=>sum+row.required,0)))))best=candidate;
  }
  return best!;
 });
}

const time=(hour:number)=>`${String(hour).padStart(2,'0')}:00`;

export default function GapHeatmap({result,staffing,onOpenRoster}:{result:Result;staffing:Record<string,number>;onOpenRoster:()=>void}){
 const [filter,setFilter]=useState('All departments');
 const [selected,setSelected]=useState(0);
 const blocks=makeBlocks(result,staffing,filter);
 const detail=blocks[selected];
 return <section className="panel gap-panel" aria-labelledby="gap-title">
  <div className="section-title"><div><h2 id="gap-title">Staffing gap heatmap</h2><p>Find the busiest uncovered hour in each four-hour block. Select a cell to inspect it.</p></div><label>Department<select value={filter} onChange={event=>{setFilter(event.target.value);setSelected(0)}}><option>All departments</option>{departments.map(name=><option key={name}>{name}</option>)}</select></label></div>
  <div className="gap-legend" aria-label="Gap colors"><span><i className="gap-key covered"/>Covered</span><span><i className="gap-key short"/>Short 1–2</span><span><i className="gap-key critical"/>Short 3+</span></div>
  <div className="gap-scroll"><div className="gap-grid" role="group" aria-label="Seven days by six four-hour blocks"><div className="gap-axis">Time</div>{Array.from({length:7},(_,day)=><div className="gap-axis" key={day}>Day {day+1}</div>)}{Array.from({length:6},(_,block)=><div className="gap-row" key={block}><div className="gap-time">{time(block*4)}–{time((block+1)*4)}</div>{Array.from({length:7},(_,day)=>{const index=day*6+block,cell=blocks[index];const level=!cell.ready?'unavailable':cell.gap===0?'covered':cell.gap<3?'short':'critical';return <button type="button" key={day} className={`gap-cell ${level}`} aria-pressed={selected===index} aria-label={`Day ${day+1}, ${time(block*4)} to ${time((block+1)*4)}, ${!cell.ready?'no estimate':cell.gap===0?'covered':`short ${cell.gap} staff positions`}`} onClick={()=>setSelected(index)}><strong>{!cell.ready?'—':cell.gap===0?'Covered':`+${cell.gap}`}</strong><small>{!cell.ready?'No data':cell.gap===0?'No gap':'short'}</small></button>})}</div>)}</div></div>
  <div className="gap-detail" aria-live="polite"><div><h3>Day {detail.day+1} · {time(detail.start%24)}–{time(detail.start%24+4)}</h3><p>{detail.ready?`Largest shortfall at ${time(detail.hour%24)}. Estimated aircraft activity during this four-hour block: ${Math.round(detail.activity)}.`:'This block does not have a complete hourly staffing estimate.'}</p></div>{detail.ready&&<div className="table-wrap"><table><thead><tr><th>Department</th><th>Estimated need</th><th>Plan positions</th><th>Short</th></tr></thead><tbody>{detail.breakdown.map(row=><tr key={row.department}><td>{row.department}</td><td>{row.required}</td><td>{row.staff}</td><td>{row.gap}</td></tr>)}</tbody></table></div>}</div>
  <p className="caption">Preview from hourly estimates and fixed staff positions, not an employee shift roster. A department's spare position cannot automatically cover another department. Aircraft activity may use synthetic data or a scaled 2013 JFK airline-departure pattern; neither is observed FBO demand. No uncertainty band or qualified-worker recommendation is available here yet.</p>
  <button type="button" onClick={onOpenRoster}>Build &amp; test a shift roster →</button>
 </section>;
}
