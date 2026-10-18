import { SLOT_IDS, SLOT_STATUSES, GATE_STATUSES, validateParkingStatus } from './parkingService.js';

const iso = v => typeof v === 'string' && /(?:Z|[+-]\d{2}:\d{2})$/.test(v) && Number.isFinite(Date.parse(v));
const revision = v => Number.isSafeInteger(v) && v >= 0;
function browserStorage() { try { return globalThis.sessionStorage; } catch { return undefined; } }
function requireValue(ok, message) { if (!ok) throw new TypeError(message); }
export function validateLiveSnapshot(v) {
  validateParkingStatus(v);
  requireValue(v.source === 'LIVE' && typeof v.stream_id === 'string' && v.stream_id && revision(v.revision), 'Invalid LIVE stream');
  const m = v.gate_meta, c = v.connection;
  requireValue(m && typeof m.confirmed === 'boolean' && (m.confirmed_at === null || iso(m.confirmed_at)) && (m.pending_command_id === null || typeof m.pending_command_id === 'string'), 'Invalid gate metadata');
  requireValue(c && ['CONNECTED','DISCONNECTED'].includes(c.mqtt) && ['ONLINE','OFFLINE','UNKNOWN'].includes(c.device) && typeof c.synchronized === 'boolean', 'Invalid connection');
  requireValue(Array.isArray(v.events), 'Invalid history');
  const ids = new Set();
  for (const e of v.events) {
    requireValue(e && typeof e.id === 'string' && !ids.has(e.id) && iso(e.timestamp), 'Invalid event ID/time'); ids.add(e.id);
    const gate = e.slotId === 'GATE';
    requireValue((gate || SLOT_IDS.includes(e.slotId)) && (gate ? e.type === 'GATE' : ['IN','OUT','STATUS'].includes(e.type)) &&
      (gate ? GATE_STATUSES : SLOT_STATUSES).includes(e.previous) && (gate ? GATE_STATUSES : SLOT_STATUSES).includes(e.current), 'Invalid event');
  }
  return v;
}
export function validateCommand(v) {
  requireValue(v && typeof v.command_id === 'string' && /^[!-~]{1,80}$/.test(v.command_id) && GATE_STATUSES.includes(v.requested_status) &&
    ['ENTRY','EXIT'].includes(v.direction) && ['PENDING','CONFIRMED','ERROR','TIMEOUT'].includes(v.state) && iso(v.created_at) &&
    (v.completed_at === null || iso(v.completed_at)) && (v.error_code === null || typeof v.error_code === 'string'), 'Invalid command');
  return v;
}
function freeze(v) { if (v && typeof v === 'object') { Object.values(v).forEach(freeze); Object.freeze(v); } return v; }
export function createLiveParkingService({ restUrl, wsUrl, fetchImpl = globalThis.fetch, WebSocketImpl = globalThis.WebSocket,
  setTimer = setTimeout, clearTimer = clearTimeout, makeId = () => crypto.randomUUID(), storage = browserStorage() } = {}) {
  let state = freeze({ schema_version:'1.0', source:'LIVE', timestamp:new Date().toISOString(), slots:Object.fromEntries(SLOT_IDS.map(id=>[id,'UNKNOWN'])),
    gate:'CLOSED', gate_meta:{confirmed:false,confirmed_at:null,pending_command_id:null}, connection:{mqtt:'DISCONNECTED',device:'UNKNOWN',synchronized:false},
    stream_id:'', revision:0, events:[], client:{transport:'CONNECTING',stale:true,error:'',command:null,commandError:'',uncertain:false} });
  const listeners = new Set();
  let running=false, generation=0, socket, reconnectTimer, pollTimer, connectTimer, attempt=0, controller, pendingRequest=null, commandVersion=0;
  const emit = next => { state=freeze(next); listeners.forEach(fn=>fn()); };
  const client = patch => emit({...state,client:{...state.client,...patch}});
  const persist = () => { try { if(pendingRequest) storage?.setItem('smartparking.pending',JSON.stringify(pendingRequest)); else storage?.removeItem('smartparking.pending'); } catch { /* Storage may be disabled. */ } };
  async function request(path, options={}, signal=controller?.signal) {
    const timeout = new AbortController();
    const abort = () => timeout.abort(); signal?.addEventListener('abort',abort,{once:true});
    if(signal?.aborted) timeout.abort();
    const timer=setTimer(abort,10000);
    try {
      const response=await fetchImpl(restUrl.replace(/\/$/,'')+path,{cache:'no-store',...options,signal:timeout.signal});
      const body=await response.json();
      if(!response.ok) { const error=new Error(body?.error?.message || `HTTP ${response.status}`); error.code=body?.error?.code; error.http=response.status; throw error; }
      return body;
    } finally { clearTimer(timer); signal?.removeEventListener('abort',abort); }
  }
  function applySnapshot(value) {
    validateLiveSnapshot(value);
    if(value.stream_id===state.stream_id && value.revision<=state.revision) return;
    emit({...value,client:state.client});
  }
  function applyCommand(value) {
    validateCommand(value);
    if(value.command_id!==pendingRequest?.command_id && value.command_id!==state.gate_meta.pending_command_id) return;
    if(state.client.command?.command_id===value.command_id && state.client.command.state!=='PENDING' && value.state==='PENDING') return;
    commandVersion++;
    client({command:value,commandError:value.error_code || '',uncertain:false});
    if(value.state!=='PENDING') { pendingRequest=null; persist(); clearTimer(pollTimer); }
  }
  async function recoverCommand(token) {
    const id=pendingRequest?.command_id || state.gate_meta.pending_command_id;
    if(!running || !id) return;
    const version=commandVersion;
    try {
      const value=await request('/api/parking/commands/'+encodeURIComponent(id));
      if(token!==generation) return;
      if(version===commandVersion) {
        applyCommand(value);
        if(value.state!=='PENDING') {
          const snapshot=await request('/api/parking/status');
          if(token===generation) {
            if(snapshot.stream_id!==state.stream_id) socket?.close();
            else applySnapshot(snapshot);
          }
        }
      }
    } catch(error) {
      if(token!==generation) return;
      client({commandError:error.http===404 ? 'Chưa tìm thấy lệnh. Có thể gửi lại cùng ID.' : error.message,uncertain:!!pendingRequest});
    }
    if(running && token===generation && (pendingRequest || state.gate_meta.pending_command_id)) pollTimer=setTimer(()=>recoverCommand(token),1500);
  }
  function connect() {
    if(!running) return;
    const token=++generation; controller=new AbortController(); let ready=false, buffered=[], commandRevision=-1, commandStream='', socketStream='';
    client({transport:'CONNECTING',stale:true,error:''});
    function message(value) {
      requireValue(value?.schema_version==='1.0','Invalid WS version');
      if(value.type==='parking.snapshot') { requireValue(value.data?.stream_id===socketStream,'REST/WS khác phiên Backend'); applySnapshot(value.data); return; }
      requireValue(value.type==='gate.command' && typeof value.stream_id==='string' && revision(value.revision),'Invalid WS message');
      validateCommand(value.data);
      requireValue(value.stream_id===socketStream,'Command khác phiên Backend');
      if(value.stream_id!==commandStream) { commandStream=value.stream_id; commandRevision=-1; }
      if(value.revision>commandRevision) { commandRevision=value.revision; applyCommand(value.data); }
    }
    function lost(error) {
      if(!running || token!==generation) return;
      ++generation; controller.abort(); clearTimer(pollTimer); clearTimer(connectTimer); socket?.close();
      client({transport:'DISCONNECTED',stale:true,error});
      reconnectTimer=setTimer(connect,Math.min(1000*2**Math.min(attempt++,5),30000));
    }
    try { socket=new WebSocketImpl(wsUrl); } catch(error) { lost(error.message); return; }
    connectTimer=setTimer(()=>lost('WebSocket không sẵn sàng sau 10 giây.'),10000);
    socket.onclose=()=>lost('Mất WebSocket. Đang kết nối lại; dữ liệu có thể đã cũ.');
    socket.onerror=()=>lost('Không kết nối được WebSocket.');
    socket.onmessage=event=>{
      if(token!==generation) return;
      try {
        const value=JSON.parse(event.data);
        if(!ready) { requireValue(buffered.length<256,'Quá nhiều bản tin khi đồng bộ'); buffered.push(value); return; }
        message(value);
      } catch(error) { lost('Dữ liệu Backend không hợp lệ: '+error.message); }
    };
    socket.onopen=async()=>{
      try {
        const snapshot=await request('/api/parking/status');
        if(token!==generation) return;
        socketStream=snapshot.stream_id; applySnapshot(snapshot); buffered.forEach(message); buffered=[]; ready=true; attempt=0;
        clearTimer(connectTimer); client({transport:'CONNECTED',stale:false,error:''}); clearTimer(pollTimer); recoverCommand(token);
      } catch(error) { if(token===generation) lost('Không đồng bộ được REST: '+error.message); }
    };
  }
  async function send(body) {
    pendingRequest=body; persist(); client({commandError:'',uncertain:false,command:{command_id:body.command_id,requested_status:body.status,direction:body.direction,state:'PENDING',created_at:new Date().toISOString(),completed_at:null,error_code:null}});
    const token=generation;
    try {
      const value=await request('/api/parking/gate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
      if(token===generation) applyCommand(value);
    } catch(error) {
      if(token!==generation) return;
      // DEVICE_UNAVAILABLE is rejected before persistence. Other 503/network outcomes may have executed; resolve by ID.
      if(error.http===409 || error.http===422 || (error.http===503 && error.code==='DEVICE_UNAVAILABLE')) { pendingRequest=null; persist(); client({command:null,commandError:`${error.code || 'REJECTED'}: ${error.message}`,uncertain:false}); }
      else client({commandError:error.message,uncertain:true});
    }
    if(running && token===generation) { clearTimer(pollTimer); recoverCommand(token); }
  }
  return {
    subscribe(fn) { listeners.add(fn); return ()=>listeners.delete(fn); },
    getParkingStatus:()=>state, getParkingEvents:()=>state.events,
    getParkingStatistics:()=>({entries:state.events.filter(e=>e.type==='IN').length,exits:state.events.filter(e=>e.type==='OUT').length}),
    start() { if(running) return; running=true; try { const saved=JSON.parse(storage?.getItem('smartparking.pending') || 'null'); if(saved && /^[!-~]{1,80}$/.test(saved.command_id) && GATE_STATUSES.includes(saved.status) && ['ENTRY','EXIT'].includes(saved.direction)) pendingRequest=saved; } catch { /* Ignore invalid storage. */ } connect(); },
    stop() { running=false; ++generation; controller?.abort(); clearTimer(reconnectTimer); clearTimer(pollTimer); clearTimer(connectTimer); socket?.close(); },
    updateSlotStatus() { throw new Error('LIVE không hỗ trợ giả lập ô đỗ'); }, reset() { throw new Error('LIVE không hỗ trợ RESET'); },
    updateGateStatus(status,direction) {
      requireValue(GATE_STATUSES.includes(status) && ['ENTRY','EXIT'].includes(direction),'Chọn ENTRY hoặc EXIT');
      requireValue(!state.client.stale && state.client.transport==='CONNECTED','Chưa đồng bộ Backend');
      requireValue(!pendingRequest && !state.gate_meta.pending_command_id,'Đang có lệnh chờ');
      requireValue(state.connection.mqtt==='CONNECTED' && state.connection.device==='ONLINE','ESP32 đang OFFLINE hoặc MQTT chưa kết nối. Chờ thiết bị ONLINE.');
      return send({command_id:makeId(),status,direction});
    },
    retryCommand() { requireValue(pendingRequest && !state.client.stale,'Không có lệnh cần thử lại hoặc chưa kết nối'); return send({...pendingRequest}); }
  };
}
