// background.js — Service Worker
// 仅在扩展安装时初始化默认 storage 值

chrome.runtime.onInstalled.addListener(() => {
  chrome.storage.local.get(['enabled', 'soundMode', 'noteMode', 'volume'], (result) => {
    const defaults = {};
    if (result.enabled === undefined)   defaults.enabled   = true;
    if (result.soundMode === undefined) defaults.soundMode = 'piano';
    if (result.noteMode === undefined)  defaults.noteMode  = 'fixed';
    if (result.volume === undefined)    defaults.volume    = 0.75;
    if (Object.keys(defaults).length > 0) {
      chrome.storage.local.set(defaults);
    }
  });
});
