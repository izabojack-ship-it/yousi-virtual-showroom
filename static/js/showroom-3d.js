/**
 * 優思國際 × 金享 — PopRealAR Three.js 3D 控制邏輯
 * 虛擬空間預設為「工廠車間」場景：環氧地坪、產線機台、檢驗台展示
 * 手機端高性效：antialias、setPixelRatio 上限 2、低多邊形環境
 */
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { OBJLoader } from 'three/addons/loaders/OBJLoader.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';

const DEG2RAD = Math.PI / 180;
const FLOOR_Y = -0.85;
const PEDESTAL_TOP_Y = -0.79;

/** 建立佔位幾何體（置於工廠檢驗台上，黃色高反差零件） */
function createPlaceholderMesh(color) {
  const group = new THREE.Group();

  const bodyGeo = new THREE.CylinderGeometry(0.35, 0.45, 1.6, 32);
  const bodyMat = new THREE.MeshStandardMaterial({
    color: new THREE.Color(color || '#FFD100'),
    metalness: 0.55,
    roughness: 0.28,
  });
  const body = new THREE.Mesh(bodyGeo, bodyMat);
  body.name = 'component_body';
  body.castShadow = true;
  body.receiveShadow = true;
  group.add(body);

  const capGeo = new THREE.TorusGeometry(0.42, 0.06, 16, 48);
  const cap = new THREE.Mesh(capGeo, bodyMat.clone());
  cap.name = 'component_cap';
  cap.rotation.x = Math.PI / 2;
  cap.position.y = 0.75;
  cap.castShadow = true;
  group.add(cap);

  const jointGeo = new THREE.SphereGeometry(0.18, 24, 24);
  const jointMat = new THREE.MeshStandardMaterial({
    color: new THREE.Color('#1E4A8C'),
    metalness: 0.7,
    roughness: 0.2,
  });
  const joint = new THREE.Mesh(jointGeo, jointMat);
  joint.name = 'component_joint';
  joint.position.set(0.5, -0.3, 0);
  group.add(joint);

  return group;
}

