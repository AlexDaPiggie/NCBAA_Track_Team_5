import test from 'node:test';
import assert from 'node:assert/strict';
import {demandCSV,parseDemandCSV,sampleDemand} from '../src/demand-csv.ts';

test('synthetic sample round-trips as a complete ordinary week',()=>{
  const rows=sampleDemand();assert.equal(rows.length,168);
  assert.deepEqual(parseDemandCSV(demandCSV(rows)),rows);
});
test('spreadsheet BOM, quoted fields, CRLF, and reordered rows work',()=>{
  const rows=sampleDemand().reverse();
  const csv='\uFEFF"fuel_requests","hour","passengers","aircraft"\r\n'+rows.map(r=>`"${r.fuel_requests}","${r.hour}","${r.passengers}","${r.aircraft}"`).join('\r\n');
  assert.deepEqual(parseDemandCSV(csv),sampleDemand());
});
test('duplicate and missing hours cannot silently replace a baseline',()=>{
  const rows=sampleDemand();rows[1].hour=0;
  assert.throws(()=>parseDemandCSV(demandCSV(rows)),/unique and complete/);
  assert.throws(()=>parseDemandCSV(demandCSV(rows.slice(1))),/exactly 168/);
});
test('reject identity columns, empty counts, negative and nonfinite demand',()=>{
  const valid=demandCSV(sampleDemand());
  assert.throws(()=>parseDemandCSV(valid.replace('fuel_requests','passenger_name')),/four headers/);
  for(const value of ['', '-1', 'Infinity', '=1+2']){
    const rows=sampleDemand();rows[0].aircraft=value;
    assert.throws(()=>parseDemandCSV(demandCSV(rows)),/aircraft must be a number/);
  }
});
test('malformed quotes and oversized inputs have clear errors',()=>{
  assert.throws(()=>parseDemandCSV('"hour'),/closing quote/);
  assert.throws(()=>parseDemandCSV('"hour"x,aircraft,passengers,fuel_requests'),/Unexpected text/);
  assert.throws(()=>parseDemandCSV('x'.repeat(100001)),/100 KB/);
});
