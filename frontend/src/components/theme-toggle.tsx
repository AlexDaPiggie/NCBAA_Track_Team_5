'use client';

import {Moon,Sun} from 'lucide-react';
import {Button} from '@/components/ui/button';
import {Tooltip,TooltipContent,TooltipTrigger} from '@/components/ui/tooltip';
import {useTheme} from './theme-provider';

export function ThemeToggle(){
  const {theme,toggleTheme}=useTheme();
  const action=`Switch to ${theme==='light'?'dark':'light'} mode`;
  return <Tooltip><TooltipTrigger asChild><Button variant="outline" className="ops-theme-toggle" onClick={toggleTheme} aria-label={action}>{theme==='light'?<Sun size={15}/>:<Moon size={15}/>}<span>{theme==='light'?'Light mode':'Dark mode'}</span></Button></TooltipTrigger><TooltipContent>{action}</TooltipContent></Tooltip>;
}
