import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {runInNewContext} from 'node:vm';
import {themeBootScript} from '../src/lib/theme.ts';

const css=readFileSync(new URL('../src/app/themes.css',import.meta.url),'utf8');
const block=css.match(/:root\[data-theme="light"\]\s*\{([^}]+)\}/)[1];
const colors=Object.fromEntries([...block.matchAll(/--([a-z-]+):\s*(#[0-9a-f]{6})/g)].map(([,key,value])=>[key,value]));
function luminance(hex){
  const rgb=hex.slice(1).match(/../g).map(v=>parseInt(v,16)/255).map(v=>v<=.04045?v/12.92:((v+.055)/1.055)**2.4);
  return rgb[0]*.2126+rgb[1]*.7152+rgb[2]*.0722;
}
function contrast(a,b){const values=[luminance(a),luminance(b)].sort((x,y)=>y-x);return (values[0]+.05)/(values[1]+.05);}
test('light text, muted labels, and status badges meet 4.5:1 contrast',()=>{
  const pairs=[['foreground','background'],['foreground','card'],['muted-foreground','card'],['muted-foreground','background'],['primary-foreground','primary'],
    ...['cyan','green','amber','red'].map(status=>[`status-${status}-text`,`status-${status}-bg`])];
  for(const [text,surface] of pairs){const ratio=contrast(colors[text],colors[surface]);assert.ok(ratio>=4.5,`${text}/${surface}: ${ratio.toFixed(2)}:1`);}
});
test('light chart traces remain distinct from white surfaces',()=>{
  for(const key of ['chart-demand','chart-capacity','chart-conflict'])assert.ok(contrast(colors[key],colors.card)>=3,key);
});
test('saved theme is applied before paint; default and blocked storage stay readable',()=>{
  for(const choice of [null,'light','dark','invalid','blocked']){
    const classes=new Set(['light','other-class']);
    const root={dataset:{theme:'light'},classList:{toggle(name,on){if(on)classes.add(name);else classes.delete(name);}}};
    runInNewContext(themeBootScript,{document:{documentElement:root},localStorage:{getItem(){if(choice==='blocked')throw new Error('Storage unavailable');return choice;}}});
    const expected=choice==='dark'?'dark':'light';
    assert.equal(root.dataset.theme,expected);assert.ok(classes.has(expected));
    assert.ok(!classes.has(expected==='dark'?'light':'dark'));assert.ok(classes.has('other-class'));
  }
});
