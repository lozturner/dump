import * as THREE from 'three';
import { PointerLockControls } from 'three/addons/controls/PointerLockControls.js';

// ---------- scene basics ----------
const scene = new THREE.Scene();
scene.background = new THREE.Color(0x1a1a22);
scene.fog = new THREE.Fog(0x1a1a22, 12, 28);

const camera = new THREE.PerspectiveCamera(72, innerWidth/innerHeight, 0.05, 100);
camera.position.set(0, 1.65, 4);

const renderer = new THREE.WebGLRenderer({ antialias:true });
renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
renderer.setSize(innerWidth, innerHeight);
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
document.body.appendChild(renderer.domElement);

addEventListener('resize', () => {
  camera.aspect = innerWidth/innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(innerWidth, innerHeight);
});

// ---------- lights ----------
scene.add(new THREE.AmbientLight(0xffffff, 0.35));

const warm = new THREE.PointLight(0xffd7a8, 1.2, 14, 1.6);
warm.position.set(-2.5, 2.7, -1);
warm.castShadow = true;
warm.shadow.mapSize.set(1024, 1024);
scene.add(warm);

const cool = new THREE.PointLight(0x9ab8ff, 0.6, 14, 1.6);
cool.position.set(2.5, 2.4, 2);
scene.add(cool);

const ceiling = new THREE.RectAreaLight(0xffffff, 0.3, 6, 6);
ceiling.position.set(0, 3.2, 0);
ceiling.lookAt(0, 0, 0);
scene.add(ceiling);

// ---------- room ----------
const ROOM = { w: 10, d: 10, h: 3.3 };

const floorMat = new THREE.MeshStandardMaterial({ color: 0x4a3e31, roughness: 0.85 });
const floor = new THREE.Mesh(new THREE.PlaneGeometry(ROOM.w, ROOM.d), floorMat);
floor.rotation.x = -Math.PI/2;
floor.receiveShadow = true;
scene.add(floor);

const boardLines = new THREE.Group();
for (let i = -ROOM.w/2 + 0.6; i < ROOM.w/2; i += 0.6) {
  const g = new THREE.PlaneGeometry(0.01, ROOM.d);
  const m = new THREE.MeshBasicMaterial({ color: 0x2a2218, transparent:true, opacity:0.5 });
  const line = new THREE.Mesh(g, m);
  line.rotation.x = -Math.PI/2;
  line.position.set(i, 0.001, 0);
  boardLines.add(line);
}
scene.add(boardLines);

const wallMat = new THREE.MeshStandardMaterial({ color: 0xe8e0d0, roughness: 0.95 });
const ceilMat = new THREE.MeshStandardMaterial({ color: 0xefe8d8, roughness: 0.95 });

function makeWall(w, h, pos, rotY) {
  const m = new THREE.Mesh(new THREE.PlaneGeometry(w, h), wallMat);
  m.position.copy(pos);
  m.rotation.y = rotY;
  m.receiveShadow = true;
  scene.add(m);
  return m;
}
makeWall(ROOM.w, ROOM.h, new THREE.Vector3(0, ROOM.h/2, -ROOM.d/2), 0);
makeWall(ROOM.w, ROOM.h, new THREE.Vector3(0, ROOM.h/2,  ROOM.d/2), Math.PI);
makeWall(ROOM.d, ROOM.h, new THREE.Vector3(-ROOM.w/2, ROOM.h/2, 0), Math.PI/2);
makeWall(ROOM.d, ROOM.h, new THREE.Vector3( ROOM.w/2, ROOM.h/2, 0), -Math.PI/2);

const ceilMesh = new THREE.Mesh(new THREE.PlaneGeometry(ROOM.w, ROOM.d), ceilMat);
ceilMesh.rotation.x = Math.PI/2;
ceilMesh.position.y = ROOM.h;
scene.add(ceilMesh);

// ---------- obstacles ----------
const obstacles = [];

