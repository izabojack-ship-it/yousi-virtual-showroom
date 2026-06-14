/**
 * 街景沉浸式步行導覽（Google Street View 概念）
 * - 點擊地面箭頭 → 相機向前/向後步行，場景交叉淡化
 * - 預載相鄰視角，步行中禁用環顧
 */
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { CSS2DRenderer, CSS2DObject } from 'three/addons/renderers/CSS2DRenderer.js';
import {
  createTechPhotoMaterial,
  injectTechHud,
  isTechMaterial,
  setPhotoMaterialOpacity,
  updateTechMaterialTime,
} from './showroom-tech-shader.js';

const PHOTO_DIST = 100;
const LOOK_MARGIN = 0.18;
const WALK_FORWARD_MS = 1200;
const WALK_BACKWARD_MS = 950;
const WALK_CAM_FORWARD = 32;
const WALK_SCENE_GAP = 50;
const INSPECT_ZOOM_RATIO = 0.72;
const ZOOM_MIN = 8;
const ZOOM_MAX = PHOTO_DIST;

function el(tag, className, html = '') {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (html) node.innerHTML = html;
  return node;
}

function easeInOutCubic(t) {
  return t < 0.5 ? 4 * t * t * t : 1 - ((-2 * t + 2) ** 3) / 2;
}

function buildGlassPanel(anchor) {
  const panel = el('div', 'sv-dt-panel');
  const accent = anchor.accent || '#00ffff';
  panel.style.setProperty('--sv-accent', accent);
  panel.innerHTML = `
    <div class="sv-dt-title">${anchor.title}</div>
    ${anchor.subtitle ? `<div class="sv-dt-sub">${anchor.subtitle}</div>` : ''}
    <dl class="sv-dt-rows">
      ${(anchor.rows || []).map((r) => `
        <div class="sv-dt-row">
          <dt>${r.label}</dt>
          <dd class="sv-dt-${r.status || 'neutral'}">${r.value}</dd>
        </div>`).join('')}
    </dl>`;
  return panel;
}

function prepareTexture(texture, renderer) {
  texture.colorSpace = THREE.SRGBColorSpace;
  texture.generateMipmaps = true;
  texture.minFilter = THREE.LinearMipmapLinearFilter;
  texture.magFilter = THREE.LinearFilter;
  texture.needsUpdate = true;
  const maxAniso = renderer?.capabilities?.getMaxAnisotropy?.() ?? 1;
  texture.anisotropy = Math.min(16, maxAniso);
  return texture;
}

function coverPlaneSize(camera, viewW, viewH, imgW, imgH) {
  const vFov = THREE.MathUtils.degToRad(camera.fov);
  const viewAspect = viewW / Math.max(viewH, 1);
  const imgAspect = imgW / Math.max(imgH, 1);
  const visibleH = 2 * Math.tan(vFov / 2) * PHOTO_DIST;
  const visibleW = visibleH * viewAspect;
  if (viewAspect >= imgAspect) {
    return { w: visibleW, h: visibleW / imgAspect };
  }
  return { h: visibleH, w: visibleH * imgAspect };
}

function buildPhotoMesh(texture, camera, viewW, viewH, renderer, opacity = 1, techEnhance = false) {
  prepareTexture(texture, renderer);
  const img = texture.image;
  const iw = img?.width || 4;
  const ih = img?.height || 3;
  const { w, h } = coverPlaneSize(camera, viewW, viewH, iw, ih);
  const geo = new THREE.PlaneGeometry(w, h);
  const mat = techEnhance
    ? createTechPhotoMaterial(texture, { opacity })
    : new THREE.MeshBasicMaterial({
      map: texture,
      transparent: opacity < 1,
      opacity,
      depthWrite: opacity >= 0.99,
    });
  const mesh = new THREE.Mesh(geo, mat);
  mesh.position.set(0, 0, -PHOTO_DIST);
  return mesh;
}

