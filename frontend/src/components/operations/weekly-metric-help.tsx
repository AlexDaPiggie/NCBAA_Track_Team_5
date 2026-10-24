'use client';

import {useState} from 'react';
import {Info} from 'lucide-react';
import {Tooltip,TooltipContent,TooltipProvider,TooltipTrigger} from '@/components/ui/tooltip';

export function WeeklyMetricHelp({label,children}:{label:string;children:React.ReactNode}){
  const [open,setOpen]=useState(false);
  return <TooltipProvider delayDuration={150}><Tooltip open={open} onOpenChange={setOpen}><TooltipTrigger asChild><button type="button" className="ops-week-help" aria-label={`About ${label}`} onClick={event=>{event.preventDefault();setOpen(value=>!value);}}><Info size={13}/></button></TooltipTrigger><TooltipContent sideOffset={5} className="ops-week-help-content">{children}</TooltipContent></Tooltip></TooltipProvider>;
}
