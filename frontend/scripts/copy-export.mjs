import {cpSync} from 'node:fs';
cpSync(new URL('../out/',import.meta.url),new URL('../dist/',import.meta.url),{recursive:true});
console.log('Static export copied to dist for the desktop package.');