function addBox(w, h, d, x, y, z, color, opts={}) {
  const mat = new THREE.MeshStandardMaterial({ color, roughness: opts.rough ?? 0.6, metalness: opts.metal ?? 0 });
  const mesh = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), mat);
  mesh.position.set(x, y, z);
  mesh.castShadow = true;
  mesh.receiveShadow = true;
  scene.add(mesh);
  obstacles.push(new THREE.Box3().setFromObject(mesh));
  return mesh;
}

// ---------- bed ----------
const bedGroup = new THREE.Group();
const bedFrame = new THREE.Mesh(new THREE.BoxGeometry(1.6, 0.35, 2.2), new THREE.MeshStandardMaterial({ color: 0x3a2a1f, roughness: 0.8 }));
bedFrame.position.set(0, 0.175, 0); bedFrame.castShadow = true; bedFrame.receiveShadow = true;
bedGroup.add(bedFrame);
const mattress = new THREE.Mesh(new THREE.BoxGeometry(1.5, 0.22, 2.05), new THREE.MeshStandardMaterial({ color: 0xf1eadb, roughness: 0.9 }));
mattress.position.set(0, 0.46, 0); mattress.castShadow = true; mattress.receiveShadow = true;
bedGroup.add(mattress);
const duvet = new THREE.Mesh(new THREE.BoxGeometry(1.52, 0.12, 1.4), new THREE.MeshStandardMaterial({ color: 0x6b7280, roughness: 0.9 }));
duvet.position.set(0, 0.62, 0.3); duvet.castShadow = true;
bedGroup.add(duvet);
const pillow = new THREE.Mesh(new THREE.BoxGeometry(1.3, 0.15, 0.4), new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.95 }));
pillow.position.set(0, 0.64, -0.75); pillow.castShadow = true;
bedGroup.add(pillow);
const headboard = new THREE.Mesh(new THREE.BoxGeometry(1.7, 0.9, 0.1), new THREE.MeshStandardMaterial({ color: 0x2a1e15, roughness: 0.7 }));
headboard.position.set(0, 0.7, -1.12); headboard.castShadow = true;
bedGroup.add(headboard);
bedGroup.position.set(-ROOM.w/2 + 1.0, 0, -1.5);
scene.add(bedGroup);
obstacles.push(new THREE.Box3().setFromObject(bedGroup));

// ---------- cabinet ----------
addBox(1.2, 1.4, 0.5, 2.5, 0.7, -ROOM.d/2 + 0.28, 0x6b4a30);
for (let i = 0; i < 3; i++) {
  const drawer = new THREE.Mesh(new THREE.BoxGeometry(1.05, 0.36, 0.02), new THREE.MeshStandardMaterial({ color: 0x4a3320, roughness: 0.7 }));
  drawer.position.set(2.5, 0.28 + i*0.42, -ROOM.d/2 + 0.55);
  scene.add(drawer);
  const handle = new THREE.Mesh(new THREE.BoxGeometry(0.18, 0.03, 0.04), new THREE.MeshStandardMaterial({ color: 0xd1a15a, metalness: 0.8, roughness: 0.3 }));
  handle.position.set(2.5, 0.28 + i*0.42, -ROOM.d/2 + 0.58);
  scene.add(handle);
}
const pot = new THREE.Mesh(new THREE.CylinderGeometry(0.12, 0.09, 0.18, 20), new THREE.MeshStandardMaterial({ color: 0x8a5a3a, roughness: 0.8 }));
pot.position.set(2.5, 1.49, -ROOM.d/2 + 0.28); pot.castShadow = true;
scene.add(pot);
const plant = new THREE.Mesh(new THREE.IcosahedronGeometry(0.22, 0), new THREE.MeshStandardMaterial({ color: 0x3f7a3a, roughness: 0.95, flatShading: true }));
plant.position.set(2.5, 1.75, -ROOM.d/2 + 0.28); plant.castShadow = true;
scene.add(plant);

