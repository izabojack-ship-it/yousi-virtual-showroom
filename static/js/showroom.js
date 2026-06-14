/* 雲端虛擬展間 — 前端互動 */

function openInquiry(productSlug) {
  const modal = document.getElementById('inquiryModal');
  const slugInput = document.getElementById('inquiryProductSlug');
  if (slugInput) slugInput.value = productSlug || '';
  if (modal) modal.classList.add('open');
}

function closeInquiry() {
  const modal = document.getElementById('inquiryModal');
  if (modal) modal.classList.remove('open');
}

/** 社群分享狀態（供快顯 Modal 使用） */
let _sharePayload = { title: '', url: '' };

function shareProduct(title, url) {
  _sharePayload = { title: title || document.title, url: url || window.location.href };
  if (navigator.share && window.matchMedia('(max-width: 640px)').matches) {
    navigator.share({ title: _sharePayload.title, url: _sharePayload.url }).catch(openShareModal);
    return;
  }
  openShareModal();
}

function openShareModal() {
  const modal = document.getElementById('shareModal');
  const titleEl = document.getElementById('shareModalTitle');
  const msgEl = document.getElementById('shareModalMsg');
  if (!modal) return;
  if (titleEl) titleEl.textContent = _sharePayload.title;
  if (msgEl) { msgEl.textContent = ''; msgEl.className = 'form-msg text-center'; }
  modal.classList.add('open');
  modal.setAttribute('aria-hidden', 'false');
}

function closeShareModal() {
  const modal = document.getElementById('shareModal');
  if (modal) {
    modal.classList.remove('open');
    modal.setAttribute('aria-hidden', 'true');
  }
}

function shareToPlatform(platform) {
  const { title, url } = _sharePayload;
  const msgEl = document.getElementById('shareModalMsg');
  const encoded = encodeURIComponent(url);
  const textEncoded = encodeURIComponent(title + ' ' + url);
  let target = '';
  switch (platform) {
    case 'line':
      target = `https://line.me/R/msg/text/?${textEncoded}`;
      window.open(target, '_blank', 'noopener');
      break;
    case 'facebook':
      target = `https://www.facebook.com/sharer/sharer.php?u=${encoded}`;
      window.open(target, '_blank', 'noopener');
      break;
    case 'linkedin':
      target = `https://www.linkedin.com/sharing/share-offsite/?url=${encoded}`;
      window.open(target, '_blank', 'noopener');
      break;
    case 'copy':
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(url).then(() => {
          if (msgEl) { msgEl.textContent = '連結已複製！'; msgEl.className = 'form-msg ok text-center'; }
        }).catch(() => fallbackCopy(url, msgEl));
      } else {
        fallbackCopy(url, msgEl);
      }
      return;
    default:
      break;
  }
}

function fallbackCopy(text, msgEl) {
  const ta = document.createElement('textarea');
  ta.value = text;
  ta.style.position = 'fixed';
  ta.style.opacity = '0';
  document.body.appendChild(ta);
  ta.select();
  try {
    document.execCommand('copy');
    if (msgEl) { msgEl.textContent = '連結已複製！'; msgEl.className = 'form-msg ok text-center'; }
  } catch (e) {
    if (msgEl) { msgEl.textContent = '複製失敗，請手動複製網址'; msgEl.className = 'form-msg err text-center'; }
  }
  document.body.removeChild(ta);
}

document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('inquiryForm');
  if (form) {
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      const msg = document.getElementById('inquiryMsg');
      const fd = new FormData(form);
      const payload = Object.fromEntries(fd.entries());
      try {
        const resp = await fetch('/inquiry/', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrf() },
          body: JSON.stringify(payload),
        });
        const data = await resp.json();
        if (data.success) {
          msg.textContent = data.message;
          msg.className = 'form-msg ok';
          form.reset();
          setTimeout(closeInquiry, 2000);
        } else {
          msg.textContent = data.error || '送出失敗';
          msg.className = 'form-msg err';
        }
      } catch (err) {
        msg.textContent = '連線失敗，請稍後再試';
        msg.className = 'form-msg err';
      }
    });
  }

  // 簡易 360 全景拖曳
  const pano = document.getElementById('panoramaViewer');
  if (pano) {
    const src = pano.dataset.src;
    if (src) {
      let offset = 50;
      pano.style.backgroundImage = `url('${src}')`;
      pano.style.backgroundSize = 'auto 100%';
      pano.style.backgroundPosition = `${offset}% center`;
      let dragging = false, startX = 0, startOffset = 50;
      pano.addEventListener('mousedown', (e) => { dragging = true; startX = e.clientX; startOffset = offset; });
      pano.addEventListener('touchstart', (e) => { dragging = true; startX = e.touches[0].clientX; startOffset = offset; });
      const move = (clientX) => {
        if (!dragging) return;
        offset = Math.max(0, Math.min(100, startOffset + (clientX - startX) * 0.15));
        pano.style.backgroundPosition = `${offset}% center`;
      };
      window.addEventListener('mousemove', (e) => move(e.clientX));
      window.addEventListener('touchmove', (e) => move(e.touches[0].clientX));
      window.addEventListener('mouseup', () => { dragging = false; });
      window.addEventListener('touchend', () => { dragging = false; });
    }
  }
});

function getCsrf() {
  const m = document.cookie.match(/csrftoken=([^;]+)/);
  return m ? m[1] : '';
}
