import { test } from 'node:test';
import assert from 'node:assert/strict';
import { createParkingService, validateParkingStatus, summarizeParking, SLOT_IDS } from '../src/services/parkingService.js';
test('UNKNOWN excludes availability and does not count a departure', () => {
 const s=createParkingService(); s.updateSlotStatus('P01','OCCUPIED'); s.updateSlotStatus('P01','UNKNOWN');
 assert.deepEqual(summarizeParking(s.getParkingStatus().slots),{total:4,occupied:0,available:3,unknown:1,status:'AVAILABLE'});
 assert.equal(s.getParkingStatistics().exits,0); assert.equal(s.getParkingEvents()[0].type,'STATUS');
 SLOT_IDS.forEach(id=>s.updateSlotStatus(id,'UNKNOWN')); assert.equal(summarizeParking(s.getParkingStatus().slots).status,'UNKNOWN');
});
test('RESET restores slots, gate, history, statistics and notifies once',()=>{
 const s=createParkingService(); s.updateSlotStatus('P01','OCCUPIED'); s.updateGateStatus('OPEN'); let calls=0;
 const stop=s.subscribe(()=>calls++); s.reset(); assert.equal(calls,1); stop();
 assert.ok(Object.values(s.getParkingStatus().slots).every(x=>x==='EMPTY')); assert.equal(s.getParkingStatus().gate,'CLOSED');
 assert.deepEqual(s.getParkingEvents(),[]); assert.deepEqual(s.getParkingStatistics(),{entries:0,exits:0});
});
test('fresh session is consistent and snapshot is immutable',()=>{
 const a=createParkingService(); a.updateSlotStatus('P01','OCCUPIED'); const b=createParkingService();
 assert.equal(b.getParkingStatus().slots.P01,'EMPTY'); assert.throws(()=>{b.getParkingStatus().slots.P01='UNKNOWN';});
 assert.equal(b.getParkingStatus(), b.getParkingStatus());
});
test('contract accepts JSON roundtrip, rejects missing slots, inherited IDs, invalid statuses and timezone-less timestamps',()=>{
 const s=createParkingService(); const v=JSON.parse(JSON.stringify(s.getParkingStatus())); assert.equal(validateParkingStatus(v),v);
 assert.throws(()=>s.updateSlotStatus('__proto__','EMPTY')); assert.throws(()=>s.updateGateStatus('BAD'));
 assert.throws(()=>validateParkingStatus({...v,slots:{P01:'EMPTY'}})); assert.throws(()=>validateParkingStatus({...v,timestamp:'2026-10-18T10:00:00'}));
});
test('entry, exit, FULL, no-op updates and statistics remain consistent',()=>{
 const s=createParkingService(); s.updateSlotStatus('P01','OCCUPIED'); s.updateSlotStatus('P01','OCCUPIED'); assert.equal(s.getParkingEvents().length,1);
 s.updateSlotStatus('P01','EMPTY'); assert.deepEqual(s.getParkingStatistics(),{entries:1,exits:1});
 SLOT_IDS.forEach(id=>s.updateSlotStatus(id,'OCCUPIED')); assert.equal(summarizeParking(s.getParkingStatus().slots).status,'FULL');
 assert.equal(summarizeParking(s.getParkingStatus().slots).available,0);
});