function disposePhotoMesh(m, disposeTexture = false) {
  if (!m) return;
  m.geometry?.dispose();
  const mat = m.material;
  if (!mat) return;
  const map = isTechMaterial(mat) ? mat.uniforms?.map?.value : mat.map;
  if (disposeTexture && map) map.dispose();
  mat.dispose();
}

function applyOrbitLimits(controls) {
  controls.minAzimuthAngle = -LOOK_MARGIN;
  controls.maxAzimuthAngle = LOOK_MARGIN;
  controls.minPolarAngle = Math.PI / 2 - LOOK_MARGIN;
  controls.maxPolarAngle = Math.PI / 2 + LOOK_MARGIN;
}

function getMeshPlaneSize(mesh) {
  if (mesh?.geometry?.parameters) {
    return { w: mesh.geometry.parameters.width, h: mesh.geometry.parameters.height };
  }
  return { w: 80, h: 60 };
}

function createGroundWalkMarker(link, onWalk, isForward) {
  const wrap = el('button', 'sv-marker sv-marker-walk sv-ground-arrow');
  wrap.type = 'button';
  wrap.title = link.sign || link.label;
  const chevronClass = isForward ? 'sv-ground-forward' : 'sv-ground-backward';
  wrap.innerHTML = `
    <div class="sv-ground-disk">
      <div class="sv-ground-pulse"></div>
      <div class="sv-ground-chevron ${chevronClass}"></div>
    </div>
    <span class="sv-ground-label">${link.sign || link.label}</span>`;
  wrap.addEventListener('click', (e) => {
    e.preventDefault();
    e.stopPropagation();
    onWalk(link.target, isForward);
  });
  return new CSS2DObject(wrap);
}

function createGroundExitMarker(exit) {
  const wrap = el('a', 'sv-marker sv-marker-exit sv-ground-exit');
  wrap.href = exit.url;
  wrap.title = exit.label;
  wrap.innerHTML = `
    <div class="sv-ground-exit-disk">
      <span class="sv-ground-exit-icon">➜</span>
    </div>
    <span class="sv-ground-exit-label">
      <span class="sv-ground-exit-tag">路標</span>${exit.label}
    </span>`;
  return new CSS2DObject(wrap);
}

function placeGroundMarker(obj, yawDeg, planeW, planeH, lane = 0) {
  const yaw = THREE.MathUtils.degToRad(yawDeg);
  const groundY = -planeH * 0.30;
  const depth = -PHOTO_DIST + 10;
  const lateralDist = planeW * 0.16;
  const x = Math.sin(yaw) * lateralDist + lane * planeW * 0.1;
  const z = depth + Math.cos(yaw) * planeH * 0.06;
  obj.position.set(x, groundY, z);
}

function clearGroup(group) {
  while (group.children.length) group.remove(group.children[0]);
}

function buildCenterNavDock(wrap) {
  const dock = el('div', 'sv-center-dock');
  dock.innerHTML = `
    <div class="sv-center-scene">
      <span class="sv-center-label"></span>
      <span class="sv-center-counter"></span>
    </div>
    <div class="sv-center-nav" role="navigation" aria-label="環景導覽">
      <button type="button" class="sv-center-btn" data-nav="prev" title="步行返回">
        <span class="sv-center-btn-icon">‹</span>
        <span class="sv-center-btn-text">步行返回</span>
      </button>
      <button type="button" class="sv-center-btn sv-center-btn-primary" data-nav="forward" title="沿動線步行前進">
        <span class="sv-center-btn-icon">👣</span>
        <span class="sv-center-btn-text">步行前進</span>
      </button>
      <button type="button" class="sv-center-btn" data-nav="next" title="下一視角">
        <span class="sv-center-btn-text">下一視角</span>
        <span class="sv-center-btn-icon">›</span>
      </button>
    </div>
    <p class="sv-center-hint">滾輪或 + 放大檢視 · 放大時自動隱藏 AR 標籤</p>
    <div class="sv-center-exits"></div>`;
  wrap.appendChild(dock);
  return dock;
}

