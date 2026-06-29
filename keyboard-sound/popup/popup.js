// popup/popup.js — 控制面板交互逻辑

document.addEventListener('DOMContentLoaded', () => {
  const enabledToggle    = document.getElementById('enabledToggle');
  const controls         = document.getElementById('controls');
  const soundBtns        = document.querySelectorAll('.mode-btn');
  const noteBtns         = document.querySelectorAll('.note-btn');
  const noteModeSection  = document.getElementById('noteModeSection');
  const volumeSlider     = document.getElementById('volumeSlider');
  const volumeVal        = document.getElementById('volumeVal');

  // ── 从 storage 读取状态并初始化 UI ────────────────────────────
  chrome.storage.local.get(['enabled', 'soundMode', 'noteMode', 'volume'], (result) => {
    const enabled   = result.enabled   !== undefined ? result.enabled   : true;
    const soundMode = result.soundMode !== undefined ? result.soundMode : 'piano';
    const noteMode  = result.noteMode  !== undefined ? result.noteMode  : 'fixed';
    const volume    = result.volume    !== undefined ? result.volume    : 0.75;

    enabledToggle.checked = enabled;
    controls.classList.toggle('disabled', !enabled);

    soundBtns.forEach(b => b.classList.toggle('active', b.dataset.sound === soundMode));
    noteBtns.forEach(b  => b.classList.toggle('active', b.dataset.note  === noteMode));
    noteModeSection.classList.toggle('hidden', soundMode === 'typewriter');

    volumeSlider.value = Math.round(volume * 100);
    volumeVal.textContent = Math.round(volume * 100) + '%';
  });

  // ── 主开关 ────────────────────────────────────────────────────
  enabledToggle.addEventListener('change', () => {
    const enabled = enabledToggle.checked;
    controls.classList.toggle('disabled', !enabled);
    chrome.storage.local.set({ enabled });
  });

  // ── 音色切换 ──────────────────────────────────────────────────
  soundBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      soundBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const soundMode = btn.dataset.sound;
      noteModeSection.classList.toggle('hidden', soundMode === 'typewriter');
      chrome.storage.local.set({ soundMode });
    });
  });

  // ── 音符模式切换 ──────────────────────────────────────────────
  noteBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      noteBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      chrome.storage.local.set({ noteMode: btn.dataset.note });
    });
  });

  // ── 音量滑块 ──────────────────────────────────────────────────
  volumeSlider.addEventListener('input', () => {
    const volume = volumeSlider.value / 100;
    volumeVal.textContent = volumeSlider.value + '%';
    chrome.storage.local.set({ volume });
  });
});
