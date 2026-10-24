import type {DemandHour} from './planner-api';

const columns=['hour','aircraft','passengers','fuel_requests'] as const;

// Parse quoted fields as well as simple spreadsheet exports. Never execute cell contents.
function rowsFromCSV(text:string):string[][] {
  const rows:string[][]=[];let row:string[]=[],cell='',quoted=false,afterQuote=false;
  for(let i=0;i<text.length;i++){
    const c=text[i];
    if(c==='"'){
      if(quoted&&text[i+1]==='"'){cell+='"';i++;}
      else if(quoted){quoted=false;afterQuote=true;}
      else if(cell.trim()||afterQuote){throw new Error('A quote appears inside an unquoted field.');}
      else quoted=true;
    }else if(c===','&&!quoted){row.push(cell.trim());cell='';afterQuote=false;}
    else if((c==='\n'||c==='\r')&&!quoted){
      if(c==='\r'&&text[i+1]==='\n')i++;
      row.push(cell.trim());if(row.some(Boolean))rows.push(row);row=[];cell='';afterQuote=false;
    }else if(afterQuote&&!/\s/.test(c)){throw new Error('Unexpected text after a closing quote.');}
    else if(!afterQuote)cell+=c;
  }
  if(quoted)throw new Error('A quoted field is missing its closing quote.');
  row.push(cell.trim());if(row.some(Boolean))rows.push(row);
  return rows;
}
export function parseDemandCSV(text:string):DemandHour[] {
  if(text.length>100_000)throw new Error('Use a CSV smaller than 100 KB. Only 168 hourly rows are needed.');
  const [headers,...rows]=rowsFromCSV(text.replace(/^\uFEFF/,''));
  if(!headers||headers.length!==4||new Set(headers).size!==4||columns.some(c=>!headers.includes(c)))
    throw new Error('Use exactly these four headers: hour, aircraft, passengers, fuel_requests. Download the sample for the format.');
  if(rows.length!==168)throw new Error(`Found ${rows.length} hourly rows. Need exactly 168: one row for each hour from 0 to 167.`);
  const result=rows.map((row,index)=>{
    if(row.length!==4)throw new Error(`CSV row ${index+2}: expected four fields.`);
    const values=Object.fromEntries(headers.map((key,i)=>[key,row[i]===''?NaN:Number(row[i])])) as DemandHour;
    for(const key of columns){
      const limit=key==='hour'?167:key==='passengers'?10000:1000;
      if(!Number.isFinite(values[key])||values[key]<0||values[key]>limit)throw new Error(`CSV row ${index+2}: ${key} must be a number from 0 to ${limit}.`);
    }
    if(!Number.isInteger(values.hour))throw new Error(`CSV row ${index+2}: hour must be a whole number.`);
    return values;
  });
  if(new Set(result.map(row=>row.hour)).size!==168)throw new Error('Hours must be unique and complete: 0 through 167. Check duplicate hours.');
  return result.sort((a,b)=>a.hour-b.hour);
}
export function downloadFile(name:string,text:string,type='text/csv'){
  const url=URL.createObjectURL(new Blob([text],{type}));
  const link=document.createElement('a');link.href=url;link.download=name;link.click();
  setTimeout(()=>URL.revokeObjectURL(url),1000);
}
export function demandCSV(rows:DemandHour[]){return [columns.join(','),...rows.map(row=>columns.map(c=>row[c]).join(','))].join('\n');}

export function sampleDemand():DemandHour[]{
  return Array.from({length:168},(_,hour)=>{
    const clock=hour%24,day=Math.floor(hour/24);
    const aircraft=Math.round((1.2+4*Math.exp(-(((clock-11)/3)**2))+5*Math.exp(-(((clock-18)/3)**2)))*[1,1.1,1.2,1.4,1.8,2,1.5][day]*25)/100;
    return {hour,aircraft,passengers:Math.round(aircraft*4.5*100)/100,fuel_requests:Math.round(aircraft*.65*100)/100};
  });
}
