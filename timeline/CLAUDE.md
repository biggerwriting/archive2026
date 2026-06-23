# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**History Mark** is a collection of standalone single-file HTML apps. Each file is fully self-contained (inline CSS + JS, no build step, no server, no dependencies beyond Google Fonts). Open any file directly in a browser.

## Files

| File | Purpose |
|---|---|
| `timeline.html` | Personal timeline — CRUD entries (note/idea/event/image), persisted to `localStorage`, filter by type, modal view/create/edit |
| `audio-heatmap.html` | Audio visualizer — drag-and-drop audio file → renders waveform energy heatmap + spectrogram via Web Audio API and a hand-rolled radix-2 FFT |
| `icon-studio.html` | SVG icon browser — 48 hand-drawn icons across 5 categories, live editor (color, stroke, linecap, fill), export as SVG or PNG |
| `mock-timeline.html` | Minimal unstyled prototype of the timeline rendering logic (seed data only, no persistence) |
| `API.md` | REST API spec for a future backend to replace `localStorage` in `timeline.html` |

## Design System

All HTML files share the same visual language:

- **Fonts**: `JetBrains Mono` (monospace labels, code, badges) + `Space Grotesk` (body text)
- **Color palette** (CSS custom properties on `:root`):
  - Background layers: `--bg: #0b0d11`, `--surface: #13161d`, `--surface2: #1a1e28`
  - Border: `--border: #252a38`
  - Text: `--text: #e2e6f0`, `--muted: #6b7390`
  - Accent colors: `--cyan: #00e5ff`, `--purple: #b57bff`, `--lime: #a3e635`, `--amber: #fbbf24`, `--coral: #ff6b6b`
- **Aesthetic**: dark glassmorphic, neon glow on hover/focus (`box-shadow: 0 0 Xpx var(--cyan)`), `backdrop-filter: blur(...)` navbar
- Type badge accent colors map: `note → cyan`, `idea → purple`, `event → amber`, `image → lime`

## Architecture Notes

### `timeline.html`
- State: `entries[]` array + `activeFilter`, `editingId`, `viewingId` globals
- Persistence: `localStorage` key `timeline_entries`; `save()` serializes on every mutation
- Rendering: imperative `render()` rebuilds the DOM from scratch; scroll-in animations via `IntersectionObserver`
- Modals: one add/edit modal (form reused for both), one view modal; toggled by adding/removing CSS classes
- Keyboard: `n` opens add modal, `Escape` closes any open modal
- **Backend migration path**: `API.md` documents the REST API (`/api/v1/timeline-entries`) to replace `localStorage`. Fields map 1-to-1 (`id`, `title`, `date`, `type`, `content`, `image`).

### `audio-heatmap.html`
- Uses Web Audio API: `AudioContext.decodeAudioData()` to decode the file, then reads raw PCM from `AudioBuffer`
- **STFT / spectrogram**: computed manually in JS — a hand-rolled Cooley–Tukey radix-2 in-place FFT (`fft()` function); no external library
- Three `<canvas>` elements: `#heatmapCanvas` (energy heatmap, bottom layer), `#waveCanvas` (waveform overlay), `#specCanvas` (spectrogram below)
- Playback via a `AudioBufferSourceNode` re-created on each play; scrubbing seeks by restarting the source at the target offset
- Color themes selectable at runtime; heatmap and spectrogram re-render on theme change

### `icon-studio.html`
- All 48 SVG icons are defined inline as JS data (path `d` strings)
- Editor state is plain object; changing any control calls `renderPreview()` which regenerates the SVG string
- PNG export uses an off-screen `<canvas>` painted with the SVG via `drawImage`

## Adding a New Page

Follow the established pattern:
1. Copy the `:root` CSS variable block and font `<link>` tags from an existing file
2. Use the same navbar markup (`.logo` + `.nav-right`) with sticky glassmorphic styling
3. Keep all CSS/JS inline — no external script files