function updateCenterDock(dock, sceneData, scenes, idx, exitList) {
  if (!dock) return;
  const labelEl = dock.querySelector('.sv-center-label');
  const counterEl = dock.querySelector('.sv-center-counter');
  const forwardBtn = dock.querySelector('[data-nav="forward"]');
  const prevBtn = dock.querySelector('[data-nav="prev"]');
  const nextBtn = dock.querySelector('[data-nav="next"]');
  const exitsEl = dock.querySelector('.sv-center-exits');

  const data = scenes[idx];
  const forwardLink = (sceneData.links || []).find((l) => l.target === idx + 1);
  const backLink = (sceneData.links || []).find((l) => l.target === idx - 1);

  if (labelEl) labelEl.textContent = data.label;
  if (counterEl) counterEl.textContent = `${idx + 1} / ${scenes.length}`;

  if (prevBtn) {
    prevBtn.disabled = idx <= 0;
    const t = prevBtn.querySelector('.sv-center-btn-text');
    if (t) t.textContent = backLink?.sign?.replace('← ', '') || '步行返回';
  }
  if (nextBtn) nextBtn.disabled = idx >= scenes.length - 1;
  if (forwardBtn) {
    forwardBtn.disabled = idx >= scenes.length - 1;
    const t = forwardBtn.querySelector('.sv-center-btn-text');
    if (t) t.textContent = forwardLink?.sign?.replace(' →', '') || '步行前進';
  }

  if (exitsEl) {
    exitsEl.innerHTML = (exitList || []).map((exit) => `
      <a class="sv-center-exit" href="${exit.url}">
        <span class="sv-center-exit-tag">路標</span>${exit.label}
      </a>`).join('');
  }
}

