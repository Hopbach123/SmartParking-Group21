import { parkingService as demo } from './parkingService.js';
import { createLiveParkingService } from './liveParkingService.js';
const env = import.meta.env;
export const mode = (env.VITE_PARKING_MODE || 'DEMO').toUpperCase();
if (!['DEMO','LIVE'].includes(mode)) throw new Error('VITE_PARKING_MODE phải là DEMO hoặc LIVE');
function liveConfig() {
  const rest = new URL(env.VITE_BACKEND_REST_URL || '/', window.location.origin);
  const ws = new URL(env.VITE_BACKEND_WS_URL || '/ws/parking', window.location.origin);
  if(ws.protocol==='http:') ws.protocol='ws:';
  if(ws.protocol==='https:') ws.protocol='wss:';
  if(!['http:','https:'].includes(rest.protocol) || !['ws:','wss:'].includes(ws.protocol)) throw new Error('URL Backend không hợp lệ');
  return {restUrl:rest.href.replace(/\/$/,''),wsUrl:ws.href};
}
export const parkingService = mode==='LIVE' ? createLiveParkingService(liveConfig()) : demo;
