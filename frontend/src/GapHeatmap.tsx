import {useMemo,useState} from 'react';
import type {Result} from './plannerTypes';

const zones=['All current departments','Passenger Services','Ramp Operations','Fuel Services'];
export default function GapHeatmap({result,staffing}:{result:Result;staffing:Record<string,number>}){
 const [zone,setZone]=useState(zones[0]);
 const departments=zone===zones[0]?zones.slice(1):[zone];
 const cells=useMemo(()=>Array.from({length:42},(_,block)=>{
  const rows=result.four_hour_requirements.filter(row=>row.block===block&&departments.includes(row.department));
  const gap=rows.reduce((sum,row)=>sum+Math.max(0,row.required-(staffing[row.department]??0)),0);
  return {block,day:Math.floor(block/6)+1,slot:block%6,gap,need:rows.reduce((sum,row)=>sum+row.required,0)};
 }),[result,staffing,zone]);
 return <section className="panel"><div className="section-title"><div><h2>Four-hour staffing gap estimate</h2><p>42 blocks · current model has three departments, not the requested seven zones and role qualifications.</p></div><label>Show<select value={zone} onChange={event=>setZone(event.target.value)}>{zones.map(item=><option key={item}>{item}</option>)}</select></label></div>
  <div className="table-wrap"><table className="gap-grid"><thead><tr><th>Day</th>{Array.from({length:6},(_,slot)=><th key={slot}>{String(slot*4).padStart(2,'0')}:00–{String(slot*4+4).padStart(2,'0')}:00</th>)}</tr></thead><tbody>{Array.from({length:7},(_,day)=><tr key={day}><th>Day {day+1}</th>{cells.filter(cell=>cell.day===day+1).map(cell=><td key={cell.block} className={cell.gap===0?'gap-ok':cell.gap<=2?'gap-low':'gap-high'} title={`${cell.need} required positions; ${cell.gap} short against selected coverage counts`}><strong>{cell.gap===0?'Covered':`−${cell.gap}`}</strong><small>{cell.need} required</small></td>)}</tr>)}</tbody></table></div>
  <p className="caption">Gap = the sum of positive required-minus-selected-department-counts within this block. It does not account for scheduled workers, cross-zone qualifications, breaks, or sub-block peaks.</p>
 </section>
}
