# timeline

  Layout
  - Sticky glassmorphic navbar with filter pills (All / Note / Image / Idea / Event)
  - Vertical timeline with animated gradient line + glowing dots
  - Year group headers as ghost typography
  - Cards reveal with staggered scroll-in animation

  Cards
  - Images (16:7 ratio, hover brightens)
  - Type badge (color-coded per type), date, title, truncated content
  - Hover: lift + colored border glow + bottom accent bar

  Interactions
  - Click any card → view modal (full content + image)
  - "+ Add" button → create modal with title, date, type, content, image URL fields
  - Delete from view modal
  - Filter by type updates timeline live
  - Press n anywhere to open the add modal, Esc to close modals

  Data
  - 8 seed entries across 2025 with real Unsplash images
  - All entries persist to localStorage

  Open the file directly in a browser — no server needed.



# icon-studio.html

  What's inside:

  48 hand-drawn SVG icons across 5 categories:
  - UI (home, settings, user, search, bell, heart, star, lock, eye…)
  - Media (play, pause, camera, mic, image, music…)
  - File (file, folder, upload, download, link, copy, code…)
  - Comm (mail, message, phone, share, send, globe, wifi…)
  - Nav (arrows, chevrons, menu, refresh, zap…)

  Editor controls (right panel):
  - Color picker + hex input + 8 neon swatch presets
  - Stroke width slider (0.5 → 4)
  - Preview size: 32 / 64 / 96 / 128
  - Linecap: Round / Square / Butt
  - Fill mode: Stroke / Fill / Both
  - Live SVG code preview (click to copy)

  Export:
  - SVG download (24×24 viewBox, styled with current settings)
  - PNG at 32px / 64px / 256px

  Navigation:
  - Category filter chips + search bar
  - Selecting an icon glows it cyan and updates the editor instantly


📅 timeline.html — 个人时间线

一个视觉精美的个人记录应用：
- 支持四种内容类型：Note（笔记）/ Idea（想法）/ Event（事件）/ Image（图片）
- 按类型筛选、按年份分组展示
- 数据持久化到 localStorage，刷新不丢失
- 卡片点击查看详情，快捷键 n 新建、Esc 关闭弹窗
- 玻璃拟态 Navbar + 滚动入场动画

🎵 audio-heatmap.html — 音频可视化分析器

拖入一个音频文件，即可看到：
- 能量热力图（waveform heatmap）
- 频谱图（spectrogram，类似 Audacity）
- 支持播放 + 时间轴拖拽定位
- 完全用原生 Web Audio API 实现，FFT 是手写的 Cooley–Tukey 基-2 算法，零外部依赖

🎨 icon-studio.html — SVG 图标编辑器

48 个手绘风格 SVG 图标，配备实时编辑器：
- 调整颜色、描边宽度、线帽样式、填充模式
- 实时预览 SVG 代码
- 导出为 SVG 或 PNG（32 / 64 / 256px）