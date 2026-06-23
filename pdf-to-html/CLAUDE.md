# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A browser-based PDF to HTML converter built with React + TypeScript + Vite. Converts PDF files entirely client-side using Mozilla's PDF.js library, with two output modes:
- **Layout mode**: Preserves exact PDF positioning using absolute positioning
- **Readable mode**: Extracts and intelligently formats text content for reading

## Development Commands

```bash
npm run dev      # Start dev server (Vite HMR enabled)
npm run build    # Type-check with tsc, then build for production
npm run lint     # Run ESLint on all TypeScript files
npm run preview  # Preview production build locally
```

## Architecture

### Core Conversion Flow (`src/lib/pdfToHtml.ts`)

The PDF parsing pipeline:
1. **Load PDF**: Use `pdfjs-dist` to parse PDF binary into document object
2. **Extract per-page text items**: Each item contains `str` (text), `transform` (position matrix), `height`
3. **Generate two HTML outputs simultaneously**:
   - **Layout HTML**: Position each text item absolutely at `(x, y)` with original font size
   - **Readable HTML**: Sort text items by Y-coordinate (top-to-bottom), group into lines, merge into paragraphs

### Text-to-Paragraph Algorithm

Key logic for readable mode (lines 202-254 in `pdfToHtml.ts`):
- Sort text blocks by Y-coordinate (descending) then X-coordinate
- Group blocks into lines using Y-coordinate tolerance (`fontSize * 0.35`)
- Merge lines into paragraphs when line gap exceeds `fontSize * 1.55`
- Handle punctuation merging (commas, periods adjacent to words)

### Component Structure

- **App.tsx**: Main orchestrator - file upload (click/drag), state management, error handling
- **ActionBar.tsx**: Mode toggle, copy to clipboard, download HTML file
- **HtmlPreview.tsx**: iframe preview + collapsible source code view

### PDF.js Worker Configuration

Worker is loaded from `pdfjs-dist/build/pdf.worker.min.mjs` using `import.meta.url` (line 6-9 in `pdfToHtml.ts`). This is required for PDF.js to work in browsers.

## TypeScript Configuration

- Strict mode enabled with additional checks (`noUnusedLocals`, `noUnusedParameters`)
- Uses `bundler` module resolution (Vite-specific)
- `verbatimModuleSyntax` enforced - use `import type` for type-only imports

## Styling Approach

Global styles in `src/index.css` define the app shell, upload panel, and preview components. No CSS modules or CSS-in-JS - plain CSS with BEM-like class naming.

## Known Limitations

- Only works with PDFs containing text layers (not scanned images)
- Complex layouts (tables, multi-column) may not convert perfectly to readable mode
- No image/vector graphics extraction