// ---------- whiteboard ----------
const BOARD_W = 2.6, BOARD_H = 1.6;
const boardCanvas = document.createElement('canvas');
boardCanvas.width = 1024; boardCanvas.height = 640;
const bctx = boardCanvas.getContext('2d');
bctx.fillStyle = '#fafafa';
bctx.fillRect(0, 0, boardCanvas.width, boardCanvas.height);
bctx.fillStyle = '#888';
bctx.font = '28px -apple-system, Segoe UI, sans-serif';
bctx.fillText('press  E  to write', 380, 320);

const boardTex = new THREE.CanvasTexture(boardCanvas);
boardTex.colorSpace = THREE.SRGBColorSpace;
const boardMesh = new THREE.Mesh(new THREE.PlaneGeometry(BOARD_W, BOARD_H), new THREE.MeshStandardMaterial({ map: boardTex, roughness: 0.5 }));
boardMesh.position.set(ROOM.w/2 - 0.02, 1.7, 0);
boardMesh.rotation.y = -Math.PI/2;
scene.add(boardMesh);

const frameMat = new THREE.MeshStandardMaterial({ color: 0x2a2a2a, roughness: 0.4 });
const frameT = 0.08;
const frame1 = new THREE.Mesh(new THREE.BoxGeometry(0.03, BOARD_H + frameT*2, frameT), frameMat);
frame1.position.set(ROOM.w/2 - 0.01, 1.7, -BOARD_W/2 - frameT/2 + 0.02);
frame1.rotation.y = -Math.PI/2;
const frame2 = frame1.clone();
frame2.position.z = BOARD_W/2 + frameT/2 - 0.02;
const frame3 = new THREE.Mesh(new THREE.BoxGeometry(0.03, frameT, BOARD_W + frameT*2), frameMat);
frame3.position.set(ROOM.w/2 - 0.01, 1.7 + BOARD_H/2 + frameT/2, 0);
frame3.rotation.y = -Math.PI/2;
const frame4 = frame3.clone();
frame4.position.y = 1.7 - BOARD_H/2 - frameT/2;
scene.add(frame1, frame2, frame3, frame4);

// ---------- rug + lamp ----------
const rug = new THREE.Mesh(new THREE.PlaneGeometry(3.2, 2.2), new THREE.MeshStandardMaterial({ color: 0x7a2e2e, roughness: 0.95 }));
rug.rotation.x = -Math.PI/2; rug.position.set(0.2, 0.005, 1.0); rug.receiveShadow = true;
scene.add(rug);

const lampBase = new THREE.Mesh(new THREE.CylinderGeometry(0.15, 0.18, 0.05, 16), new THREE.MeshStandardMaterial({ color: 0x222, metalness: 0.5, roughness: 0.3 }));
lampBase.position.set(-3.5, 0.025, 3); scene.add(lampBase);
const lampPole = new THREE.Mesh(new THREE.CylinderGeometry(0.02, 0.02, 1.6, 8), new THREE.MeshStandardMaterial({ color: 0x222, metalness: 0.5 }));
lampPole.position.set(-3.5, 0.85, 3); scene.add(lampPole);
const lampShade = new THREE.Mesh(new THREE.ConeGeometry(0.25, 0.3, 16, 1, true), new THREE.MeshStandardMaterial({ color: 0xf4b860, side: THREE.DoubleSide, emissive: 0x8a4a10, emissiveIntensity:0.4 }));
lampShade.position.set(-3.5, 1.7, 3); scene.add(lampShade);
const lampLight = new THREE.PointLight(0xffc98a, 0.8, 5, 1.8);
lampLight.position.set(-3.5, 1.55, 3); scene.add(lampLight);

// ---------- touch detect ----------
const IS_TOUCH = ('ontouchstart' in window) || navigator.maxTouchPoints > 0;
if (IS_TOUCH) {
  document.body.classList.add('touch');
  document.querySelectorAll('.deskHelp').forEach(el => el.style.display = 'none');
  document.querySelectorAll('.touchHelp').forEach(el => el.style.display = 'block');
}

// ---------- controls ----------
const controls = new PointerLockControls(camera, renderer.domElement);
scene.add(controls.getObject());

