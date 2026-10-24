'use client';

import {createContext,useContext,useEffect,useState,type ReactNode} from 'react';
import {themeStorageKey as key} from '@/lib/theme';

type Theme='light'|'dark';
const ThemeContext=createContext<{theme:Theme;toggleTheme:()=>void}|null>(null);

function applyTheme(theme:Theme){
  const root=document.documentElement;
  root.dataset.theme=theme;
  root.classList.toggle('dark',theme==='dark');
  root.classList.toggle('light',theme==='light');
}

export function ThemeProvider({children}:{children:ReactNode}){
  const [theme,setTheme]=useState<Theme>('light');
  useEffect(()=>{
    // The head script applies the saved palette before the page paints.
    const initial=document.documentElement.dataset.theme==='dark'?'dark':'light';
    applyTheme(initial);setTheme(initial);
    const onStorage=(event:StorageEvent)=>{
      if(event.key===key||event.key===null){const next=event.newValue==='dark'?'dark':'light';applyTheme(next);setTheme(next);}
    };
    window.addEventListener('storage',onStorage);
    return ()=>window.removeEventListener('storage',onStorage);
  },[]);
  function toggleTheme(){
    const next=theme==='light'?'dark':'light';
    applyTheme(next);setTheme(next);
    try{localStorage.setItem(key,next);}catch{/* Switching still works when storage is unavailable. */}
  }
  return <ThemeContext.Provider value={{theme,toggleTheme}}>{children}</ThemeContext.Provider>;
}

export function useTheme(){
  const context=useContext(ThemeContext);
  if(!context)throw new Error('Theme controls require ThemeProvider.');
  return context;
}

