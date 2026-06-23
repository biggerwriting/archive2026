import {
  GlobalWorkerOptions,
  getDocument,
} from 'pdfjs-dist'

GlobalWorkerOptions.workerSrc = new URL(
  'pdfjs-dist/build/pdf.worker.min.mjs',
  import.meta.url,
).toString()

export type HtmlOutputMode = 'layout' | 'readable'

export interface PdfToHtmlResult {
  layoutHtml: string
  readableHtml: string
  pageCount: number
  hasExtractableText: boolean
}

interface LayoutTextBlock {
  str: string
  x: number
  top: number
  fontSize: number
}

interface ReadableTextBlock {
  str: string
  x: number
  y: number
  fontSize: number
}

const DEFAULT_FONT_SIZE = 12

interface PdfTextItem {
  str: string
  transform: number[]
  height?: number
}

function isTextItem(item: unknown): item is PdfTextItem {
  if (!item || typeof item !== 'object') {
    return false
  }
  if (!('str' in item) || !('transform' in item)) {
    return false
  }
  const maybeText = item as { str: unknown; transform: unknown }
  return typeof maybeText.str === 'string' && Array.isArray(maybeText.transform)
}

function escapeHtml(input: string): string {
  return input
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;')
}

function createLayoutHtml(pages: string[]): string {
  return [
    '<!doctype html>',
    '<html lang="en">',
    '<head>',
    '  <meta charset="utf-8" />',
    '  <meta name="viewport" content="width=device-width, initial-scale=1" />',
    '  <title>PDF to HTML (Layout)</title>',
    '  <style>',
    '    body { margin: 0; padding: 24px; background: #f6f7fb; font-family: Arial, sans-serif; }',
    '    .pdf-layout-document { display: grid; gap: 24px; justify-content: center; }',
    '    .pdf-layout-page { position: relative; background: #fff; box-shadow: 0 2px 12px rgba(0,0,0,0.12); overflow: hidden; }',
    '    .pdf-layout-text { position: absolute; white-space: pre; color: #111; transform-origin: left top; }',
    '  </style>',
    '</head>',
    '<body>',
    '  <article class="pdf-layout-document">',
    ...pages,
    '  </article>',
    '</body>',
    '</html>',
  ].join('\n')
}

function createReadableHtml(paragraphs: string[]): string {
  const paragraphHtml =
    paragraphs.length > 0
      ? paragraphs.map((text) => `    <p>${escapeHtml(text)}</p>`).join('\n')
      : '    <p>[No text content could be extracted from this PDF.]</p>'

  return [
    '<!doctype html>',
    '<html lang="en">',
    '<head>',
    '  <meta charset="utf-8" />',
    '  <meta name="viewport" content="width=device-width, initial-scale=1" />',
    '  <title>PDF to HTML (Readable)</title>',
    '  <style>',
    '    body { margin: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Arial, sans-serif; background: #fff; color: #111; }',
    '    article { max-width: 900px; margin: 40px auto; padding: 0 24px 64px; line-height: 1.65; font-size: 18px; }',
    '    h1 { line-height: 1.2; font-size: 28px; margin: 0 0 24px; }',
    '    p { margin: 0 0 16px; }',
    '  </style>',
    '</head>',
    '<body>',
    '  <article>',
    '    <h1>PDF Text Content</h1>',
    paragraphHtml,
    '  </article>',
    '</body>',
    '</html>',
  ].join('\n')
}

function lineToText(line: ReadableTextBlock[]): string {
  const sorted = [...line].sort((a, b) => a.x - b.x)
  const parts: string[] = []

  for (const part of sorted) {
    const value = part.str.trim()
    if (!value) {
      continue
    }
    if (parts.length === 0) {
      parts.push(value)
      continue
    }
    const prev = parts[parts.length - 1]
    if (/^[,.;:!?)]/.test(value) || /[(]$/.test(prev)) {
      parts[parts.length - 1] = `${prev}${value}`
    } else {
      parts.push(value)
    }
  }

  return parts.join(' ')
}