let touchActive = false;
const startEl = document.getElementById('start');
startEl.addEventListener('click', () => {
  if (IS_TOUCH) { touchActive = true; startEl.style.display = 'none'; }
  else controls.lock();
});
controls.addEventListener('lock',   () => startEl.style.display = 'none');
controls.addEventListener('unlock', () => {
  if (!noteModal.classList.contains('on') && !boardModal.classList.contains('on')) startEl.style.display = 'flex';
});

function isActive() { return IS_TOUCH ? touchActive : controls.isLocked; }

// ---------- keys ----------
const keys = {};
addEventListener('keydown', e => {
  keys[e.code] = true;
  if (e.code === 'KeyN' && isActive()) openNoteModal();
  if (e.code === 'KeyE' && isActive() && nearBoard) openBoardModal();
});
addEventListener('keyup', e => keys[e.code] = false);

// ---------- touch UI ----------
const touchMove = { x: 0, y: 0 };
let touchRun = false;

(function setupStick() {
  const stick = document.getElementById('stick');
  const nub   = document.getElementById('stickNub');
  const R     = 55;
  let active = null, cx = 0, cy = 0;
  stick.addEventListener('pointerdown', e => {
    active = e.pointerId;
    const r = stick.getBoundingClientRect();
    cx = r.left + r.width/2; cy = r.top + r.height/2;
    stick.setPointerCapture(e.pointerId);
    updateNub(e.clientX, e.clientY);
  });
  stick.addEventListener('pointermove', e => {
    if (e.pointerId !== active) return;
    updateNub(e.clientX, e.clientY);
  });
  const end = e => {
    if (e.pointerId !== active) return;
    active = null; touchMove.x = 0; touchMove.y = 0;
    nub.style.transform = 'translate(0,0)';
  };
  stick.addEventListener('pointerup', end);
  stick.addEventListener('pointercancel', end);
  function updateNub(x, y) {
    let dx = x - cx, dy = y - cy;
    const d = Math.hypot(dx, dy);
    if (d > R) { dx = dx * R / d; dy = dy * R / d; }
    nub.style.transform = `translate(${dx}px, ${dy}px)`;
    touchMove.x = dx / R; touchMove.y = dy / R;
  }
})();

(function setupLook() {
  const pad = document.getElementById('lookPad');
  let pid = null, lx = 0, ly = 0;
  const SENS = 0.003;
  const obj = controls.getObject();
  pad.addEventListener('pointerdown', e => {
    pid = e.pointerId; lx = e.clientX; ly = e.clientY;
    pad.setPointerCapture(e.pointerId);
  });
  pad.addEventListener('pointermove', e => {
    if (e.pointerId !== pid || !isActive()) return;
    const dx = e.clientX - lx, dy = e.clientY - ly;
    lx = e.clientX; ly = e.clientY;
    obj.rotation.y -= dx * SENS;
    camera.rotation.x -= dy * SENS;
    camera.rotation.x = Math.max(-Math.PI/2 + 0.01, Math.min(Math.PI/2 - 0.01, camera.rotation.x));
  });
  const end = e => { if (e.pointerId === pid) pid = null; };
  pad.addEventListener('pointerup', end);
  pad.addEventListener('pointercancel', end);
})();

document.getElementById('btnN').addEventListener('click', () => { if (isActive()) openNoteModal(); });
document.getElementById('btnE').addEventListener('click', () => { if (isActive() && nearBoard) openBoardModal(); });
document.getElementById('btnRun').addEventListener('click', e => {
  touchRun = !touchRun;
  e.currentTarget.classList.toggle('on', touchRun);
});

const velocity = new THREE.Vector3();
const direction = new THREE.Vector3();
const PLAYER_R = 0.35;

function collide(next) {
  const p = new THREE.Vector3(next.x, 0.6, next.z);
  const sphere = new THREE.Sphere(p, PLAYER_R);
  for (const b of obstacles) if (b.intersectsSphere(sphere)) return true;
  if (Math.abs(next.x) > ROOM.w/2 - PLAYER_R) return true;
  if (Math.abs(next.z) > ROOM.d/2 - PLAYER_R) return true;
  return false;
}

