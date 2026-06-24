# 语音提醒音频

当前使用微信 wx.textToSpeech（AI 语音合成）动态生成语音，无需本地 mp3 文件。

若需离线语音（方案 B），可将以下 5 个 mp3 文件放入此目录：
- posture_bad.mp3   — 「请调整坐姿，抬头挺胸」
- lying_down.mp3    — 「请不要趴着，小心眼睛近视」
- take_break.mp3    — 「已持续坐了 X 分钟，站起来活动一下吧」
- badge_earned.mp3  — 「恭喜解锁勋章」
- posture_good.mp3  — 「很好，继续保持」

并将 AlertService._playAudio 改回 mp3 模式（取消注释 AUDIO_FILES 映射部分）。