export function initStreetViewTour(container, tourConfig, options = {}) {
  if (!container || !tourConfig?.scenes?.length) return null;

  const { scenes, exits = [], zoneTitle = '' } = tourConfig;
  const digitalTwins = options.showDigitalTwins === true ? (options.digitalTwins || []) : [];
  const showDigitalTwins = digitalTwins.length > 0;
  const vrMode = options.vrMode === true;
  const techEnhance = options.techMode === true;

  let index = 0;
  let mesh = null;
  let currentTexture = null;
  let viewSize = { w: 0, h: 0 };
  let animId = null;
  let transitioning = false;
  let twinsUserEnabled = showDigitalTwins;
  let guidesUserEnabled = true;
  const textureCache = new Map();
  const twinGroup = new THREE.Group();
  const markerGroup = new THREE.Group();

  const wrap = el('div', vrMode ? 'sv-wrap sv-vr-mode sv-refined-mode' : 'sv-wrap sv-refined-mode');
  if (techEnhance) wrap.classList.add('sv-tech-mode');
  if (!showDigitalTwins) wrap.classList.add('sv-no-twins');

  if (vrMode) {
    wrap.innerHTML = `
      <div class="sv-canvas-host sv-canvas-vr">
        <div class="sv-refined-vignette"></div>
      </div>
      <div class="sv-inspect-badge">🔍 檢視模式 · 雙擊恢復 · AR 已隱藏（導覽路標仍顯示）</div>
      <div class="sv-walk-overlay" hidden>
        <div class="sv-walk-bar"><div class="sv-walk-bar-fill"></div></div>
        <span class="sv-walk-status">步行中…</span>
      </div>`;
  } else {
    wrap.innerHTML = `
    <div class="sv-hud-top">
      <div class="sv-location">
        <span class="sv-location-badge">${techEnhance ? 'SMART FACTORY · 360°' : 'STREET VIEW'}</span>
        <span class="sv-location-zone">${zoneTitle}</span>
      </div>
      <div class="sv-compass" title="拖曳環顧">⊙ 環顧</div>
    </div>
    <div class="sv-canvas-host">
      <div class="sv-refined-vignette"></div>
    </div>
    <div class="sv-inspect-badge">🔍 檢視模式 · 雙擊恢復 · AR 已隱藏（導覽路標仍顯示）</div>
    <div class="sv-walk-overlay" hidden>
      <div class="sv-walk-bar"><div class="sv-walk-bar-fill"></div></div>
      <span class="sv-walk-status">步行中…</span>
    </div>`;
  }
  container.appendChild(wrap);

  const host = wrap.querySelector('.sv-canvas-host');
  if (techEnhance) injectTechHud(host, 'ORIGINAL · SHARP');
  const walkOverlay = wrap.querySelector('.sv-walk-overlay');
  const walkBarFill = wrap.querySelector('.sv-walk-bar-fill');
  const walkStatus = wrap.querySelector('.sv-walk-status');
  const centerDock = buildCenterNavDock(wrap);

  const zoomTools = el('div', 'sv-zoom-tools');
  zoomTools.innerHTML = `
    <button type="button" class="sv-zoom-btn" data-zoom="in" title="放大檢視">+</button>
    <button type="button" class="sv-zoom-btn" data-zoom="out" title="縮小">−</button>
    <button type="button" class="sv-zoom-btn" data-zoom="reset" title="恢復視野">⊙</button>
    ${showDigitalTwins ? '<button type="button" class="sv-zoom-btn sv-ar-toggle active" id="svArToggle" title="AR 遙測面板">AR</button>' : ''}
    <button type="button" class="sv-zoom-btn sv-guide-toggle active" id="svGuideToggle" title="地面導覽與路標">導覽</button>`;
  wrap.appendChild(zoomTools);

  centerDock.querySelectorAll('[data-nav]').forEach((btn) => {
    btn.addEventListener('click', () => {
      if (btn.dataset.nav === 'prev' && index > 0) walkToScene(index - 1, false);
      if (btn.dataset.nav === 'next' && index < scenes.length - 1) walkToScene(index + 1, true);
      if (btn.dataset.nav === 'forward' && index < scenes.length - 1) walkToScene(index + 1, true);
    });
  });

  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0x080810);
  const camera = new THREE.PerspectiveCamera(68, 16 / 10, 0.1, 1000);
  camera.position.set(0, 0, 0);

  const renderer = new THREE.WebGLRenderer({ antialias: true, powerPreference: 'high-performance' });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2.5));
  host.insertBefore(renderer.domElement, host.firstChild);

  const labelRenderer = new CSS2DRenderer();
  labelRenderer.domElement.className = 'sv-label-layer';
  host.appendChild(labelRenderer.domElement);

  const controls = new OrbitControls(camera, renderer.domElement);
  controls.enableZoom = true;
  controls.zoomSpeed = 0.85;
  controls.enablePan = false;
  controls.rotateSpeed = -0.28;
  controls.enableDamping = true;
  controls.dampingFactor = 0.1;
  controls.minDistance = ZOOM_MIN;
  controls.maxDistance = ZOOM_MAX;
  controls.target.set(0, 0, -PHOTO_DIST);
  applyOrbitLimits(controls);

  function getViewDistance() {
    return camera.position.distanceTo(controls.target);
  }

  function resetView() {
    camera.position.set(0, 0, 0);
    controls.target.set(0, 0, -PHOTO_DIST);
    controls.update();
    applyOrbitLimits(controls);
    updateInspectMode();
  }

  function updateInspectMode() {
    const ratio = getViewDistance() / PHOTO_DIST;
    const inspecting = ratio < INSPECT_ZOOM_RATIO;
    wrap.classList.toggle('sv-inspect-mode', inspecting);
    /* 放大時只隱藏 AR 遙測面板；地面箭頭與路標保留 */
    twinGroup.visible = twinsUserEnabled && !inspecting && !transitioning;
    markerGroup.visible = guidesUserEnabled && !transitioning;
    centerDock?.classList.toggle('sv-dock-minimal', false);
  }

  zoomTools.querySelectorAll('[data-zoom]').forEach((btn) => {
    btn.addEventListener('click', () => {
      const dist = getViewDistance();
      if (btn.dataset.zoom === 'in') {
        const dir = camera.position.clone().sub(controls.target).normalize();
        camera.position.copy(controls.target).add(dir.multiplyScalar(Math.max(ZOOM_MIN, dist * 0.82)));
      }
      if (btn.dataset.zoom === 'out') {
        const dir = camera.position.clone().sub(controls.target).normalize();
        camera.position.copy(controls.target).add(dir.multiplyScalar(Math.min(ZOOM_MAX, dist * 1.18)));
      }
      if (btn.dataset.zoom === 'reset') {
        resetView();
        return;
      }
      updateInspectMode();
    });
  });

  const arToggle = zoomTools.querySelector('#svArToggle');
  arToggle?.addEventListener('click', () => {
    twinsUserEnabled = !twinsUserEnabled;
    arToggle.classList.toggle('active', twinsUserEnabled);
    updateInspectMode();
  });

  const guideToggle = zoomTools.querySelector('#svGuideToggle');
  guideToggle?.addEventListener('click', () => {
    guidesUserEnabled = !guidesUserEnabled;
    guideToggle.classList.toggle('active', guidesUserEnabled);
    updateInspectMode();
  });

  controls.addEventListener('change', updateInspectMode);
  renderer.domElement.addEventListener('dblclick', () => {
    resetView();
  });

  scene.add(twinGroup);
  scene.add(markerGroup);

  const loader = new THREE.TextureLoader();

  function loadTexture(url) {
    if (textureCache.has(url)) {
      return Promise.resolve(textureCache.get(url));
    }
    return new Promise((resolve, reject) => {
      loader.load(url, (texture) => {
        prepareTexture(texture, renderer);
        textureCache.set(url, texture);
        resolve(texture);
      }, undefined, reject);
    });
  }

  function preloadAdjacent(i) {
    [i - 1, i + 1].forEach((j) => {
      if (j >= 0 && j < scenes.length) {
        loadTexture(scenes[j].url).catch(() => {});
      }
    });
  }

  function rebuildPhotoMesh(resetControls = false) {
    if (!currentTexture || viewSize.w < 1) return;
    if (mesh) {
      scene.remove(mesh);
      disposePhotoMesh(mesh);
    }
    mesh = buildPhotoMesh(currentTexture, camera, viewSize.w, viewSize.h, renderer, 1, techEnhance);
    scene.add(mesh);
    rebuildGroundMarkers(index);
    if (resetControls) {
      resetView();
    }
  }

  function resize() {
    if (transitioning) return;
    const w = Math.max(1, host.clientWidth || container.clientWidth || window.innerWidth);
    const h = vrMode
      ? Math.max(1, host.clientHeight || container.clientHeight || window.innerHeight)
      : Math.max(360, Math.round(w * 0.62));
    if (!vrMode) host.style.height = `${h}px`;
    viewSize = { w, h };
    renderer.setSize(w, h, false);
    labelRenderer.setSize(w, h);
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
    rebuildPhotoMesh(false);
  }

  function updateDock(i) {
    updateCenterDock(centerDock, scenes[i], scenes, i, exits);
    if (vrMode && options.onSceneChange) {
      options.onSceneChange(scenes[i], i, scenes.length);
    }
  }

  function rebuildGroundMarkers(sceneIndex) {
    clearGroup(markerGroup);
    if (!mesh) return;
    const { w, h } = getMeshPlaneSize(mesh);
    const sceneData = scenes[sceneIndex];

    (sceneData.links || []).forEach((link) => {
      const isForward = link.target > sceneIndex;
      const obj = createGroundWalkMarker(link, walkToScene, isForward);
      const yaw = link.yaw ?? (isForward ? 0 : 180);
      placeGroundMarker(obj, yaw, w, h, isForward ? 0 : -0.4);
      markerGroup.add(obj);
    });

    exits.forEach((exit, i) => {
      const obj = createGroundExitMarker(exit);
      placeGroundMarker(obj, exit.yaw ?? 45, w, h, 0.7 + i * 0.55);
      markerGroup.add(obj);
    });
  }

  function rebuildTwins() {
    while (twinGroup.children.length) twinGroup.remove(twinGroup.children[0]);
    if (!showDigitalTwins) return;
    digitalTwins.forEach((t) => {
      const panel = buildGlassPanel(t);
      const obj = new CSS2DObject(panel);
      obj.position.set((t.position[0] ?? 0) * 22, t.position[1] ?? 1, -PHOTO_DIST + 18);
      twinGroup.add(obj);
    });
  }

  function setWalkUi(active, progress = 0, label = '步行中…') {
    if (walkOverlay) walkOverlay.hidden = !active;
    if (walkBarFill) walkBarFill.style.width = `${Math.round(progress * 100)}%`;
    if (walkStatus) walkStatus.textContent = label;
    wrap.classList.toggle('sv-walking', active);
    centerDock.style.opacity = active ? '0.35' : '1';
    centerDock.style.pointerEvents = active ? 'none' : '';
  }

  async function walkToScene(targetIndex, isForward) {
    if (transitioning || targetIndex === index) return;
    if (targetIndex < 0 || targetIndex >= scenes.length) return;

    transitioning = true;
    controls.enabled = false;
    markerGroup.visible = false;
    twinGroup.visible = false;
    setWalkUi(true, 0, isForward ? '沿動線步行前進…' : '返回上一視角…');
    host.classList.add('sv-walk-motion');

    let incomingMesh = null;
    try {
      const targetTexture = await loadTexture(scenes[targetIndex].url);
      incomingMesh = buildPhotoMesh(targetTexture, camera, viewSize.w, viewSize.h, renderer, 0, techEnhance);
      incomingMesh.material.depthWrite = false;

      const duration = isForward ? WALK_FORWARD_MS : WALK_BACKWARD_MS;
      const startCam = camera.position.clone();
      const startMeshZ = mesh.position.z;
      const label = scenes[targetIndex].label;

      if (isForward) {
        incomingMesh.position.z = -PHOTO_DIST - WALK_SCENE_GAP;
      } else {
        incomingMesh.position.z = -PHOTO_DIST + 18;
        incomingMesh.scale.set(1.06, 1.06, 1);
      }
      scene.add(incomingMesh);

      await new Promise((resolve) => {
        const t0 = performance.now();
        const tick = (now) => {
          const raw = Math.min(1, (now - t0) / duration);
          const t = easeInOutCubic(raw);

          if (isForward) {
            camera.position.z = t * WALK_CAM_FORWARD;
            camera.position.y = Math.sin(t * Math.PI * 4) * 0.22 * (1 - t * 0.6);
            mesh.position.z = startMeshZ + t * 20;
            setPhotoMaterialOpacity(mesh.material, 1 - t);
            mesh.material.transparent = true;
            incomingMesh.position.z = -PHOTO_DIST - WALK_SCENE_GAP + t * (WALK_SCENE_GAP + 22);
            setPhotoMaterialOpacity(incomingMesh.material, Math.min(1, t * 1.15));
          } else {
            camera.position.z = -t * 14;
            camera.position.y = Math.sin(t * Math.PI * 3) * 0.15 * (1 - t);
            mesh.position.z = startMeshZ + t * 25;
            setPhotoMaterialOpacity(mesh.material, 1 - t * 0.9);
            mesh.material.transparent = true;
            incomingMesh.position.z = -PHOTO_DIST + 18 * (1 - t);
            setPhotoMaterialOpacity(incomingMesh.material, t);
            const s = 1.06 - t * 0.06;
            incomingMesh.scale.set(s, s, 1);
          }

          setWalkUi(true, raw, raw < 0.5
            ? (isForward ? '沿動線步行前進…' : '返回上一視角…')
            : `抵達：${label}`);

          if (raw < 1) {
            requestAnimationFrame(tick);
          } else {
            resolve();
          }
        };
        requestAnimationFrame(tick);
      });

      scene.remove(mesh);
      disposePhotoMesh(mesh);

      mesh = incomingMesh;
      mesh.position.set(0, 0, -PHOTO_DIST);
      mesh.scale.set(1, 1, 1);
      setPhotoMaterialOpacity(mesh.material, 1);
      mesh.material.transparent = false;
      mesh.material.depthWrite = true;

      camera.position.copy(startCam);
      camera.position.set(0, 0, 0);

      index = targetIndex;
      currentTexture = targetTexture;
      updateDock(index);
      preloadAdjacent(index);
      rebuildGroundMarkers(index);

      resetView();
    } catch (err) {
      console.error('[streetview] 步行切換失敗:', err);
      if (incomingMesh) {
        scene.remove(incomingMesh);
        disposePhotoMesh(incomingMesh, false);
      }
    } finally {
      controls.enabled = true;
      host.classList.remove('sv-walk-motion');
      setWalkUi(false);
      transitioning = false;
      updateInspectMode();
    }
  }

  function showScene(i, resetControls = true) {
    index = ((i % scenes.length) + scenes.length) % scenes.length;
    updateDock(index);

    loadTexture(scenes[index].url).then((texture) => {
      currentTexture = texture;
      rebuildPhotoMesh(resetControls);
      preloadAdjacent(index);
    }).catch((err) => {
      console.error('[streetview] 無法載入環景照片:', scenes[index].url, err);
    });
  }

  function onKeyDown(e) {
    if (transitioning) return;
    if (e.key === 'ArrowLeft' && index > 0) walkToScene(index - 1, false);
    if (e.key === 'ArrowRight' && index < scenes.length - 1) walkToScene(index + 1, true);
  }
  window.addEventListener('keydown', onKeyDown);

  function animate() {
    animId = requestAnimationFrame(animate);
    const t = performance.now() * 0.001;
    scene.traverse((obj) => {
      if (obj.material && isTechMaterial(obj.material)) {
        updateTechMaterialTime(obj.material, t);
      }
    });
    if (!transitioning) {
      twinGroup.children.forEach((c, i) => {
        c.position.y = (digitalTwins[i]?.position[1] ?? 1) + Math.sin(t * 1.2 + i) * 0.06;
      });
      markerGroup.children.forEach((c, i) => {
        if (c.element?.classList.contains('sv-ground-arrow')) {
          c.position.y = getMeshPlaneSize(mesh).h * -0.30 + Math.sin(t * 2.2 + i) * 0.35;
        }
      });
    }
    controls.update();
    renderer.render(scene, camera);
    labelRenderer.render(scene, camera);
    updateInspectMode();
  }

  const ro = new ResizeObserver(resize);
  ro.observe(host);
  ro.observe(container);
  resize();
  rebuildTwins();
  showScene(0);
  resetView();
  animate();

  return {
    destroy() {
      cancelAnimationFrame(animId);
      window.removeEventListener('keydown', onKeyDown);
      ro.disconnect();
      textureCache.forEach((t) => t.dispose());
      textureCache.clear();
      renderer.dispose();
      wrap.remove();
    },
  };
}

export function initImmersiveTour(container, imageUrls, options = {}) {
  const tourConfig = {
    zoneTitle: options.title || '',
    scenes: (imageUrls || []).map((url, i, arr) => ({
      id: i,
      url,
      label: i === 0 ? '起點' : i === arr.length - 1 ? '終點' : `視角 ${i + 1}`,
      links: [
        ...(i > 0 ? [{ type: 'walk', target: i - 1, label: '返回', sign: '← 返回' }] : []),
        ...(i < arr.length - 1 ? [{ type: 'walk', target: i + 1, label: '前進', sign: '沿動線前進 →' }] : []),
      ],
    })),
    exits: options.exits || [],
  };
  return initStreetViewTour(container, tourConfig, { techMode: false, refinedMode: true, ...options });
}
