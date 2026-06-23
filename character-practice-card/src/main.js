const GRID = 96;
const RENDER_SIZE = 640;
const CARD_BASE = 360;

const FONTS = [
  { id: 'lxgw', label: '霞鹜文楷（网页字库）', stack: '"LXGW WenKai", "Kaiti SC", "STKaiti", serif' },
  { id: 'noto', label: '思源宋体（Noto Serif SC）', stack: '"Noto Serif SC", "Songti SC", serif' },
  { id: 'system', label: '系统楷书（楷体 / 华文楷体）', stack: '"Kaiti SC", "KaiTi", "STKaiti", "FangSong", serif' },
];

const els = {
  charInput: document.querySelector('#char-input'),
  fontSelect: document.querySelector('#font-select'),
  modeSelect: document.querySelector('#mode-select'),
  thresholdRange: document.querySelector('#threshold-range'),
  thresholdValue: document.querySelector('#threshold-value'),
  generateBtn: document.querySelector('#generate-btn'),
  downloadBtn: document.querySelector('#download-btn'),
  statusLine: document.querySelector('#status-line'),
  gallery: document.querySelector('#gallery'),
  cardCount: document.querySelector('#card-count'),
  lightbox: document.querySelector('#lightbox'),
  lightboxStage: document.querySelector('#lightbox-stage'),
  lightboxClose: document.querySelector('#lightbox-close'),
};

/** @type {HTMLCanvasElement[]} */
let lastCanvases = [];

function initFontSelect() {
  els.fontSelect.innerHTML = FONTS.map((f) => `<option value="${f.id}">${f.label}</option>`).join('');
}

function getFontStack(id) {
  return FONTS.find((f) => f.id === id)?.stack ?? FONTS[0].stack;
}

function extractChars(text) {
  const out = [];
  for (const ch of text) {
    if (/\s/.test(ch)) continue;
    const cp = ch.codePointAt(0);
    if (cp && (cp > 0x2e7f || (cp >= 0x4e00 && cp <= 0x9fff))) {
      out.push(ch);
    }
  }
  return out;
}


function sampleGrid(char, fontStack, thresholdPct) {
  const size = RENDER_SIZE;
  const cell = size / GRID;
  const off = document.createElement('canvas');
  off.width = size;
  off.height = size;
  const ctx = off.getContext('2d', { willReadFrequently: true });
  if (!ctx) throw new Error('Canvas unsupported');

  ctx.clearRect(0, 0, size, size);
  ctx.fillStyle = '#ffffff';
  ctx.fillRect(0, 0, size, size);

  const fontSize = Math.round(size * 0.72);
  ctx.fillStyle = '#0b0b0b';
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.font = `${fontSize}px ${fontStack}`;
  ctx.fillText(char, size / 2, size / 2 + cell * 0.02);

  const img = ctx.getImageData(0, 0, size, size).data;
  /** @type {boolean[][]} */
  const cells = Array.from({ length: GRID }, () => Array(GRID).fill(false));

  for (let row = 0; row < GRID; row++) {
    for (let col = 0; col < GRID; col++) {
      let dark = 0;
      let total = 0;
      const x0 = Math.floor(col * cell);
      const y0 = Math.floor(row * cell);
      const x1 = Math.floor((col + 1) * cell);
      const y1 = Math.floor((row + 1) * cell);
      for (let y = y0; y < y1; y += 2) {
        for (let x = x0; x < x1; x += 2) {
          const i = (y * size + x) * 4;
          const lum = (img[i] + img[i + 1] + img[i + 2]) / 3;
          if (255 - lum > 18) dark++;
          total++;
        }
      }
      cells[row][col] = total > 0 && (dark / total) * 100 >= thresholdPct;
    }
  }

  return cells;
}

function vertexLit(cells, vx, vy) {
  for (let dr = -1; dr <= 0; dr++) {
    for (let dc = -1; dc <= 0; dc++) {
      const r = vy + dr;
      const c = vx + dc;
      if (r >= 0 && r < GRID && c >= 0 && c < GRID && cells[r][c]) return true;
    }
  }
  return false;
}

function drawPracticeCard(canvas, char, cells, mode, meta = { label: '' }) {
  const scale = canvas.width / CARD_BASE;
  const padding = Math.round(36 * scale);
  const gridPx = canvas.width - padding * 2;
  const cell = gridPx / GRID;
  const ctx = canvas.getContext('2d');
  if (!ctx) return;

  ctx.clearRect(0, 0, canvas.width, canvas.height);
  const paper = ctx.createLinearGradient(0, 0, canvas.width, canvas.height);
  paper.addColorStop(0, '#fdf8f0');
  paper.addColorStop(1, '#efe4d4');
  ctx.fillStyle = paper;
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  const ox = padding;
  const oy = padding;

  ctx.strokeStyle = 'rgba(12,10,9,0.08)';
  ctx.lineWidth = 1;
  for (let i = 0; i <= GRID; i++) {
    const p = i * cell;
    ctx.beginPath();
    ctx.moveTo(ox + p, oy);
    ctx.lineTo(ox + p, oy + GRID * cell);
    ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(ox, oy + p);
    ctx.lineTo(ox + GRID * cell, oy + p);
    ctx.stroke();
  }

  if (mode === 'grid') {
    ctx.fillStyle = 'rgba(12,10,9,0.82)';
    const radius = cell * 0.18;
    for (let row = 0; row < GRID; row++) {
      for (let col = 0; col < GRID; col++) {
        if (!cells[row][col]) continue;
        const x = ox + col * cell;
        const y = oy + row * cell;
        const pad = cell * 0.12;
        roundedRect(ctx, x + pad, y + pad, cell - pad * 2, cell - pad * 2, radius);
        ctx.fill();
      }
    }
  } else {
    for (let vy = 0; vy <= GRID; vy++) {
      for (let vx = 0; vx <= GRID; vx++) {
        if (!vertexLit(cells, vx, vy)) continue;
        const cx = ox + vx * cell;
        const cy = oy + vy * cell;
        ctx.beginPath();
        ctx.fillStyle = 'rgba(12,10,9,0.82)';
        ctx.arc(cx, cy, Math.max(1.8, cell * 0.12), 0, Math.PI * 2);
        ctx.fill();
      }
    }
  }

  ctx.fillStyle = 'rgba(12,10,9,0.55)';
  ctx.font = `600 ${Math.round((11 + canvas.width * 0.018) * scale)}px Syne, system-ui`;
  ctx.textAlign = 'left';
  ctx.textBaseline = 'bottom';
  ctx.fillText(meta.label, padding, canvas.height - 14);

  ctx.textAlign = 'right';
  ctx.fillText(char, canvas.width - padding, canvas.height - 14);
}

