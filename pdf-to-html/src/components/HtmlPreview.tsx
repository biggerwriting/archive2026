import type { HtmlOutputMode } from '../lib/pdfToHtml'

interface HtmlPreviewProps {
  htmlContent: string
  mode: HtmlOutputMode
}

export function HtmlPreview({ htmlContent, mode }: HtmlPreviewProps) {
  return (
    <section className="preview-panel">
      <header>
        <h2>HTML 预览</h2>
        <span>{mode === 'layout' ? '当前模式: 保留排版' : '当前模式: 可读文本'}</span>
      </header>

      <div className="preview-content">
        <iframe title="HTML preview" srcDoc={htmlContent} />
      </div>

      <details>
        <summary>查看 HTML 源码</summary>
        <pre>{htmlContent}</pre>
      </details>
    </section>
  )
}
