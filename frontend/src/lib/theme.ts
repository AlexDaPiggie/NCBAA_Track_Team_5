export const themeStorageKey='crewpilot-theme';
export const themeBootScript=`try{var t=localStorage.getItem('${themeStorageKey}')==='dark'?'dark':'light';var r=document.documentElement;r.dataset.theme=t;r.classList.toggle('dark',t==='dark');r.classList.toggle('light',t==='light');}catch(e){}`;
