/**
 * 自然對比 — 設備幾乎原圖直出，背景輕度淡化
 */
import * as THREE from 'three';

const TECH_VERTEX = `
varying vec2 vUv;
void main() {
  vUv = uv;
  gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
}
`;

const TECH_FRAGMENT = `
uniform sampler2D map;
uniform float opacity;
uniform float time;
varying vec2 vUv;

float subjectMask(vec3 c) {
  float lum = dot(c, vec3(0.2126, 0.7152, 0.0722));
  float sat = max(c.r, max(c.g, c.b)) - min(c.r, min(c.g, c.b));
  float dark = 1.0 - smoothstep(0.0, 0.46, lum);
  float mid = smoothstep(0.12, 0.56, lum) * (1.0 - smoothstep(0.56, 0.88, lum));
  float colored = smoothstep(0.04, 0.32, sat);
  return clamp(max(dark * 0.92, mid * colored * 0.98), 0.0, 1.0);
}

vec3 sharpenSubject(vec3 orig, sampler2D tex, vec2 uv, float obj) {
  vec2 px = vec2(1.1 / 1920.0, 1.1 / 1080.0);
  vec3 n = (
    texture2D(tex, uv + vec2(px.x, 0.0)).rgb +
    texture2D(tex, uv - vec2(px.x, 0.0)).rgb +
    texture2D(tex, uv + vec2(0.0, px.y)).rgb +
    texture2D(tex, uv - vec2(0.0, px.y)).rgb
  ) * 0.25;
  vec3 detail = orig - n;
  return clamp(orig + detail * 0.42 * obj, 0.0, 1.0);
}

vec3 backgroundSoft(vec3 orig) {
  float lum = dot(orig, vec3(0.2126, 0.7152, 0.0722));
  vec3 bg = mix(vec3(lum), orig, 0.58);
  bg = mix(bg, vec3(0.97, 0.98, 1.0), 0.30);
  return bg * 1.04;
}

void main() {
  vec4 tex = texture2D(map, vUv);
  vec3 orig = tex.rgb;
  float obj = subjectMask(orig);

  vec3 subject = sharpenSubject(orig, map, vUv, obj);
  vec3 bg = backgroundSoft(orig);
  vec3 color = mix(bg, subject, obj);

  float scan = sin(vUv.y * 900.0 + time * 0.4) * 0.0008;
  color += scan;

  gl_FragColor = vec4(color, tex.a * opacity);
}
`;

export function createTechPhotoMaterial(texture, { opacity = 1 } = {}) {
  return new THREE.ShaderMaterial({
    uniforms: {
      map: { value: texture },
      opacity: { value: opacity },
      time: { value: 0 },
    },
    vertexShader: TECH_VERTEX,
    fragmentShader: TECH_FRAGMENT,
    transparent: opacity < 1,
    depthWrite: opacity >= 0.99,
  });
}

export function updateTechMaterialTime(material, t) {
  if (material?.uniforms?.time) {
    material.uniforms.time.value = t;
  }
}

export function setTechMaterialOpacity(material, opacity) {
  if (!material?.uniforms?.opacity) return;
  material.uniforms.opacity.value = opacity;
  material.transparent = opacity < 1;
  material.depthWrite = opacity >= 0.99;
}

export function isTechMaterial(material) {
  return Boolean(material?.uniforms?.map);
}

export function setPhotoMaterialOpacity(material, opacity) {
  if (isTechMaterial(material)) {
    setTechMaterialOpacity(material, opacity);
    return;
  }
  material.opacity = opacity;
  material.transparent = opacity < 1;
  material.depthWrite = opacity >= 0.99;
}

export function injectTechHud(canvasHost, label = 'ORIGINAL · SHARP') {
  if (!canvasHost || canvasHost.querySelector('.sv-tech-hud')) return null;
  const hud = document.createElement('div');
  hud.className = 'sv-tech-hud';
  hud.innerHTML = `
    <div class="sv-tech-bloom"></div>
    <div class="sv-tech-scanlines"></div>
    <div class="sv-tech-grid"></div>
    <div class="sv-tech-corner sv-tech-tl"></div>
    <div class="sv-tech-corner sv-tech-tr"></div>
    <div class="sv-tech-corner sv-tech-bl"></div>
    <div class="sv-tech-corner sv-tech-br"></div>
    <div class="sv-tech-readout">
      <span class="sv-tech-live">● LIVE</span>
      <span class="sv-tech-sync">${label}</span>
    </div>`;
  canvasHost.appendChild(hud);
  return hud;
}
