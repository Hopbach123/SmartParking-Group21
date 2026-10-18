import { test } from 'node:test';
import assert from 'node:assert/strict';
import { createLiveParkingService, validateLiveSnapshot } from '../src/services/liveParkingService.js';
const now='2026-10-18T12:00:00Z';
const snap=(revision=1,stream_id='A')=>({schema_version:'1.0',source:'LIVE',timestamp:now,slots:{P01:'EMPTY',P02:'EMPTY',P03:'UNKNOWN',P04:'OCCUPIED'},gate:'CLOSED',gate_meta:{confirmed:false,confirmed_at:null,pending_command_id:null},connection:{mqtt:'CONNECTED',device:'ONLINE',synchronized:false},stream_id,revision,events:[]});
const record=(state='PENDING')=>({command_id:'cmd-1',requested_status:'OPEN',direction:'ENTRY',state,created_at:now,completed_at:state==='PENDING'?null:now,error_code:null});
const tick=()=>new Promise(r=>setImmediate(r));
function harness({initial=snap(),saved=null,post,getCommand}={}) {
 const sockets=[],timers=new Map(),calls=[]; let next=0, dataset=initial, command=record();
 class WS { constructor(){sockets.push(this);} close(){this.closed=true;} open(){return this.onopen();} message(v){this.onmessage({data:typeof v==='string'?v:JSON.stringify(v)});} disconnect(){this.onclose();} }
 const storage={value:saved,getItem(){return this.value;},setItem(k,v){this.value=v;},removeItem(){this.value=null;}};
 const service=createLiveParkingService({restUrl:'http://backend',wsUrl:'ws://backend/ws/parking',WebSocketImpl:WS,storage,makeId:()=> 'cmd-1',
 setTimer(fn,delay){const id=++next;timers.set(id,{fn,delay});return id;},clearTimer(id){timers.delete(id);},
 async fetchImpl(url,options){calls.push({url,...options}); if(options.method==='POST' && post)return post(url,options);
 if(url.includes('/commands/') && getCommand)return getCommand();
 return {ok:true,json:async()=>url.includes('/commands/')?command:options.method==='POST'?command:dataset};}});
 return {service,sockets,timers,calls,storage,setData(v){dataset=v;},setCommand(v){command=v;},async start(){service.start();await sockets.at(-1).open();await tick();},async run(delay){const item=[...timers].find(([,t])=>t.delay===delay);assert.ok(item,`timer ${delay}`);timers.delete(item[0]);await item[1].fn();await tick();},stop(){service.stop();}};
}
const msg=data=>({type:'parking.snapshot',schema_version:'1.0',data});
test('LIVE starts UNKNOWN; store stable, frozen, no RESET/slot writes',async()=>{
 const h=harness();const s=h.service;assert.ok(Object.values(s.getParkingStatus().slots).every(v=>v==='UNKNOWN'));
 assert.equal(s.getParkingStatus(),s.getParkingStatus());assert.throws(()=>s.reset());assert.throws(()=>s.updateSlotStatus());
 await h.start();assert.equal(s.getParkingStatus().client.stale,false);assert.throws(()=>{s.getParkingStatus().slots.P01='BAD';});h.stop();assert.equal(h.timers.size,0);
});
test('WS applies newer revisions, ignores duplicates/old snapshots and computes history from server',async()=>{
 const h=harness();await h.start();const v=snap(3);v.slots.P01='OCCUPIED';v.events=[{id:'e',timestamp:now,slotId:'P01',type:'IN',previous:'EMPTY',current:'OCCUPIED'}];
 h.sockets[0].message(msg(v));h.sockets[0].message(msg(snap(2)));assert.equal(h.service.getParkingStatus().revision,3);assert.equal(h.service.getParkingStatistics().entries,1);h.stop();
});
test('malformed WS disconnects without erasing last known history; reconnect fetches REST and accepts new stream',async()=>{
 const h=harness();await h.start();h.sockets[0].message('bad json');assert.equal(h.service.getParkingStatus().client.stale,true);assert.equal(h.service.getParkingStatus().slots.P01,'EMPTY');
 h.setData(snap(0,'B'));await h.run(1000);await h.sockets[1].open();assert.equal(h.service.getParkingStatus().stream_id,'B');assert.equal(h.service.getParkingStatus().revision,0);assert.equal(h.service.getParkingStatus().client.stale,false);h.stop();
});
test('disconnect blocks commands, preserves last-known and old socket cannot mutate after reconnect',async()=>{
 const h=harness();await h.start();h.sockets[0].disconnect();assert.throws(()=>h.service.updateGateStatus('OPEN','ENTRY'));
 h.setData(snap(7));await h.run(1000);await h.sockets[1].open();h.sockets[0].message(msg(snap(99)));assert.equal(h.service.getParkingStatus().revision,7);h.stop();
});
test('REST newer than initial WS buffer is not rolled back',async()=>{
 const h=harness({initial:snap(8)});h.service.start();h.sockets[0].message(msg(snap(2)));await h.sockets[0].open();assert.equal(h.service.getParkingStatus().revision,8);h.stop();
});
test('REST/WS stream mismatch forces resync rather than mixing datasets',async()=>{
 const h=harness({initial:snap(1,'B')});h.service.start();h.sockets[0].message(msg(snap(8,'A')));await h.sockets[0].open();assert.equal(h.service.getParkingStatus().client.stale,true);assert.equal(h.service.getParkingStatus().stream_id,'B');h.stop();
});
test('gate POST keeps confirmed position until ACK and command/snapshot same revision both apply',async()=>{
 const h=harness();await h.start();await h.service.updateGateStatus('OPEN','ENTRY');assert.equal(h.service.getParkingStatus().gate,'CLOSED');assert.equal(h.service.getParkingStatus().client.command.state,'PENDING');
 assert.throws(()=>h.service.updateGateStatus('CLOSED','EXIT'));assert.deepEqual(JSON.parse(h.calls.find(c=>c.method==='POST').body),{command_id:'cmd-1',status:'OPEN',direction:'ENTRY'});
 h.sockets[0].message({type:'gate.command',schema_version:'1.0',stream_id:'A',revision:4,data:record('CONFIRMED')});const v=snap(4);v.gate='OPEN';v.gate_meta={confirmed:true,confirmed_at:now,pending_command_id:null};h.sockets[0].message(msg(v));
 assert.equal(h.service.getParkingStatus().gate,'OPEN');assert.equal(h.service.getParkingStatus().client.command.state,'CONFIRMED');h.stop();
});
test('FULL rejection exposes backend error and never optimistically opens gate',async()=>{
 const h=harness({post:async()=>({ok:false,status:409,json:async()=>({error:{code:'PARKING_FULL',message:'Full'}})})});await h.start();await h.service.updateGateStatus('OPEN','ENTRY');assert.match(h.service.getParkingStatus().client.commandError,/PARKING_FULL/);assert.equal(h.service.getParkingStatus().gate_meta.confirmed,false);assert.equal(h.storage.value,null);h.stop();
});
test('ambiguous POST is recoverable by same ID, never automatic republish',async()=>{
 let count=0;const h=harness({post:async()=>{count++;throw new Error('Network lost');}});await h.start();h.setCommand(record('TIMEOUT'));await h.service.updateGateStatus('OPEN','ENTRY');await tick();assert.equal(count,1);assert.equal(h.service.getParkingStatus().client.command.state,'TIMEOUT');assert.equal(h.service.getParkingStatus().gate,'CLOSED');h.stop();
});
test('refresh recovers saved command with GET only',async()=>{
 const h=harness({saved:JSON.stringify({command_id:'cmd-1',status:'OPEN',direction:'ENTRY'})});h.setCommand(record('CONFIRMED'));await h.start();assert.equal(h.service.getParkingStatus().client.command.state,'CONFIRMED');assert.equal(h.calls.filter(c=>c.method==='POST').length,0);h.stop();
});
test('refresh without pending request can recover server pending command',async()=>{
 const v=snap();v.gate_meta.pending_command_id='cmd-1';const h=harness({initial:v});await h.start();assert.equal(h.service.getParkingStatus().client.command.state,'PENDING');h.stop();
});
test('no duplicate events; reject invalid event enums, duplicate IDs, wrong source and connection',()=>{
 for(const change of [v=>v.source='DEMO',v=>v.connection.device='BAD',v=>v.revision=-1,v=>v.gate_meta.confirmed='yes',v=>v.events=[{id:'x',timestamp:now,slotId:'P01',type:'GATE',previous:'EMPTY',current:'EMPTY'}]]){const v=snap();change(v);assert.throws(()=>validateLiveSnapshot(v));}
 const e={id:'x',timestamp:now,slotId:'P01',type:'STATUS',previous:'UNKNOWN',current:'OCCUPIED'};assert.throws(()=>validateLiveSnapshot({...snap(),events:[e,e]}));
});
test('history baseline STATUS does not fabricate an IN, FULL/UNKNOWN data left intact',async()=>{
 const v=snap();v.slots={P01:'OCCUPIED',P02:'OCCUPIED',P03:'OCCUPIED',P04:'OCCUPIED'};v.events=[{id:'b',timestamp:now,slotId:'P01',type:'STATUS',previous:'UNKNOWN',current:'OCCUPIED'}];const h=harness({initial:v});await h.start();assert.equal(h.service.getParkingStatistics().entries,0);assert.ok(Object.values(h.service.getParkingStatus().slots).every(s=>s==='OCCUPIED'));h.stop();
});

