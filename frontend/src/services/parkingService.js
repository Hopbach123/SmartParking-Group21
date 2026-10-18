/** Frontend contract v1. Timestamps: ISO 8601 UTC. No persistence or network calls. */
export const SLOT_IDS = Object.freeze(['P01', 'P02', 'P03', 'P04']);
export const SLOT_STATUSES = Object.freeze(['EMPTY', 'OCCUPIED', 'UNKNOWN']);
export const GATE_STATUSES = Object.freeze(['OPEN', 'CLOSED']);
export const INITIAL = Object.freeze(Object.fromEntries(SLOT_IDS.map(id => [id, 'EMPTY'])));
export function validateParkingStatus(value) {
  if (!value || value.schema_version !== '1.0' || !value.slots ||
      Object.keys(value.slots).length !== SLOT_IDS.length ||
      !SLOT_IDS.every(id => Object.hasOwn(value.slots, id) && SLOT_STATUSES.includes(value.slots[id])) ||
      !GATE_STATUSES.includes(value.gate) || typeof value.timestamp !== 'string' ||
      !/^\d{4}-\d{2}-\d{2}T.*(?:Z|[+-]\d{2}:\d{2})$/.test(value.timestamp) ||
      !Number.isFinite(Date.parse(value.timestamp))) throw new TypeError('Invalid parking status v1');
  return value;
}
export function summarizeParking(slots) {
  const occupied = SLOT_IDS.filter(id => slots[id] === 'OCCUPIED').length;
  const available = SLOT_IDS.filter(id => slots[id] === 'EMPTY').length;
  const unknown = SLOT_IDS.filter(id => slots[id] === 'UNKNOWN').length;
  return { total: SLOT_IDS.length, occupied, available, unknown, status: occupied === SLOT_IDS.length ? 'FULL' : available ? 'AVAILABLE' : 'UNKNOWN' };
}
const freezeState = value => Object.freeze({ ...value, slots: Object.freeze({ ...value.slots }), events: Object.freeze(value.events.map(event => Object.freeze({ ...event }))) });
export function createParkingService() {
  const fresh = () => freezeState({ schema_version: '1.0', source: 'DEMO', slots: INITIAL, gate: 'CLOSED', timestamp: new Date().toISOString(), events: [] });
  let state = fresh();
  const listeners = new Set();
  const publish = next => { state = freezeState(next); listeners.forEach(fn => fn()); return state; };
  function updateSlotStatus(slotId, status) {
    if (!SLOT_IDS.includes(slotId) || !SLOT_STATUSES.includes(status)) throw new TypeError('Invalid slot or status');
    const previous = state.slots[slotId];
    if (previous === status) return state;
    const timestamp = new Date().toISOString();
    const type = status === 'OCCUPIED' ? 'IN' : previous === 'OCCUPIED' && status === 'EMPTY' ? 'OUT' : 'STATUS';
    return publish({ ...state, slots: { ...state.slots, [slotId]: status }, timestamp, events: [{ id: crypto.randomUUID(), timestamp, slotId, type, previous, current: status }, ...state.events] });
  }
  return {
    subscribe(fn) { listeners.add(fn); return () => listeners.delete(fn); },
    getParkingStatus: () => state,
    getParkingEvents: () => state.events,
    getParkingStatistics: () => ({ entries: state.events.filter(e => e.type === 'IN').length, exits: state.events.filter(e => e.type === 'OUT').length }),
    updateSlotStatus,
    updateGateStatus(status) {
      if (!GATE_STATUSES.includes(status)) throw new TypeError('Invalid gate status');
      if (state.gate === status) return state;
      const timestamp = new Date().toISOString();
      return publish({ ...state, gate: status, timestamp, events: [{ id: crypto.randomUUID(), timestamp, slotId: 'GATE', type: 'GATE', previous: state.gate, current: status }, ...state.events] });
    },
    reset() { return publish(fresh()); }
  };
}
export const parkingService = createParkingService();
