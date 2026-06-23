import { useMemo, useState, type ChangeEvent, type DragEvent } from 'react'
import { ActionBar } from './components/ActionBar'
import { HtmlPreview } from './components/HtmlPreview'
import {
  convertPdfToHtml,
  type HtmlOutputMode,
  type PdfToHtmlResult,
} from './lib/pdfToHtml'

function App() {
  const [activeMode, setActiveMode] = useState<HtmlOutputMode>('layout')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [fileName, setFileName] = useState<string | null>(null)
  const [result, setResult] = useState<PdfToHtmlResult | null>(null)

  const htmlContent = useMemo(() => {
    if (!result) {
      return ''
    }
    return activeMode === 'layout' ? result.layoutHtml : result.readableHtml
  }, [activeMode, result])

  const handleFile = async (file: File) => {
    if (!file.name.toLowerCase().endsWith('.pdf')) {
      setError('请上传 .pdf 文件。')
      return
    }

    setIsLoading(true)
    setError(null)
    setResult(null)
    setFileName(file.name)

    try {
      const parsed = await convertPdfToHtml(file)
      setResult(parsed)
      if (!parsed.hasExtractableText) {
        setError('PDF 已解析，但未提取到可读文本（可能是扫描件或图片型 PDF）。')
      }
    } catch {
      setError('解析 PDF 失败，请确认文件未损坏或尝试其他文件。')
    } finally {
      setIsLoading(false)
    }
  }

  const onInputChange = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) {
      return
    }
    await handleFile(file)
    event.target.value = ''
  }

  const onDrop = async (event: DragEvent<HTMLElement>) => {
    event.preventDefault()
    const file = event.dataTransfer.files?.[0]
    if (!file) {
      return
    }
    await handleFile(file)
  }

  const onDragOver = (event: DragEvent<HTMLElement>) => {
    event.preventDefault()
  }

  return (
    <main className="app-shell">
      <header className="top-header">
        <h1>PDF 转 HTML</h1>
        <p>上传 PDF 后，可在浏览器内生成 HTML（保留排版 / 可读文本）。</p>
      </header>

      <section className="upload-panel" onDrop={onDrop} onDragOver={onDragOver}>
        <label htmlFor="pdf-upload" className="upload-label">
          <strong>点击选择 PDF</strong>
          <span>或拖拽文件到此区域</span>
        </label>
        <input id="pdf-upload" type="file" accept="application/pdf,.pdf" onChange={onInputChange} />
      </section>

      {isLoading && <p className="status">正在解析 PDF，请稍候...</p>}
      {error && <p className="status error">{error}</p>}

      {result && (
        <section className="result-panel">
          <div className="meta">
            <span>文件: {fileName}</span>
            <span>页数: {result.pageCount}</span>
          </div>

          <ActionBar
            mode={activeMode}
            onModeChange={setActiveMode}
            htmlContent={htmlContent}
            fileName={fileName}
          />

          <HtmlPreview htmlContent={htmlContent} mode={activeMode} />
        </section>
      )}
    </main>
  )
}

export default App
