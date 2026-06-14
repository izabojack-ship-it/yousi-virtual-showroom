/**
 * 鋁台 / 工廠展間 — 多視角沉浸式環景
 * 將現場實拍照片投影於球面內側，支援拖曳環顧、切換視角（非完整 360° 等距柱狀圖）
 */
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { createTechPhotoMaterial, updateTechMaterialTime } from './showroom-tech-shader.js';

export function initImmersiveTour(container, imageUrls, options = {}) {
  if (!container || !imageUrls?.length) return null;

  const title = options.title || '';
  let index = 0;
  let mesh = null;
  let animId = null;

  const wrap = document.createElement('div');
  wrap.className = 'immersive-tour-wrap';
  wrap.innerHTML = `
    <div class="immersive-tour-badge">
      科技美顏環景 · 明亮乾淨 · 拖曳環顧 · 切換視角
    </div>
    <div class="immersive-tour-canvas-host"></div>
    <div class="immersive-tour-controls">
      <button type="button" class="immersive-btn" data-act="prev" aria-label="上一視角">‹</button>
      <span class="immersive-tour-counter">1 / ${imageUrls.length}</span>
      <button type="button" class="immersive-btn" data-act="next" aria-label="下一視角">›</button>
    </div>
    ${title ? `<p class="immersive-tour-caption">${title}</p>` : ''}
    <p class="immersive-tour-note">
      此區為現場實拍多視角環景。完整 360° 環繞需使用全景相機或 iPhone 全景模式拍攝。
    </p>
  `;
  container.appendChild(wrap);

  const host = wrap.querySelector('.immersive-tour-canvas-host');
  const counter = wrap.querySelector('.immersive-tour-counter');

  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0x0a1628);
  const camera = new THREE.PerspectiveCamera(72, 16 / 10, 0.1, 1000);
  camera.position.set(0, 0, 0.01);

  const renderer = new THREE.WebGLRenderer({ antialias: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  host.appendChild(renderer.domElement);

  const controls = new OrbitControls(camera, renderer.domElement);
  controls.enableZoom = true;
  controls.enablePan = false;
  controls.rotateSpeed = -0.35;
  controls.minDistance = 0.01;
  controls.maxDistance = 0.01;
  controls.minPolarAngle = Math.PI * 0.28;
  controls.maxPolarAngle = Math.PI * 0.72;

  const loader = new THREE.TextureLoader();
  loader.setCrossOrigin('anonymous');

  function resize() {
    const w = host.clientWidth;
    const h = Math.max(280, Math.round(w * 0.62));
    host.style.height = `${h}px`;
    renderer.setSize(w, h);
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
  }

  function buildPhotoSphere(texture) {
    texture.colorSpace = THREE.SRGBColorSpace;
    texture.minFilter = THREE.LinearFilter;
    texture.generateMipmaps = false;

    const geo = new THREE.SphereGeometry(500, 64, 48, -Math.PI * 0.32, Math.PI * 0.64, Math.PI * 0.22, Math.PI * 0.56);
    geo.scale(-1, 1, 1);
    const mat = createTechPhotoMaterial(texture);
    return new THREE.Mesh(geo, mat);
  }

  function showScene(i) {
    index = (i + imageUrls.length) % imageUrls.length;
    counter.textContent = `${index + 1} / ${imageUrls.length}`;
    loader.load(imageUrls[index], (texture) => {
      if (mesh) {
        scene.remove(mesh);
        mesh.geometry.dispose();
        const map = mesh.material.uniforms?.map?.value;
        if (map) map.dispose();
        mesh.material.dispose();
      }
      mesh = buildPhotoSphere(texture);
      scene.add(mesh);
      controls.reset();
    });
  }

  function animate() {
    animId = requestAnimationFrame(animate);
    if (mesh?.material) {
      updateTechMaterialTime(mesh.material, performance.now() * 0.001);
    }
    controls.update();
    renderer.render(scene, camera);
  }

  wrap.querySelector('[data-act="prev"]').addEventListener('click', () => showScene(index - 1));
  wrap.querySelector('[data-act="next"]').addEventListener('click', () => showScene(index + 1));

  const ro = new ResizeObserver(resize);
  ro.observe(host);
  resize();
  showScene(0);
  animate();

  return {
    destroy() {
      cancelAnimationFrame(animId);
      ro.disconnect();
      renderer.dispose();
      wrap.remove();
    },
  };
}
