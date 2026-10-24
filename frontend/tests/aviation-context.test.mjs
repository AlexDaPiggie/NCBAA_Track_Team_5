import test from 'node:test';
import assert from 'node:assert/strict';
import {laxSuperBowl2022Context,laxSuperBowl2022TotalArrivals} from '../src/lib/aviation-context.ts';

test('LAX historical arrivals are complete, sourced, and explicitly context-only',()=>{
  assert.equal(laxSuperBowl2022Context.airport,'LAX');
  assert.equal(laxSuperBowl2022Context.periodStart,'2022-02-07');
  assert.equal(laxSuperBowl2022Context.periodEnd,'2022-02-13');
  assert.equal(laxSuperBowl2022Context.arrivals.length,24);
  assert.deepEqual(laxSuperBowl2022Context.arrivals.map(row=>row.hour),Array.from({length:24},(_,hour)=>hour));
  assert.equal(laxSuperBowl2022TotalArrivals,3502);
  assert.equal(laxSuperBowl2022Context.usage,'reference-only');
  assert.match(laxSuperBowl2022Context.limitations,/not general aviation/i);
  assert.match(laxSuperBowl2022Context.limitations,/forecast for 2027/i);
});