function roundedRect(ctx, x, y, w, h, r) {
  const rr = Math.min(r, w / 2, h / 2);
  ctx.beginPath();
  ctx.moveTo(x + rr, y);
  ctx.arcTo(x + w, y, x + w, y + h, rr);
  ctx.arcTo(x + w, y + h, x, y + h, rr);
  ctx.arcTo(x, y + h, x, y, rr);
  ctx.arcTo(x, y, x + w, y, rr);
  ctx.closePath();
}

function makeCardCanvas(scale = 1) {
  const canvas = document.createElement('canvas');
  canvas.width = Math.round(CARD_BASE * scale);
  canvas.height = Math.round(CARD_BASE * scale);
  return canvas;
}

function renderToCanvas(char, cells, mode, fontId, scale = 1) {
  const canvas = makeCardCanvas(scale);
  const fontLabel = FONTS.find((f) => f.id === fontId)?.label ?? '';
  drawPracticeCard(canvas, char, cells, mode, {
    label: fontLabel,
  });
  return canvas;
}

async function waitForFonts() {
  if (document.fonts?.load) {
    try {
      await document.fonts.load('600 18px "LXGW WenKai"');
      await document.fonts.load('600 18px "Noto Serif SC"');
    } catch {
      /* ignore */
    }
  }
  if (document.fonts?.ready) {
    try {
      await document.fonts.ready;
    } catch {
      /* ignore */
    }
  }
  await new Promise((r) => setTimeout(r, 120));
}

function setStatus(text) {
  els.statusLine.textContent = text;
}

async function handleGenerate() {
  const raw = els.charInput.value.trim();
  const chars = extractChars(raw);
  if (!chars.length) {
    setStatus('请输入至少一个汉字（空白与重复会自动忽略）。');
    return;
  }

  els.generateBtn.disabled = true;
  els.downloadBtn.disabled = true;
  setStatus('正在渲染…');
  els.gallery.innerHTML = '';
  lastCanvases = [];

  const fontId = els.fontSelect.value;
  const mode = els.modeSelect.value;
  const threshold = Number(els.thresholdRange.value);

  await waitForFonts();

  for (const char of chars) {
    await waitForFonts();
    const cells = sampleGrid(char, getFontStack(fontId), threshold);

    const thumb = renderToCanvas(char, cells, mode, fontId, 1);
    const wrapper = document.createElement('article');
    wrapper.className = 'card';
    wrapper.innerHTML = `<div class="card__meta"><span>96×96 栅格</span><span class="card__char">${char}</span></div>`;
    wrapper.appendChild(thumb);

    const hi = renderToCanvas(char, cells, mode, fontId, 2);
    wrapper.addEventListener('click', () => openLightbox(hi));

    els.gallery.appendChild(wrapper);
    lastCanvases.push(thumb);
  }

  els.cardCount.textContent = `${chars.length} 张`;
  els.downloadBtn.disabled = lastCanvases.length === 0;
  els.generateBtn.disabled = false;

  setStatus(`已生成 ${chars.length} 张卡片。点击图片可放大预览。`);
}

function openLightbox(sourceCanvas) {
  els.lightbox.hidden = false;
  els.lightboxStage.innerHTML = '';
  const big = document.createElement('canvas');
  big.width = sourceCanvas.width;
  big.height = sourceCanvas.height;
  big.getContext('2d')?.drawImage(sourceCanvas, 0, 0);
  els.lightboxStage.appendChild(big);
}

function closeLightbox() {
  els.lightbox.hidden = true;
  els.lightboxStage.innerHTML = '';
}

async function downloadAll() {
  for (let idx = 0; idx < lastCanvases.length; idx++) {
    const canvas = lastCanvases[idx];
    await new Promise((resolve) => {
      canvas.toBlob((blob) => {
        if (!blob) {
          resolve();
          return;
        }
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `练字卡-${String(idx + 1).padStart(2, '0')}.png`;
        a.click();
        URL.revokeObjectURL(url);
        setTimeout(resolve, 220);
      });
    });
  }
}

els.thresholdRange.addEventListener('input', () => {
  els.thresholdValue.textContent = `${els.thresholdRange.value}%`;
});

els.generateBtn.addEventListener('click', () => {
  void handleGenerate();
});

els.downloadBtn.addEventListener('click', () => {
  void downloadAll();
});

els.lightboxClose.addEventListener('click', closeLightbox);
els.lightbox.addEventListener('click', (e) => {
  if (e.target === els.lightbox) closeLightbox();
});

window.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') closeLightbox();
});

initFontSelect();
els.thresholdValue.textContent = `${els.thresholdRange.value}%`;
els.charInput.value = '永和九年';
setStatus('点击「生成卡片」开始。');
