import type {Metadata} from 'next';
import {TooltipProvider} from '@/components/ui/tooltip';
import {ThemeProvider} from '@/components/theme-provider';
import {themeBootScript} from '@/lib/theme';
import './globals.css';
import './themes.css';

export const metadata:Metadata={title:'CrewPilot AI | Mission Control',description:'An aviation staffing command center. Simulate arrival waves, test crew disruptions, and review explainable recovery plans using labeled synthetic data.'};
export default function RootLayout({children}:{children:React.ReactNode}){
  return <html lang="en" className="light" data-theme="light" suppressHydrationWarning><head><script id="crewpilot-theme-init" dangerouslySetInnerHTML={{__html:themeBootScript}}/></head><body><ThemeProvider><TooltipProvider>{children}</TooltipProvider></ThemeProvider></body></html>;
}