/** 冷室壓鑄機簡化 3D 預覽（STEP 尚未轉 GLB 時使用） */
function createDieCastingMachineMesh(color, tonnage = 420) {
  const group = new THREE.Group();
  group.name = 'die_casting_machine';
  const t = 0.75 + Math.min(Math.max(tonnage, 100), 1500) / 1500 * 0.55;

  const bodyMat = new THREE.MeshStandardMaterial({
    color: new THREE.Color(color || '#8B9299'),
    metalness: 0.64,
    roughness: 0.32,
  });
  const darkMat = new THREE.MeshStandardMaterial({
    color: 0x232931,
    metalness: 0.52,
    roughness: 0.48,
  });
  const accentMat = new THREE.MeshStandardMaterial({
    color: 0xcc0000,
    metalness: 0.42,
    roughness: 0.38,
  });
  const panelMat = new THREE.MeshStandardMaterial({
    color: 0x1a2332,
    metalness: 0.35,
    roughness: 0.55,
  });

  const base = new THREE.Mesh(new THREE.BoxGeometry(2.4 * t, 0.22 * t, 1.55 * t), darkMat);
  base.name = 'machine_base';
  base.position.y = -0.55 * t;
  group.add(base);

  const platenBot = new THREE.Mesh(new THREE.BoxGeometry(1.75 * t, 0.12 * t, 1.15 * t), bodyMat.clone());
  platenBot.name = 'machine_body';
  platenBot.position.y = -0.35 * t;
  group.add(platenBot);

  const frameL = new THREE.Mesh(new THREE.BoxGeometry(0.18 * t, 1.65 * t, 0.18 * t), darkMat);
  frameL.position.set(-0.72 * t, 0.45 * t, 0.42 * t);
  group.add(frameL);
  const frameR = frameL.clone();
  frameR.position.set(-0.72 * t, 0.45 * t, -0.42 * t);
  group.add(frameR);
  const frameL2 = frameL.clone();
  frameL2.position.set(0.72 * t, 0.45 * t, 0.42 * t);
  group.add(frameL2);
  const frameR2 = frameL.clone();
  frameR2.position.set(0.72 * t, 0.45 * t, -0.42 * t);
  group.add(frameR2);

  const mainBody = new THREE.Mesh(new THREE.BoxGeometry(1.55 * t, 0.95 * t, 1.05 * t), bodyMat.clone());
  mainBody.name = 'machine_body';
  mainBody.position.y = 0.35 * t;
  group.add(mainBody);

  const topPlaten = new THREE.Mesh(new THREE.BoxGeometry(1.7 * t, 0.14 * t, 1.12 * t), bodyMat.clone());
  topPlaten.name = 'machine_body';
  topPlaten.position.y = 1.05 * t;
  group.add(topPlaten);

  const inject = new THREE.Mesh(new THREE.CylinderGeometry(0.18 * t, 0.2 * t, 2.0 * t, 28), bodyMat.clone());
  inject.name = 'injection_unit';
  inject.rotation.z = Math.PI / 2;
  inject.position.set(-1.35 * t, 0.15 * t, 0);
  group.add(inject);

  const hopper = new THREE.Mesh(new THREE.CylinderGeometry(0.14 * t, 0.2 * t, 0.35 * t, 24), darkMat);
  hopper.position.set(-1.35 * t, 0.55 * t, 0);
  group.add(hopper);

  const cabinet = new THREE.Mesh(new THREE.BoxGeometry(0.55 * t, 1.1 * t, 0.45 * t), panelMat);
  cabinet.name = 'control_cabinet';
  cabinet.position.set(1.05 * t, 0.2 * t, 0.65 * t);
  group.add(cabinet);

  const stripe = new THREE.Mesh(new THREE.BoxGeometry(0.06 * t, 1.15 * t, 1.08 * t), accentMat);
  stripe.name = 'machine_accent';
  stripe.position.set(0.68 * t, 0.42 * t, 0);
  group.add(stripe);

  const badge = new THREE.Mesh(
    new THREE.PlaneGeometry(0.55 * t, 0.14 * t),
    new THREE.MeshStandardMaterial({ color: 0xffd100, emissive: 0xffd100, emissiveIntensity: 0.12 })
  );
  badge.position.set(0, 1.22 * t, 0.53 * t);
  group.add(badge);

  return group;
}