// ---------- notes ----------
const noteModal = document.getElementById('noteModal');
const noteText  = document.getElementById('noteText');
document.getElementById('noteCancel').onclick = closeNoteModal;
document.getElementById('noteOk').onclick = placeNote;
noteText.addEventListener('keydown', e => {
  if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); placeNote(); }
  if (e.key === 'Escape') closeNoteModal();
});

function openNoteModal() {
  if (!IS_TOUCH) controls.unlock();
  noteModal.classList.add('on');
  setTimeout(() => noteText.focus(), 30);
}
function closeNoteModal() {
  noteModal.classList.remove('on');
  noteText.value = '';
  if (!IS_TOUCH) controls.lock();
}

const notes = [];
function placeNote() {
  const text = noteText.value.trim();
  if (!text) { closeNoteModal(); return; }
  const c = document.createElement('canvas');
  c.width = 512; c.height = 512;
  const ctx = c.getContext('2d');
  ctx.fillStyle = pickNoteColor();
  ctx.fillRect(0, 0, 512, 512);
  ctx.fillStyle = 'rgba(220,220,220,0.55)';
  ctx.fillRect(180, 10, 150, 28);
  ctx.fillStyle = '#222';
  ctx.font = '36px "Comic Sans MS", "Segoe Script", cursive';
  ctx.textBaseline = 'top';
  wrapText(ctx, text, 40, 70, 432, 48);
  const tex = new THREE.CanvasTexture(c);
  tex.colorSpace = THREE.SRGBColorSpace;
  const note = new THREE.Mesh(new THREE.PlaneGeometry(0.45, 0.45), new THREE.MeshStandardMaterial({ map: tex, side: THREE.DoubleSide, roughness: 0.9 }));
  const forward = new THREE.Vector3();
  camera.getWorldDirection(forward);
  const pos = camera.position.clone().add(forward.multiplyScalar(1.4));
  pos.y = Math.max(0.5, Math.min(ROOM.h - 0.4, pos.y));
  note.position.copy(pos);
  note.lookAt(camera.position);
  note.rotation.z = (Math.random() - 0.5) * 0.2;
  scene.add(note);
  notes.push(note);
  closeNoteModal();
}

function pickNoteColor() {
  const palette = ['#fff59d','#ffe0a8','#ffb3b3','#b3e5fc','#c8f7c5','#fff59d'];
  return palette[Math.floor(Math.random()*palette.length)];
}

function wrapText(ctx, text, x, y, maxW, lh) {
  const words = text.split(/\s+/);
  let line = '', yy = y;
  for (const w of words) {
    const test = line ? line + ' ' + w : w;
    if (ctx.measureText(test).width > maxW && line) {
      ctx.fillText(line, x, yy);
      line = w; yy += lh;
      if (yy > 460) { ctx.fillText(line + '…', x, yy); return; }
    } else { line = test; }
  }
  if (line) ctx.fillText(line, x, yy);
}

// ---------- whiteboard drawing ----------
const boardModal = document.getElementById('boardModal');
const bigCanvas = document.getElementById('boardCanvas');
const bigCtx = bigCanvas.getContext('2d');
let drawColor = '#1a1a1a';
let drawing = false;
let lastPt = null;
let erasing = false;

function syncFromBoard() { bigCtx.drawImage(boardCanvas, 0, 0); }
function syncToBoard()   { bctx.drawImage(bigCanvas, 0, 0); boardTex.needsUpdate = true; }

document.querySelectorAll('#boardModal .swatch').forEach(sw => {
  sw.onclick = () => {
    document.querySelectorAll('#boardModal .swatch').forEach(s => s.classList.remove('active'));
    sw.classList.add('active');
    drawColor = sw.dataset.color;
    erasing = false;
  };
});
document.getElementById('boardErase').onclick = () => erasing = true;
document.getElementById('boardClear').onclick = () => {
  bigCtx.fillStyle = '#fafafa';
  bigCtx.fillRect(0, 0, bigCanvas.width, bigCanvas.height);
};
document.getElementById('boardClose').onclick = () => {
  syncToBoard();
  boardModal.classList.remove('on');
  if (!IS_TOUCH) controls.lock();
};

