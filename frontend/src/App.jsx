import React from 'react';
import SceneErrorBoundary from './SceneErrorBoundary.jsx';
import { INITIAL, parkingService } from './services/parkingService.js';
import { useCallback, useEffect, useRef, useState, useSyncExternalStore } from 'react';
import Spline from '@splinetool/react-spline';
import { Activity, BarChart3, CarFront, CircleParking, DoorOpen, LayoutDashboard, ParkingSquare, Radio, RotateCcw, ShieldCheck } from 'lucide-react';
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';

const SCENE_URL = 'https://prod.spline.design/NNU0y3In1BxfOzsL/scene.splinecode';
const label = { EMPTY: 'Còn trống', OCCUPIED: 'Có xe', UNKNOWN: 'Không xác định' };
const timeNow = () => new Date().toLocaleTimeString('vi-VN', { hour12: false });

export default function App() {
  const [page, setPage] = useState('overview');
  const pages = {
    overview: { title: 'Smart Parking Dashboard', description: 'Theo dõi sức chứa, trạng thái bãi xe và mô hình 3D. Chọn một mục bên trái để thao tác chi tiết.' },
    slots: { title: 'Quản lý ô đỗ', description: 'Nhấn P01–P04 để mô phỏng xe vào hoặc rời bãi. UNKNOWN mô phỏng cảm biến chưa xác định. Điều khiển cổng ở phía dưới.' },
    history: { title: 'Lịch sử hoạt động', description: 'Theo dõi thời gian, vị trí, loại sự kiện và trạng thái trước/sau. Sự kiện mới nhất nằm đầu bảng; dữ liệu chỉ lưu trong phiên.' },
    statistics: { title: 'Báo cáo thống kê', description: 'Tổng hợp lượt xe vào, xe ra và lượt vào theo từng ô từ lịch sử của phiên hiện tại. Tạo sự kiện trong Quản lý ô đỗ để cập nhật biểu đồ.' }
  };
  const spline = useRef(null);
  const initialBarrierRotation = useRef(null);
  const state = useSyncExternalStore(parkingService.subscribe, parkingService.getParkingStatus);
  const { slots, events } = state;
  const gateOpen = state.gate === 'OPEN';
  const [sceneError, setSceneError] = useState('');
  const [axis, setAxis] = useState('');
  const [direction, setDirection] = useState(1);
  const [diagnostics, setDiagnostics] = useState([]);
  const statistics = parkingService.getParkingStatistics();
  const sampleChart = Object.keys(INITIAL).map(id => ({ time: id, count: events.filter(e => e.slotId === id && e.type === 'IN').length }));
  const [sceneReady, setSceneReady] = useState(false);
  const [checks, setChecks] = useState({});
  const occupied = Object.values(slots).filter(s => s === 'OCCUPIED').length;
  const empty = Object.values(slots).filter(s => s === 'EMPTY').length;
  const unknown = Object.values(slots).filter(s => s === 'UNKNOWN').length;
  const full = occupied === 4;
  const parkingStatus = full ? 'FULL' : empty > 0 ? 'AVAILABLE' : 'UNKNOWN';

  const syncScene = useCallback((app, nextSlots, nextGate) => {
    if (!app) return;
    Object.entries(nextSlots).forEach(([id, state]) => {
      const car = app.findObjectByName(`Car_${id}`);
      if (car) car.visible = state === 'OCCUPIED';
      const slot = app.findObjectByName(`Slot_${id}`);
      if (slot && 'color' in slot) {
        const color = state === 'EMPTY' ? '#22c55e' : state === 'OCCUPIED' ? '#f97316' : '#94a3b8';
        try { slot.color = color; } catch (error) { console.error('Slot color:', id, error); }
      }
    });
    const barrier = app.findObjectByName('Gate_Barrier');
    if (barrier && initialBarrierRotation.current !== null) {
      for (const key of ['x','y','z']) barrier.rotation[key] = initialBarrierRotation.current[key];
      if (axis && nextGate) barrier.rotation[axis] += direction * Math.PI / 2;
    }
  }, [axis, direction]);

  function handleLoad(app) {
    const loadedObjects = app.getAllObjects();
    if (!loadedObjects.length) {
      spline.current = null;
      setSceneReady(false);
      setSceneError('Runtime chưa cung cấp đối tượng nào. Scene chưa sẵn sàng; không thể kết luận tên bị sai.');
      setDiagnostics([]);
      return;
    }
    setSceneError('');
    spline.current = app;
    const names = ['Slot_P01', 'Slot_P02', 'Slot_P03', 'Slot_P04', 'Car_P01', 'Car_P02', 'Car_P03', 'Car_P04', 'Gate_Base', 'Gate_Barrier', 'Parking_Ground', 'Parking_Road'];
    setChecks(Object.fromEntries(names.map(name => [name, Boolean(app.findObjectByName(name))])));
    const barrier = app.findObjectByName('Gate_Barrier');
    initialBarrierRotation.current = barrier ? { x: barrier.rotation.x, y: barrier.rotation.y, z: barrier.rotation.z } : null;
    const issues = names.filter(name => !app.findObjectByName(name)).map(name => `Không tìm thấy ${name}; kiểm tra tên trong Spline Editor.`);
    for (const id of Object.keys(INITIAL)) { const obj = app.findObjectByName(`Slot_${id}`); if (obj && !('color' in obj)) issues.push(`Slot_${id}: chưa hỗ trợ màu qua color; cần kiểm tra material trong Spline Editor.`); }
    const actualObjects = app.getAllObjects().map(obj => ({ name: obj.name, id: obj.uuid }));
    console.table(actualObjects);
    if (issues.length) issues.push('Tên thực tế trong scene: ' + (actualObjects.map(obj => obj.name || '(không tên)').join(', ') || '(không có đối tượng)'));
    setDiagnostics(issues);
    console.table(Object.fromEntries(names.map(name => [name, Boolean(app.findObjectByName(name))])));
    syncScene(app, slots, gateOpen);
    setSceneReady(true);
  }

  useEffect(() => { syncScene(spline.current, slots, gateOpen); }, [slots, gateOpen, syncScene]);
  useEffect(() => { if (sceneReady) return; const timer = setTimeout(() => setSceneError('Scene chưa tải sau 30 giây. Kiểm tra mạng và quyền public trong Spline.'), 30000); return () => clearTimeout(timer); }, [sceneReady]);
  function changeSlot(id) { parkingService.updateSlotStatus(id, slots[id] === 'OCCUPIED' ? 'EMPTY' : 'OCCUPIED'); }
  function changeGate(open) { parkingService.updateGateStatus(open ? 'OPEN' : 'CLOSED'); }
  function reset() { parkingService.reset(); }

  return <div className="shell">
    <aside className="sidebar">
      <div className="brand"><ParkingSquare size={28}/><div><strong>SMART PARKING</strong><small>IoT Control Center</small></div></div>
      <nav aria-label="Điều hướng chức năng">{[
        ['overview', 'Tổng quan', LayoutDashboard], ['slots', 'Quản lý ô đỗ', CarFront],
        ['history', 'Lịch sử hoạt động', Activity], ['statistics', 'Báo cáo thống kê', BarChart3]
      ].map(([id, title, Icon]) => <button key={id} type="button" className={'nav ' + (page === id ? 'active' : '')} aria-current={page === id ? 'page' : undefined} onClick={() => setPage(id)}><Icon size={18}/>{title}</button>)}</nav>
      <div className="sidebar-bottom"><ShieldCheck size={16}/> Đồ án IoT · Đề tài 21</div>
    </aside>
    <main className="main">
      <header className="top"><div><p className="eyebrow">SMART PARKING · {page === 'overview' ? 'TỔNG QUAN' : 'CHỨC NĂNG'}</p><h1>{pages[page].title}</h1><p className="muted">Cập nhật: {new Date(state.timestamp).toLocaleString('vi-VN')} · Giám sát và mô phỏng bãi đỗ xe thông minh theo thời gian thực</p></div><div className="top-actions"><span className="live"><Radio size={15}/> DEMO MODE</span><button className="secondary" onClick={reset}><RotateCcw size={15}/> Đặt lại</button></div></header>
      <section className="page-intro" aria-live="polite"><p>{pages[page].description}</p>{page !== 'slots' && <button className="secondary" onClick={() => setPage('slots')}>Đi tới quản lý ô đỗ</button>}</section>
      <section className="kpis" hidden={page === 'history'}><article className="kpi"><span>Tổng số ô đỗ</span><strong>04</strong><small>Quy mô bãi xe</small></article><article className="kpi"><span>Đang sử dụng</span><strong>{String(occupied).padStart(2,'0')}</strong><small>{Math.round(occupied/4*100)}% công suất</small></article><article className="kpi"><span>Còn trống</span><strong className="green">{String(empty).padStart(2,'0')}</strong><small>Sẵn sàng tiếp nhận</small></article><article className="kpi"><span>Trạng thái bãi</span><strong className={full ? 'red state' : 'green state'}>{parkingStatus}</strong><small>{unknown} ô chưa xác định</small></article></section>
      <section className="workspace" hidden={page !== 'overview' && page !== 'slots'}><article className="panel scene"><div className="panel-head"><div><h2>Mô hình bãi xe 3D</h2><p>Trực quan trạng thái từ Spline</p></div><span className={sceneReady ? 'pill success' : 'pill'}>{sceneReady ? 'Scene loaded' : sceneError ? 'Scene error' : 'Loading scene'}</span></div><div className="scene-view"><SceneErrorBoundary onFailure={(error) => { spline.current = null; setSceneReady(false); setChecks({}); setDiagnostics([]); setSceneError(String(error.message || error)); }}><Spline scene={SCENE_URL} onLoad={handleLoad} onError={(error) => { console.error(error); setSceneError('Không thể tải scene Spline. Kiểm tra kết nối và Scene URL.'); }}/></SceneErrorBoundary></div><div className="scene-footer"><span>Scene: NNU0y3In1BxfOzsL</span><span>{Object.values(checks).filter(Boolean).length}/12 đối tượng được tìm thấy</span></div>{sceneError && <p role="alert" className="diagnostic">{sceneError}</p>}{diagnostics.map(message => <p className="diagnostic" key={message}>{message}</p>)}</article>
      <article className="panel"><div className="panel-head"><div><h2>Trạng thái ô đỗ</h2><p>Nhấn từng ô để giả lập xe vào/ra</p></div><span className="pill">4 vị trí</span></div><div className="slots">{Object.entries(slots).map(([id,state]) => <div key={id}><button className={`slot ${state.toLowerCase()}`} key={id} onClick={() => changeSlot(id)}><div className="slot-top"><b>{id}</b><CarFront size={20}/></div><span>{label[state]}</span><small>Nhấn để chuyển trạng thái</small></button><button className="secondary" onClick={() => parkingService.updateSlotStatus(id, 'UNKNOWN')}>UNKNOWN {id}</button></div>)}</div><div className="gate"><div><h3><DoorOpen size={18}/> Điều khiển barrier</h3><p>Trạng thái: <b>{gateOpen ? 'OPEN' : 'CLOSED'}</b></p></div><p>Chọn trục và chiều sau khi quan sát bản lề trong scene. Chưa chọn: chỉ cập nhật trạng thái, chưa xoay 3D.</p><select aria-label="Trục barrier" value={axis} onChange={e => setAxis(e.target.value)}><option value="">Chưa xác minh trục</option>{['x','y','z'].map(a => <option key={a} value={a}>{a.toUpperCase()}</option>)}</select><select aria-label="Chiều xoay" value={direction} onChange={e => setDirection(Number(e.target.value))}><option value="1">+90°</option><option value="-1">−90°</option></select><div className="gate-buttons"><button className={gateOpen ? 'primary' : 'secondary'} onClick={() => changeGate(true)}>Mở cổng</button><button className={!gateOpen ? 'primary' : 'secondary'} onClick={() => changeGate(false)}>Đóng cổng</button></div></div></article></section>
      <section className={'bottom ' + (page === 'overview' ? '' : 'single-page')} hidden={page === 'slots'}><article className="panel" hidden={page === 'statistics'}><div className="panel-head"><div><h2>Lịch sử hoạt động</h2><p>Sự kiện giả lập trong phiên</p></div><span className="pill">{events.length} sự kiện</span></div><div className="events"><table><thead><tr><th>Thời gian</th><th>Vị trí</th><th>Loại</th><th>Trước</th><th>Sau</th></tr></thead><tbody>{events.length === 0 && <tr><td colSpan={5}>Chưa có sự kiện. Vào tab Quản lý ô đỗ để giả lập xe vào/ra hoặc mở/đóng cổng.</td></tr>}{events.map((e,i) => <tr key={i}><td>{new Date(e.timestamp).toLocaleTimeString('vi-VN')}</td><td>{e.slotId}</td><td><span className={`event-type ${e.type.toLowerCase()}`}>{e.type}</span></td><td>{e.previous}</td><td>{e.current}</td></tr>)}</tbody></table></div></article><article className="panel" hidden={page === 'history'}><div className="panel-head"><div><h2>Thống kê sử dụng</h2><p>Xe vào: {statistics.entries} · Xe ra: {statistics.exits}</p></div><span className="pill">Phiên hiện tại</span></div><div className="chart">{page !== 'history' && page !== 'slots' && <ResponsiveContainer width="100%" height="100%"><BarChart data={sampleChart}><CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e9edf4"/><XAxis dataKey="time" tickLine={false} axisLine={false} fontSize={12}/><YAxis allowDecimals={false}  tickLine={false} axisLine={false} fontSize={12}/><Tooltip/><Bar dataKey="count" fill="#4477e8" radius={[5,5,0,0]} name="Lượt xe vào"/></BarChart></ResponsiveContainer>}</div></article></section>
      <footer>Smart Parking IoT MVP · Dữ liệu đang giả lập — chưa kết nối ESP32 / MQTT / FastAPI.</footer>
    </main>
  </div>;
}