/** 虛擬工廠車間環境（環氧地坪 · 機台背景 ·  overhead 照明） */
function createFactoryEnvironment(scene) {
  const env = new THREE.Group();
  env.name = 'factory_environment';

  scene.background = new THREE.Color(0x1a1f26);
  scene.fog = new THREE.Fog(0x1a1f26, 10, 28);

  const floorMat = new THREE.MeshStandardMaterial({
    color: 0x52565e,
    metalness: 0.2,
    roughness: 0.72,
  });
  const floor = new THREE.Mesh(new THREE.PlaneGeometry(28, 28), floorMat);
  floor.rotation.x = -Math.PI / 2;
  floor.position.y = FLOOR_Y;
  floor.receiveShadow = true;
  env.add(floor);

  const grid = new THREE.GridHelper(28, 28, 0xf4a261, 0x3d4450);
  grid.position.y = FLOOR_Y + 0.01;
  env.add(grid);

  const safetyMat = new THREE.MeshBasicMaterial({ color: 0xffd100, transparent: true, opacity: 0.35 });
  const lane = new THREE.Mesh(new THREE.PlaneGeometry(1.2, 28), safetyMat);
  lane.rotation.x = -Math.PI / 2;
  lane.position.set(-1.5, FLOOR_Y + 0.02, 0);
  env.add(lane);

  const pedestal = new THREE.Mesh(
    new THREE.CylinderGeometry(0.58, 0.65, 0.14, 36),
    new THREE.MeshStandardMaterial({ color: 0x787f8a, metalness: 0.65, roughness: 0.32 })
  );
  pedestal.position.y = FLOOR_Y + 0.07;
  pedestal.castShadow = true;
  pedestal.receiveShadow = true;
  env.add(pedestal);

  const wallMat = new THREE.MeshStandardMaterial({ color: 0x2a3038, metalness: 0.08, roughness: 0.92 });
  const backWall = new THREE.Mesh(new THREE.PlaneGeometry(28, 9), wallMat);
  backWall.position.set(0, 3.6, -7);
  backWall.receiveShadow = true;
  env.add(backWall);

  const leftWall = new THREE.Mesh(new THREE.PlaneGeometry(14, 9), wallMat);
  leftWall.rotation.y = Math.PI / 2;
  leftWall.position.set(-7, 3.6, 0);
  env.add(leftWall);

  const rightWall = new THREE.Mesh(new THREE.PlaneGeometry(14, 9), wallMat);
  rightWall.rotation.y = -Math.PI / 2;
  rightWall.position.set(7, 3.6, 0);
  env.add(rightWall);

  const machineMat = new THREE.MeshStandardMaterial({ color: 0x232931, metalness: 0.45, roughness: 0.55 });
  const machines = [
    { x: -5.2, z: -5.5, w: 2.4, h: 2.0, d: 1.6 },
    { x: 4.8, z: -5.0, w: 2.0, h: 2.4, d: 1.4 },
    { x: -6.0, z: 2.5, w: 1.5, h: 1.6, d: 1.2 },
    { x: 5.5, z: 3.0, w: 1.8, h: 1.5, d: 1.0 },
  ];
  machines.forEach(({ x, z, w, h, d }) => {
    const body = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), machineMat);
    body.position.set(x, FLOOR_Y + h / 2, z);
    body.castShadow = true;
    body.receiveShadow = true;
    env.add(body);
    const light = new THREE.Mesh(
      new THREE.BoxGeometry(w * 0.6, 0.06, 0.25),
      new THREE.MeshStandardMaterial({ color: 0x4ade80, emissive: 0x22c55e, emissiveIntensity: 0.8 })
    );
    light.position.set(x, FLOOR_Y + h + 0.05, z + d * 0.2);
    env.add(light);
  });

  const pipeMat = new THREE.MeshStandardMaterial({ color: 0x64748b, metalness: 0.7, roughness: 0.35 });
  const pipe = new THREE.Mesh(new THREE.CylinderGeometry(0.06, 0.06, 12, 12), pipeMat);
  pipe.rotation.z = Math.PI / 2;
  pipe.position.set(0, 5.8, -6.5);
  env.add(pipe);

  [-4, 0, 4].forEach((x) => {
    const fixture = new THREE.Mesh(
      new THREE.BoxGeometry(2.8, 0.1, 0.5),
      new THREE.MeshStandardMaterial({ color: 0xfef3c7, emissive: 0xfff7ed, emissiveIntensity: 1.0 })
    );
    fixture.position.set(x, 5.6, 2);
    env.add(fixture);
  });

  const sign = new THREE.Mesh(
    new THREE.PlaneGeometry(2.2, 0.5),
    new THREE.MeshStandardMaterial({ color: 0xffd100, emissive: 0xffd100, emissiveIntensity: 0.15 })
  );
  sign.position.set(-5.5, 3.2, -6.95);
  env.add(sign);

  scene.add(env);
  return env;
}

/** 簡約攝影棚（scene_theme=studio 時使用） */
function createStudioEnvironment(scene) {
  scene.background = new THREE.Color(0x0f2d52);
  scene.fog = null;

  const ground = new THREE.Mesh(
    new THREE.CircleGeometry(3, 64),
    new THREE.MeshStandardMaterial({ color: 0x1e4a8c, metalness: 0.1, roughness: 0.85 })
  );
  ground.rotation.x = -Math.PI / 2;
  ground.position.y = FLOOR_Y;
  ground.receiveShadow = true;
  scene.add(ground);
}

function applyColorToMeshes(root, hexColor, keepJointBlue) {
  const color = new THREE.Color(hexColor);
  const keep = ['joint', 'machine_accent', 'machine_base', 'control_cabinet'];
  root.traverse((child) => {
    if (!child.isMesh) return;
    if (keepJointBlue && child.name && keep.some((k) => child.name.includes(k))) return;
    if (Array.isArray(child.material)) {
      child.material.forEach((m) => {
        if (m.color) m.color.copy(color);
        m.needsUpdate = true;
      });
    } else if (child.material && child.material.color) {
      child.material.color.copy(color);
      child.material.needsUpdate = true;
    }
  });
}