test('unknown outcome retains ID; explicit retry reuses exact request, reconnect never reposts',async()=>{
 let posts=[];const h=harness({post:async(u,o)=>{posts.push(o.body);throw new Error('Lost response');},getCommand:()=>({ok:false,status:404,json:async()=>({error:{message:'Missing'}})})});
 await h.start();await h.service.updateGateStatus('OPEN','EXIT');await tick();assert.equal(h.service.getParkingStatus().client.uncertain,true);assert.match(h.storage.value,/cmd-1/);
 await h.service.retryCommand();await tick();assert.equal(posts.length,2);assert.equal(posts[0],posts[1]);
 h.sockets[0].disconnect();await h.run(1000);await h.sockets[1].open();assert.equal(posts.length,2);h.stop();
});
test('WS handshake timeout schedules bounded reconnect',async()=>{
 const h=harness();h.service.start();await h.run(10000);assert.equal(h.service.getParkingStatus().client.transport,'DISCONNECTED');assert.ok([...h.timers.values()].some(t=>t.delay===1000));h.stop();
});
test('late POST PENDING cannot regress a command already confirmed by WS',async()=>{
 let finish;const h=harness({post:()=>new Promise(r=>finish=r)});await h.start();const sending=h.service.updateGateStatus('OPEN','ENTRY');
 h.sockets[0].message({type:'gate.command',schema_version:'1.0',stream_id:'A',revision:2,data:record('CONFIRMED')});finish({ok:true,json:async()=>record()});await sending;assert.equal(h.service.getParkingStatus().client.command.state,'CONFIRMED');h.stop();
});

