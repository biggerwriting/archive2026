import { useMemo, useState } from 'react'
import type { HtmlOutputMode } from '../lib/pdfToHtml'

interface ActionBarProps {
  mode: HtmlOutputMode
  onModeChange: (mode: HtmlOutputMode) => void
  htmlContent: string
  fileName: string | null
}

function getOutputFileName(fileName: string | null, mode: HtmlOutputMode): string {
  const baseName = fileName ? fileName.replace(/\.pdf$/i, '') : 'pdf-output'
  return `${baseName}-${mode}.html`
}

export function ActionBar({
  mode,
  onModeChange,
  htmlContent,
  fileName,
}: ActionBarProps) {
  const [copyState, setCopyState] = useState<'idle' | 'success' | 'error'>('idle')
  const downloadName = useMemo(() => getOutputFileName(fileName, mode), [fileName, mode])

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(htmlContent)
      setCopyState('success')
    } catch {
      setCopyState('error')
    }
    window.setTimeout(() => setCopyState('idle'), 1500)
  }

  const handleDownload = () => {
    const blob = new Blob([htmlContent], { type: 'text/html;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = downloadName
    link.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="action-bar">
      <div className="mode-switch">
        <button
          type="button"
          className={mode === 'layout' ? 'active' : ''}
          onClick={() => onModeChange('layout')}
        >
          保留排版
        </button>
        <button
          type="button"
          className={mode === 'readable' ? 'active' : ''}
          onClick={() => onModeChange('readable')}
        >
          可读文本
        </button>
      </div>

      <div className="action-buttons">
        <button type="button" onClick={handleCopy}>
          {copyState === 'success' && '已复制'}
          {copyState === 'error' && '复制失败'}
          {copyState === 'idle' && '复制 HTML'}
        </button>
        <button type="button" onClick={handleDownload}>
          下载 HTML
        </button>
      </div>
    </div>
  )
}