const YousiShowroom3D = {
  scene: null,
  camera: null,
  renderer: null,
  controls: null,
  model: null,
  animId: null,
  baseScale: 1,
  config: {},
  pivotGroup: null,
  sceneTheme: 'factory',
  envGroup: null,

  init(opts) {
    const canvas = document.getElementById(opts.canvasId);
    const container = document.getElementById(opts.containerId);
    const loaderEl = document.getElementById(opts.loaderId);
    const fallbackEl = document.getElementById(opts.fallbackId);
    if (!canvas || !container) return;

    this.config = opts.config || {};
    this.sceneTheme = opts.sceneTheme || this.config.scene_theme || 'factory';
    const defaultColor = opts.defaultColor || this.config.default_color || '#FFD100';
    const width = container.clientWidth;
    const height = container.clientHeight;

    this.scene = new THREE.Scene();

    this.camera = new THREE.PerspectiveCamera(42, width / height, 0.1, 100);
    this.camera.position.set(2.4, 1.55, 3.0);

    this.renderer = new THREE.WebGLRenderer({
      canvas,
      antialias: true,
      alpha: false,
      powerPreference: 'high-performance',
    });
    this.renderer.setSize(width, height, false);
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    this.renderer.outputColorSpace = THREE.SRGBColorSpace;
    this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
    this.renderer.toneMappingExposure = this.sceneTheme === 'factory' ? 1.05 : 1.15;
    this.renderer.shadowMap.enabled = true;
    this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;

    this.controls = new OrbitControls(this.camera, canvas);
    this.controls.enableDamping = true;
    this.controls.dampingFactor = 0.06;
    this.controls.minDistance = 1.4;
    this.controls.maxDistance = 9;
    this.controls.maxPolarAngle = Math.PI * 0.88;
    this.controls.target.set(0, 0.15, 0);

    const pmrem = new THREE.PMREMGenerator(this.renderer);
    this.scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;
    pmrem.dispose();

    if (this.sceneTheme === 'factory') {
      this.envGroup = createFactoryEnvironment(this.scene);
      this._setupFactoryLighting();
    } else {
      createStudioEnvironment(this.scene);
      this._setupStudioLighting();
    }

    this.pivotGroup = new THREE.Group();
    this.pivotGroup.position.y = PEDESTAL_TOP_Y;
    this.scene.add(this.pivotGroup);

    const gltfUrl = this.config.gltf_url;
    const previewMode = this.config.preview_mode || 'component';
    const cadConvertUrl = this.config.cad_convert_url || '';
    const cadBadgeEl = document.getElementById('threeCadBadge');
    const loaderTextEl = loaderEl ? loaderEl.querySelector('p') : null;

    if (gltfUrl) {
      const gltfLoader = new GLTFLoader();
      gltfLoader.load(
        gltfUrl,
        (gltf) => {
          this._mountModel(gltf.scene, defaultColor);
          if (loaderEl) loaderEl.style.display = 'none';
        },
        undefined,
        () => {
          if (cadConvertUrl) {
            this._convertCadFromServer(cadConvertUrl, loaderEl, loaderTextEl, cadBadgeEl, defaultColor);
          } else {
            this._mountModel(createPlaceholderMesh(defaultColor), defaultColor);
            if (loaderEl) loaderEl.style.display = 'none';
          }
        }
      );
    } else if (cadConvertUrl) {
      this._convertCadFromServer(cadConvertUrl, loaderEl, loaderTextEl, cadBadgeEl, defaultColor);
    } else if (previewMode === 'die_casting') {
      const tonnage = this.config.machine_tonnage || 420;
      this._mountModel(createDieCastingMachineMesh(defaultColor, tonnage), defaultColor);
      this.camera.position.set(3.2, 1.85, 3.6);
      this.controls.target.set(0, 0.25, 0);
      if (loaderEl) loaderEl.style.display = 'none';
      if (cadBadgeEl) cadBadgeEl.classList.remove('hidden');
    } else {
      this._mountModel(createPlaceholderMesh(defaultColor), defaultColor);
      if (loaderEl) loaderEl.style.display = 'none';
      if (fallbackEl) {
        fallbackEl.classList.remove('hidden');
        fallbackEl.classList.add('flex');
      }
    }

    const initialScale = (this.config.scale && this.config.scale.default) || 1;
    this.setScale(initialScale);

    this._animate();
    this._bindResize(container);

    window.YousiShowroom3D = this;
  },

  _setupFactoryLighting() {
    const hemi = new THREE.HemisphereLight(0xe2e8f0, 0x3d4450, 0.55);
    this.scene.add(hemi);

    const overhead = new THREE.DirectionalLight(0xfff7ed, 1.35);
    overhead.position.set(2, 8, 4);
    overhead.castShadow = true;
    overhead.shadow.mapSize.set(1024, 1024);
    overhead.shadow.camera.near = 0.5;
    overhead.shadow.camera.far = 25;
    overhead.shadow.camera.left = -8;
    overhead.shadow.camera.right = 8;
    overhead.shadow.camera.top = 8;
    overhead.shadow.camera.bottom = -8;
    this.scene.add(overhead);

    const fill = new THREE.DirectionalLight(0x94a3b8, 0.4);
    fill.position.set(-4, 3, -2);
    this.scene.add(fill);

    const accent = new THREE.DirectionalLight(0xffd100, 0.55);
    accent.position.set(3, 2, -3);
    this.scene.add(accent);

    [[-4, 5.5, 2], [0, 5.5, 2], [4, 5.5, 2]].forEach(([x, y, z]) => {
      const pl = new THREE.PointLight(0xfffbeb, 0.35, 12);
      pl.position.set(x, y, z);
      this.scene.add(pl);
    });
  },

  _setupStudioLighting() {
    const hemi = new THREE.HemisphereLight(0xe8f4fc, 0x0f2d52, 0.9);
    this.scene.add(hemi);

    const keyLight = new THREE.DirectionalLight(0xffffff, 1.4);
    keyLight.position.set(4, 6, 3);
    keyLight.castShadow = true;
    keyLight.shadow.mapSize.set(1024, 1024);
    this.scene.add(keyLight);

    const rimLight = new THREE.DirectionalLight(0xffd100, 0.6);
    rimLight.position.set(-3, 2, -4);
    this.scene.add(rimLight);
  },

  _mountModel(object, defaultColor) {
    if (this.model) {
      this.pivotGroup.remove(this.model);
    }
    this.model = object;
    this.model.traverse((child) => {
      if (child.isMesh) {
        child.castShadow = true;
        child.receiveShadow = true;
        if (child.material && !child.material.isMeshStandardMaterial) {
          const old = child.material;
          child.material = new THREE.MeshStandardMaterial({
            color: old.color || new THREE.Color(defaultColor),
            metalness: 0.55,
            roughness: 0.38,
          });
        }
      }
    });

    const box = new THREE.Box3().setFromObject(this.model);
    const size = box.getSize(new THREE.Vector3());
    const maxDim = Math.max(size.x, size.y, size.z) || 1;
    const fitScale = (this.config.preview_mode === 'die_casting' || this.config.cad_convert_url ? 2.2 : 1.4) / maxDim;
    this.model.scale.setScalar(fitScale);
    this.baseScale = fitScale;

    const center = box.getCenter(new THREE.Vector3());
    this.model.position.sub(center.multiplyScalar(fitScale));
    this.pivotGroup.add(this.model);
    applyColorToMeshes(this.model, defaultColor, true);
    this._fitCamera();
  },

  _fitCamera() {
    if (!this.model || !this.camera || !this.controls) return;
    const box = new THREE.Box3().setFromObject(this.pivotGroup);
    if (box.isEmpty()) return;
    const center = box.getCenter(new THREE.Vector3());
    const size = box.getSize(new THREE.Vector3());
    const maxDim = Math.max(size.x, size.y, size.z) || 1;
    const dist = maxDim * 2.2;
    this.camera.position.set(center.x + dist * 0.7, center.y + dist * 0.5, center.z + dist * 0.7);
    this.controls.target.copy(center);
    this.controls.minDistance = dist * 0.05;
    this.controls.maxDistance = dist * 8;
    this.camera.near = dist * 0.001;
    this.camera.far = dist * 50;
    this.camera.updateProjectionMatrix();
  },

  _convertCadFromServer(url, loaderEl, loaderTextEl, cadBadgeEl, defaultColor) {
    const quality = 'low';
    const convertUrl = url + (url.includes('?') ? '&' : '?') + 'quality=' + quality;
    if (loaderTextEl) {
      loaderTextEl.textContent = '正在將 STEP 轉換為 3D 格式（快速）…大型模型可能需要數分鐘';
    }

    const xhr = new XMLHttpRequest();
    xhr.open('GET', convertUrl, true);
    xhr.responseType = 'arraybuffer';
    xhr.timeout = 600000;

    xhr.onload = () => {
      const fmt = xhr.getResponseHeader('X-3D-Format') || 'glb';
      const byteLen = xhr.response ? xhr.response.byteLength : 0;
      const sizeMB = (byteLen / (1024 * 1024)).toFixed(1);

      if (xhr.status === 200 && byteLen > 100) {
        if (parseFloat(sizeMB) > 40) {
          this._cadConvertFailed(loaderEl, loaderTextEl, '轉換後檔案過大（' + sizeMB + ' MB）');
          return;
        }
        if (loaderTextEl) loaderTextEl.textContent = '載入 3D 模型（' + sizeMB + ' MB）…';
        try {
          if (fmt === 'obj') {
            this._loadOBJBuffer(xhr.response, defaultColor);
          } else {
            this._loadGLTFBuffer(xhr.response, defaultColor);
          }
          if (loaderEl) loaderEl.style.display = 'none';
          if (cadBadgeEl) cadBadgeEl.classList.remove('hidden');
        } catch (err) {
          this._cadConvertFailed(loaderEl, loaderTextEl, '載入模型失敗：' + err.message);
        }
        return;
      }

      let msg = 'STEP 轉換失敗（HTTP ' + xhr.status + '）';
      try {
        const json = JSON.parse(new TextDecoder().decode(xhr.response));
        msg = json.rtnmsg || msg;
      } catch (e) { /* ignore */ }
      this._cadConvertFailed(loaderEl, loaderTextEl, msg);
    };

    xhr.onerror = () => this._cadConvertFailed(loaderEl, loaderTextEl, 'STEP 轉換連線失敗');
    xhr.ontimeout = () => this._cadConvertFailed(loaderEl, loaderTextEl, 'STEP 轉換逾時，檔案可能太大');
    xhr.send();
  },

  _cadConvertFailed(loaderEl, loaderTextEl, msg) {
    const color = this.config.default_color || '#8B9299';
    const tonnage = this.config.machine_tonnage || 420;
    if (this.config.preview_mode === 'die_casting') {
      this._mountModel(createDieCastingMachineMesh(color, tonnage), color);
      if (loaderEl) loaderEl.style.display = 'none';
      if (loaderTextEl) loaderTextEl.textContent = msg + '（目前顯示簡化模型）';
    } else {
      this._mountModel(createPlaceholderMesh(color), color);
      if (loaderEl) loaderEl.style.display = 'none';
    }
  },

  _loadGLTFBuffer(buffer, defaultColor) {
    const loader = new GLTFLoader();
    loader.parse(
      buffer,
      '',
      (gltf) => {
        this._mountModel(gltf.scene, defaultColor);
      },
      (err) => {
        throw err || new Error('GLB 解析失敗');
      }
    );
  },

  _loadOBJBuffer(buffer, defaultColor) {
    const text = new TextDecoder().decode(buffer);
    const loader = new OBJLoader();
    const root = loader.parse(text);
    this._mountModel(root, defaultColor);
  },

  _animate() {
    if (this.animId) cancelAnimationFrame(this.animId);
    const tick = () => {
      this.animId = requestAnimationFrame(tick);
      if (this.controls) this.controls.update();
      if (this.renderer && this.scene && this.camera) {
        this.renderer.render(this.scene, this.camera);
      }
    };
    tick();
  },

  _bindResize(container) {
    const onResize = () => {
      const w = container.clientWidth;
      const h = container.clientHeight;
      if (!w || !h) return;
      this.camera.aspect = w / h;
      this.camera.updateProjectionMatrix();
      this.renderer.setSize(w, h, false);
      this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    };
    window.addEventListener('resize', onResize);
    if (window.ResizeObserver) {
      const ro = new ResizeObserver(onResize);
      ro.observe(container);
    }
  },

  setScale(value) {
    if (!this.model) return;
    const s = this.baseScale * value;
    this.model.scale.setScalar(s);
  },

  setDiameter(mm) {
    if (!this.model || !this.config.diameter) return;
    const range = this.config.diameter.max - this.config.diameter.min;
    if (range <= 0) return;
    const ratio = (mm - this.config.diameter.min) / range;
    const scaleX = 0.85 + ratio * 0.3;
    const scaleZ = 0.85 + ratio * 0.3;
    const base = this.baseScale * (this.config.scale ? this.config.scale.default : 1);
    this.model.scale.x = base * scaleX;
    this.model.scale.z = base * scaleZ;
  },

  setAngleCut(deg) {
    if (!this.pivotGroup) return;
    this.pivotGroup.rotation.z = deg * DEG2RAD;
  },

  setJointAngle(deg) {
    if (!this.model) return;
    const joint = this.model.getObjectByName('component_joint');
    if (joint) {
      joint.rotation.y = deg * DEG2RAD;
    } else {
      this.model.rotation.y = deg * DEG2RAD * 0.5;
    }
  },

  setElevationAngle(deg) {
    if (!this.pivotGroup) return;
    this.pivotGroup.rotation.x = deg * DEG2RAD;
  },

  setMeshColor(hexColor) {
    if (!this.model) return;
    applyColorToMeshes(this.model, hexColor, true);
  },
};

