/**
 * VR 展覽館 — 全螢幕沉浸模式（風格參考 VR展覽館）
 */
import { initStreetViewTour } from './showroom-streetview.js';

const rotateOverlay = document.getElementById('vrRotateOverlay');
const fsOverlay = document.getElementById('vrFullscreenOverlay');
const helpPanel = document.getElementById('vrHelpPanel');
const helpBtn = document.getElementById('vrHelpBtn');
const helpClose = document.getElementById('vrHelpClose');
const fsBtn = document.getElementById('vrEnterFullscreen');
const sceneLabel = document.getElementById('vrSceneLabel');
const mount = document.getElementById('vrTourMount');

function isPortrait() {
  return window.innerHeight > window.innerWidth;
}

function isMobile() {
  return window.matchMedia('(max-width: 900px)').matches;
}

function requestFullscreen() {
  const el = document.documentElement;
  const fn = el.requestFullscreen || el.webkitRequestFullscreen || el.msRequestFullscreen;
  if (fn) return fn.call(el).catch(() => {});
}

function showOverlay(el) {
  if (el) el.hidden = false;
}

function hideOverlay(el) {
  if (el) el.hidden = true;
}

function checkOrientation() {
  if (!isMobile() || sessionStorage.getItem('vr_skip_rotate')) {
    hideOverlay(rotateOverlay);
    return;
  }
  if (isPortrait()) showOverlay(rotateOverlay);
  else hideOverlay(rotateOverlay);
}

document.querySelectorAll('[data-vr-dismiss]').forEach((btn) => {
  btn.addEventListener('click', () => {
    const key = btn.dataset.vrDismiss;
    if (key === 'rotate') sessionStorage.setItem('vr_skip_rotate', '1');
    if (key === 'fullscreen') sessionStorage.setItem('vr_skip_fs_prompt', '1');
    hideOverlay(key === 'rotate' ? rotateOverlay : fsOverlay);
  });
});

if (!sessionStorage.getItem('vr_skip_fs_prompt') && isMobile()) {
  showOverlay(fsOverlay);
} else {
  hideOverlay(fsOverlay);
}

fsBtn?.addEventListener('click', () => {
  requestFullscreen();
  hideOverlay(fsOverlay);
});

helpBtn?.addEventListener('click', () => showOverlay(helpPanel));
helpClose?.addEventListener('click', () => hideOverlay(helpPanel));

window.addEventListener('resize', checkOrientation);
window.addEventListener('orientationchange', checkOrientation);
checkOrientation();

const tourEl = document.getElementById('street-tour-json');

if (mount && tourEl) {
  const tourConfig = JSON.parse(tourEl.textContent);
  initStreetViewTour(mount, tourConfig, {
    vrMode: true,
    refinedMode: true,
    techMode: false,
    onSceneChange(scene, index, total) {
      if (sceneLabel) sceneLabel.textContent = scene.label;
    },
  });
}