export async function convertPdfToHtml(file: File): Promise<PdfToHtmlResult> {
  const fileBytes = await file.arrayBuffer()
  const loadingTask = getDocument({ data: fileBytes })
  const pdfDoc = await loadingTask.promise

  const layoutPages: string[] = []
  const readableBlocks: ReadableTextBlock[] = []

  for (let pageNumber = 1; pageNumber <= pdfDoc.numPages; pageNumber += 1) {
    const page = await pdfDoc.getPage(pageNumber)
    const viewport = page.getViewport({ scale: 1 })
    const content = await page.getTextContent()

    const pageBlocks: LayoutTextBlock[] = []
    const pageReadableBlocks: ReadableTextBlock[] = []

    for (const item of content.items) {
      if (!isTextItem(item)) {
        continue
      }

      const text = item.str
      if (!text.trim()) {
        continue
      }

      const x = item.transform[4]
      const y = viewport.height - item.transform[5]
      const fontSize =
        Math.hypot(item.transform[0], item.transform[1]) ||
        item.height ||
        DEFAULT_FONT_SIZE

      pageBlocks.push({
        str: text,
        x,
        top: Math.max(0, y - fontSize),
        fontSize,
      })

      pageReadableBlocks.push({
        str: text,
        x,
        y: item.transform[5],
        fontSize,
      })
    }

    const textSpans = pageBlocks
      .map(
        (block) =>
          `<span class="pdf-layout-text" style="left:${block.x.toFixed(2)}px;top:${block.top.toFixed(2)}px;font-size:${block.fontSize.toFixed(2)}px;">${escapeHtml(block.str)}</span>`,
      )
      .join('')

    layoutPages.push(
      `<section class="pdf-layout-page" style="width:${viewport.width.toFixed(2)}px;height:${viewport.height.toFixed(2)}px;">${textSpans}</section>`,
    )

    readableBlocks.push(...pageReadableBlocks)
  }

  const sortedBlocks = [...readableBlocks].sort((a, b) => {
    if (Math.abs(a.y - b.y) > 1.5) {
      return b.y - a.y
    }
    return a.x - b.x
  })

  const lines: ReadableTextBlock[][] = []
  for (const block of sortedBlocks) {
    const currentLine = lines[lines.length - 1]
    if (!currentLine) {
      lines.push([block])
      continue
    }

    const currentY = currentLine[0].y
    const tolerance = Math.max(2, block.fontSize * 0.35)
    if (Math.abs(block.y - currentY) <= tolerance) {
      currentLine.push(block)
      continue
    }
    lines.push([block])
  }

  const paragraphs: string[] = []
  let paragraphParts: string[] = []
  let previousY: number | null = null
  let previousFontSize = DEFAULT_FONT_SIZE

  for (const line of lines) {
    const lineText = lineToText(line)
    if (!lineText) {
      continue
    }

    const currentY = line[0].y
    const currentFontSize = line[0].fontSize
    const lineGap = previousY === null ? 0 : previousY - currentY
    const paragraphBreakThreshold = Math.max(previousFontSize, currentFontSize) * 1.55

    if (previousY !== null && lineGap > paragraphBreakThreshold && paragraphParts.length) {
      paragraphs.push(paragraphParts.join(' ').replace(/\s+/g, ' ').trim())
      paragraphParts = []
    }

    paragraphParts.push(lineText)
    previousY = currentY
    previousFontSize = currentFontSize
  }

  if (paragraphParts.length > 0) {
    paragraphs.push(paragraphParts.join(' ').replace(/\s+/g, ' ').trim())
  }

  const hasExtractableText = paragraphs.some((text) => text.length > 0)

  return {
    layoutHtml: createLayoutHtml(layoutPages),
    readableHtml: createReadableHtml(paragraphs),
    pageCount: pdfDoc.numPages,
    hasExtractableText,
  }
}