window.YousiShowroom3D = YousiShowroom3D;

function autoInitFromDOM() {
  const canvas = document.getElementById('threeCanvas');
  const panel = document.getElementById('poprealPanel');
  if (!canvas || !panel) return;

  let config = {};
  try {
    config = JSON.parse(panel.dataset.config || '{}');
  } catch (e) {
    config = {};
  }

  const defaultColor = panel.dataset.defaultColor || config.default_color || '#FFD100';
  const sceneTheme = panel.dataset.sceneTheme || config.scene_theme || 'factory';

  YousiShowroom3D.init({
    canvasId: 'threeCanvas',
    containerId: 'threeContainer',
    loaderId: 'threeLoader',
    fallbackId: 'threeFallback',
    config,
    defaultColor,
    sceneTheme,
  });

  bindPoprealSliders();
}

function bindPoprealSliders() {
  const scaleSlider = document.getElementById('scaleSlider');
  if (scaleSlider) {
    scaleSlider.addEventListener('input', function () {
      const val = document.getElementById('scaleValue');
      if (val) val.textContent = this.value;
      YousiShowroom3D.setScale(parseFloat(this.value));
    });
  }
  const diameterSlider = document.getElementById('diameterSlider');
  if (diameterSlider) {
    diameterSlider.addEventListener('input', function () {
      const val = document.getElementById('diameterValue');
      if (val) val.textContent = this.value;
      YousiShowroom3D.setDiameter(parseFloat(this.value));
    });
  }
  const angleCutSlider = document.getElementById('angleCutSlider');
  if (angleCutSlider) {
    angleCutSlider.addEventListener('input', function () {
      const val = document.getElementById('angleCutValue');
      if (val) val.textContent = this.value;
      YousiShowroom3D.setAngleCut(parseFloat(this.value));
    });
  }
  const jointSlider = document.getElementById('jointAngleSlider');
  if (jointSlider) {
    jointSlider.addEventListener('input', function () {
      const val = document.getElementById('jointAngleValue');
      if (val) val.textContent = this.value;
      YousiShowroom3D.setJointAngle(parseFloat(this.value));
    });
  }
  const elevSlider = document.getElementById('elevationAngleSlider');
  if (elevSlider) {
    elevSlider.addEventListener('input', function () {
      const val = document.getElementById('elevationAngleValue');
      if (val) val.textContent = this.value;
      YousiShowroom3D.setElevationAngle(parseFloat(this.value));
    });
  }
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', autoInitFromDOM);
} else {
  autoInitFromDOM();
}

export default YousiShowroom3D;
