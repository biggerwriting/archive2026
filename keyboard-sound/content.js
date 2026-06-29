// content.js — 按键监听与音频播放
// 通过 content_scripts 注入到每个网页，note-engine.js 先于本文件加载

(() => {
  // ── 状态缓存 ──────────────────────────────────────────────────
  let state = {
    enabled:   true,
    soundMode: 'piano',    // 'piano' | 'typewriter'
    noteMode:  'fixed',    // 'fixed' | 'sequential' | 'random'
    volume:    0.75,
    seqIndex:  0           // sequential 模式指针
  };

  // ── AudioContext（懒加载，首次按键时创建）───────────────────────
  let audioCtx = null;
  let gainNode = null;

  function getAudioCtx() {
    if (!audioCtx) {
      audioCtx = new (window.AudioContext || window.webkitAudioContext)();
      gainNode = audioCtx.createGain();
      gainNode.gain.value = state.volume;
      gainNode.connect(audioCtx.destination);
    }
    return audioCtx;
  }

  // ── WebAudioFont 钢琴（懒加载）──────────────────────────────────
  let pianoPlayer = null;
  let pianoPreset = null;
  let pianoLoading = false;

  function loadPiano() {
    if (pianoPlayer || pianoLoading) return;
    pianoLoading = true;

    // 动态注入 webaudiofont-player.js
    const playerScript = document.createElement('script');
    playerScript.src = chrome.runtime.getURL('assets/piano/webaudiofont-player.js');
    playerScript.onload = () => {
      // 动态注入 piano.js（音色数据）
      const presetScript = document.createElement('script');
      presetScript.src = chrome.runtime.getURL('assets/piano/piano.js');
      presetScript.onload = () => {
        const ctx = getAudioCtx();
        pianoPlayer = new window.WebAudioFontPlayer();
        pianoPreset = window._tone_0000_Aspirin_sf2_file;
        pianoPlayer.loader.decodeAfterLoading(ctx, '_tone_0000_Aspirin_sf2_file');
        pianoLoading = false;
      };
      document.head.appendChild(presetScript);
    };
    document.head.appendChild(playerScript);
  }

  // ── 打字机音效（预加载 AudioBuffer）────────────────────────────
  const typewriterBuffers = { key: null, space: null, enter: null };
  let typewriterLoaded = false;

  async function loadTypewriter() {
    if (typewriterLoaded) return;
    typewriterLoaded = true;
    const ctx = getAudioCtx();
    const files = { key: 'key.wav', space: 'space.wav', enter: 'enter.wav' };
    await Promise.all(Object.entries(files).map(async ([name, file]) => {
      try {
        const url = chrome.runtime.getURL(`assets/typewriter/${file}`);
        const resp = await fetch(url);
        const arrayBuf = await resp.arrayBuffer();
        typewriterBuffers[name] = await ctx.decodeAudioData(arrayBuf);
      } catch (e) {
        console.warn(`[KeyboardSound] Failed to load ${file}:`, e);
      }
    }));
  }

  // ── 播放函数 ────────────────────────────────────────────────────
  function playPiano(pitch) {
    if (!pianoPlayer || !pianoPreset) return;
    const ctx = getAudioCtx();
    gainNode.gain.value = state.volume;
    pianoPlayer.queueWaveTable(ctx, gainNode, pianoPreset, 0, pitch, 1.5);
  }

  function playTypewriterBuffer(buffer) {
    if (!buffer) return;
    const ctx = getAudioCtx();
    gainNode.gain.value = state.volume;
    const source = ctx.createBufferSource();
    source.buffer = buffer;
    source.connect(gainNode);
    source.start();
  }

  function playTypewriter(keyValue) {
    const k = keyValue.toLowerCase();
    if (k === ' ') {
      playTypewriterBuffer(typewriterBuffers.space);
    } else if (k === 'enter' || k === 'backspace') {
      playTypewriterBuffer(typewriterBuffers.enter);
    } else {
      playTypewriterBuffer(typewriterBuffers.key);
    }
  }

  // ── 判断是否在可输入元素中 ──────────────────────────────────────
  function isTypingTarget(el) {
    if (!el) return false;
    const tag = el.tagName.toLowerCase();
    if (tag === 'input' || tag === 'textarea') return true;
    if (el.isContentEditable) return true;
    return false;
  }

  // ── keydown 监听 ─────────────────────────────────────────────
  document.addEventListener('keydown', (e) => {
    if (!state.enabled) return;
    if (!isTypingTarget(document.activeElement)) return;

    if (state.soundMode === 'piano') {
      // 懒加载钢琴资源
      if (!pianoPlayer && !pianoLoading) loadPiano();

      const { pitch, nextState } = getNoteForKey(e.key, state.noteMode, { seqIndex: state.seqIndex });
      state.seqIndex = nextState.seqIndex;
      if (pitch !== null) playPiano(pitch);

    } else {
      // 懒加载打字机音效
      if (!typewriterLoaded) loadTypewriter();
      playTypewriter(e.key);
    }
  }, true); // 捕获阶段

  // ── 读取初始状态 ─────────────────────────────────────────────
  chrome.storage.local.get(['enabled', 'soundMode', 'noteMode', 'volume'], (result) => {
    if (result.enabled   !== undefined) state.enabled   = result.enabled;
    if (result.soundMode !== undefined) state.soundMode = result.soundMode;
    if (result.noteMode  !== undefined) state.noteMode  = result.noteMode;
    if (result.volume    !== undefined) state.volume    = result.volume;
  });

  // ── 实时监听 storage 变化 ────────────────────────────────────
  chrome.storage.onChanged.addListener((changes) => {
    if (changes.enabled   !== undefined) state.enabled   = changes.enabled.newValue;
    if (changes.soundMode !== undefined) state.soundMode = changes.soundMode.newValue;
    if (changes.noteMode  !== undefined) state.noteMode  = changes.noteMode.newValue;
    if (changes.volume    !== undefined) state.volume    = changes.volume.newValue;
  });

})();