function boardPt(e) {
  const r = bigCanvas.getBoundingClientRect();
  const cx = e.touches ? e.touches[0].clientX : e.clientX;
  const cy = e.touches ? e.touches[0].clientY : e.clientY;
  return { x: (cx - r.left) * (bigCanvas.width / r.width), y: (cy - r.top) * (bigCanvas.height / r.height) };
}
function startDraw(e) { e.preventDefault(); drawing = true; lastPt = boardPt(e); }
function moveDraw(e) {
  if (!drawing) return;
  e.preventDefault();
  const p = boardPt(e);
  bigCtx.strokeStyle = erasing ? '#fafafa' : drawColor;
  bigCtx.lineWidth = erasing ? 30 : 4;
  bigCtx.lineCap = 'round'; bigCtx.lineJoin = 'round';
  bigCtx.beginPath();
  bigCtx.moveTo(lastPt.x, lastPt.y);
  bigCtx.lineTo(p.x, p.y);
  bigCtx.stroke();
  lastPt = p;
}
function endDraw() { drawing = false; }

bigCanvas.addEventListener('mousedown', startDraw);
bigCanvas.addEventListener('mousemove', moveDraw);
addEventListener('mouseup', endDraw);
bigCanvas.addEventListener('touchstart', startDraw, { passive:false });
bigCanvas.addEventListener('touchmove', moveDraw,  { passive:false });
addEventListener('touchend', endDraw);

function openBoardModal() {
  if (!IS_TOUCH) controls.unlock();
  syncFromBoard();
  boardModal.classList.add('on');
}

// ---------- proximity ----------
const promptEl = document.getElementById('prompt');
let nearBoard = false;
function checkBoardProximity() {
  const dx = camera.position.x - (ROOM.w/2 - 0.02);
  const dz = camera.position.z;
  const dist = Math.hypot(dx, dz);
  const yOk = Math.abs(camera.position.y - 1.7) < 1.2;
  const inZ = Math.abs(dz) < BOARD_W/2 + 0.4;
  nearBoard = dist < 1.6 && inZ && yOk;
  promptEl.classList.toggle('on', nearBoard && isActive() && !IS_TOUCH);
  document.getElementById('btnE').classList.toggle('on', nearBoard && isActive() && IS_TOUCH);
}

// ---------- loop ----------
const clock = new THREE.Clock();
function animate() {
  const dt = Math.min(clock.getDelta(), 0.1);
  if (isActive()) {
    const running = keys['ShiftLeft'] || keys['ShiftRight'] || touchRun;
    const speed = running ? 6.5 : 3.2;
    direction.set(0, 0, 0);
    if (keys['KeyW'] || keys['ArrowUp'])    direction.z -= 1;
    if (keys['KeyS'] || keys['ArrowDown'])  direction.z += 1;
    if (keys['KeyA'] || keys['ArrowLeft'])  direction.x -= 1;
    if (keys['KeyD'] || keys['ArrowRight']) direction.x += 1;
    if (IS_TOUCH) { direction.x += touchMove.x; direction.z += touchMove.y; }
    if (direction.lengthSq() > 0) direction.normalize();
    velocity.x -= velocity.x * 10 * dt;
    velocity.z -= velocity.z * 10 * dt;
    velocity.x += direction.x * speed * 10 * dt;
    velocity.z += direction.z * speed * 10 * dt;
    const obj = controls.getObject();
    const before = obj.position.clone();
    controls.moveRight(velocity.x * dt);
    if (collide(obj.position)) obj.position.x = before.x;
    controls.moveForward(-velocity.z * dt);
    if (collide(obj.position)) obj.position.z = before.z;
    for (const n of notes) n.lookAt(camera.position);
  }
  checkBoardProximity();
  renderer.render(scene, camera);
  requestAnimationFrame(animate);
}
animate();