test('503 DEVICE_UNAVAILABLE before persistence clears local pending and polling',async()=>{
 const h=harness({post:async()=>({ok:false,status:503,json:async()=>({error:{code:'DEVICE_UNAVAILABLE',message:'MQTT/device not online'}})})});
 await h.start();await h.service.updateGateStatus('OPEN','ENTRY');await tick();
 const state=h.service.getParkingStatus();assert.equal(state.client.command,null);assert.equal(state.client.uncertain,false);assert.match(state.client.commandError,/DEVICE_UNAVAILABLE/);assert.equal(h.storage.value,null);assert.equal(h.calls.filter(c=>c.url.includes('/commands/')).length,0);h.stop();
});
test('offline snapshot prevents creating or sending a new gate request',async()=>{
 const v=snap();v.connection.device='OFFLINE';const h=harness({initial:v});await h.start();
 assert.throws(()=>h.service.updateGateStatus('OPEN','ENTRY'),/OFFLINE/);assert.equal(h.storage.value,null);assert.equal(h.calls.filter(c=>c.method==='POST').length,0);h.stop();
});
test('503 PUBLISH_FAILED remains recoverable and is never mistaken for preflight rejection',async()=>{
 const h=harness({post:async()=>({ok:false,status:503,json:async()=>({error:{code:'PUBLISH_FAILED',message:'Delivery unknown'}})})});await h.start();h.setCommand(record('ERROR'));
 await h.service.updateGateStatus('OPEN','ENTRY');await tick();assert.equal(h.service.getParkingStatus().client.command.state,'ERROR');assert.equal(h.service.getParkingStatus().gate,'CLOSED');h.stop();
});
