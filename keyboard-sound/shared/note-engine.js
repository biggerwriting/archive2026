// shared/note-engine.js
// 纯函数模块：根据按键和模式选择要播放的音符
// 不依赖任何外部 API，可在 content.js 和测试中直接使用

/**
 * C 大调音阶音符（顺序循环和随机模式使用）
 * MIDI pitch 值：C4=60, D4=62, E4=64, F4=65, G4=67, A4=69, B4=71
 *               C5=72, D5=74, E5=76, F5=77, G5=79, A5=81, B5=83
 */
const C_MAJOR_SCALE = [60, 62, 64, 65, 67, 69, 71, 72, 74, 76, 77, 79, 81, 83];

/**
 * 固定映射：A-Z → C4-B5（26个键对应26个音），数字 0-9 → C3-B3（10个音）
 * A=C4(60), B=D4(62), C=E4(64), D=F4(65), E=G4(67), F=A4(69), G=B4(71),
 * H=C5(72), I=D5(74), J=E5(76), K=F5(77), L=G5(79), M=A5(81), N=B5(83),
 * O=C6(84) ... Z=E7(100) — 超出范围时钢琴自动处理高八度
 */
const ALPHA_TO_PITCH = {};
const ALPHA_BASE = 60; // C4
const ALPHA_SEMITONES = [0,2,4,5,7,9,11,12,14,16,17,19,21,23,24,26,28,29,31,33,35,36,38,40,41,43];
'abcdefghijklmnopqrstuvwxyz'.split('').forEach((ch, i) => {
  ALPHA_TO_PITCH[ch] = ALPHA_BASE + ALPHA_SEMITONES[i];
});

const DIGIT_TO_PITCH = {};
const DIGIT_BASE = 48; // C3
const DIGIT_SEMITONES = [0,2,4,5,7,9,11,12,14,16];
'0123456789'.split('').forEach((ch, i) => {
  DIGIT_TO_PITCH[ch] = DIGIT_BASE + DIGIT_SEMITONES[i];
});

/**
 * getNoteForKey — 核心接口
 *
 * @param {string} keyValue  - event.key 的值（如 "a", "Enter", " "）
 * @param {string} mode      - "fixed" | "sequential" | "random"
 * @param {object} state     - { seqIndex: number }
 * @returns {{ pitch: number|null, nextState: object }}
 *   pitch: MIDI 音高值（如 60 = C4），null 表示不播放
 *   nextState: 更新后的状态（sequential 模式会递增 seqIndex）
 */
function getNoteForKey(keyValue, mode, state) {
  const k = keyValue.toLowerCase();
  const nextState = { ...state };

  // 过滤修饰键和功能键
  const IGNORED_KEYS = new Set([
    'shift','control','alt','meta','capslock','tab','escape',
    'arrowup','arrowdown','arrowleft','arrowright',
    'home','end','pageup','pagedown','insert','delete',
    'f1','f2','f3','f4','f5','f6','f7','f8','f9','f10','f11','f12'
  ]);
  if (IGNORED_KEYS.has(k)) {
    return { pitch: null, nextState };
  }

  if (mode === 'fixed') {
    let pitch = null;
    if (ALPHA_TO_PITCH[k] !== undefined) {
      pitch = ALPHA_TO_PITCH[k];
    } else if (DIGIT_TO_PITCH[k] !== undefined) {
      pitch = DIGIT_TO_PITCH[k];
    } else {
      // 空格、回车、标点等映射到 C4
      pitch = 60;
    }
    return { pitch, nextState };
  }

  if (mode === 'sequential') {
    const idx = (state.seqIndex || 0) % C_MAJOR_SCALE.length;
    const pitch = C_MAJOR_SCALE[idx];
    nextState.seqIndex = idx + 1;
    return { pitch, nextState };
  }

  if (mode === 'random') {
    const idx = Math.floor(Math.random() * C_MAJOR_SCALE.length);
    return { pitch: C_MAJOR_SCALE[idx], nextState };
  }

  return { pitch: null, nextState };
}

// 导出（content script 环境下直接挂到 window，测试环境支持 module.exports）
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { getNoteForKey, C_MAJOR_SCALE, ALPHA_TO_PITCH, DIGIT_TO_PITCH };
}
