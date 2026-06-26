const fs = require('fs');
const path = require('path');

// 简单的 Markdown 到 HTML 转换器
function markdownToHtml(markdown) {
    let html = markdown;

    // 标题转换
    html = html.replace(/^### (.*$)/gim, '<h3>$1</h3>');
    html = html.replace(/^## (.*$)/gim, '<h2>$1</h2>');
    html = html.replace(/^# (.*$)/gim, '<h1>$1</h1>');

    // 粗体和斜体
    html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    html = html.replace(/\*(.*?)\*/g, '<em>$1</em>');

    // 代码块
    html = html.replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>');
    html = html.replace(/`(.*?)`/g, '<code>$1</code>');

    // 链接
    html = html.replace(/\[([^\]]*)\]\(([^\)]*)\)/g, '<a href="$2">$1</a>');

    // 图片
    html = html.replace(/!\[([^\]]*)\]\(([^\)]*)\)/g, '<img src="$2" alt="$1">');

    // 列表（支持 * 和 - 两种前缀）
    html = html.replace(/^[\*\-] (.*$)/gim, '<li>$1</li>');
    // 将连续的 <li> 行整体包裹进 <ul>
    html = html.replace(/(<li>.*?<\/li>\n?)+/g, (match) => `<ul>\n${match}</ul>`);

    // 段落（先保护代码块，防止其内容被包进 <p> 标签）
    const codeBlocks = [];
    html = html.replace(/<pre><code>[\s\S]*?<\/code><\/pre>/g, (match) => {
        codeBlocks.push(match);
        return `\x00CODEBLOCK${codeBlocks.length - 1}\x00`;
    });
    html = html.replace(/^(?!<[h|u|l|p|\/])(.*$)/gim, '<p>$1</p>');
    html = html.replace(/\x00CODEBLOCK(\d+)\x00/g, (_, i) => codeBlocks[+i]);

    // 清理多余的段落标签
    html = html.replace(/<p><h/g, '<h');
    html = html.replace(/<\/h([1-6])><\/p>/g, '</h$1>');
    html = html.replace(/<p><ul>/g, '<ul>');
    html = html.replace(/<\/ul><\/p>/g, '</ul>');
    html = html.replace(/<p><pre>/g, '<pre>');
    html = html.replace(/<\/pre><\/p>/g, '</pre>');

    return html;
}

// 生成完整的 HTML 文档
function createHtmlDocument(content, title = 'Markdown Document') {
    return `<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>${title}</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            max-width: 800px;
            margin: 40px auto;
            padding: 0 20px;
            color: #333;
            background: #fff;
        }
        h1, h2, h3 {
            color: #2c3e50;
            margin-top: 2em;
            margin-bottom: 0.5em;
        }
        h1 {
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }
        h2 {
            border-bottom: 2px solid #3498db;
            padding-bottom: 5px;
        }
        code {
            background: #f4f4f4;
            padding: 2px 6px;
            border-radius: 4px;
            font-family: 'SF Mono', Monaco, monospace;
            font-size: 0.9em;
        }
        pre {
            background: #f8f8f8;
            padding: 15px;
            border-radius: 8px;
            overflow-x: auto;
            border: 1px solid #e1e1e1;
        }
        pre code {
            background: none;
            padding: 0;
        }
        ul {
            padding-left: 20px;
        }
        li {
            margin: 5px 0;
        }
        p {
            margin: 1em 0;
        }
        a {
            color: #3498db;
            text-decoration: none;
        }
        a:hover {
            text-decoration: underline;
        }
        blockquote {
            border-left: 4px solid #3498db;
            margin: 1em 0;
            padding-left: 20px;
            color: #666;
        }
        @media (max-width: 768px) {
            body {
                margin: 20px auto;
                padding: 0 15px;
            }
            h1 {
                font-size: 1.8em;
            }
            h2 {
                font-size: 1.5em;
            }
        }
    </style>
</head>
<body>
${content}
</body>
</html>`;
}

// 主函数
function convertMarkdownToHtml(markdownFile, outputFile = null) {
    try {
        // 读取 Markdown 文件
        const markdown = fs.readFileSync(markdownFile, 'utf8');

        // 转换为 HTML
        const htmlContent = markdownToHtml(markdown);

        // 获取文件名作为标题
        const title = path.basename(markdownFile, '.md');

        // 生成完整的 HTML 文档
        const fullHtml = createHtmlDocument(htmlContent, title);

        // 确定输出文件名
        if (!outputFile) {
            outputFile = markdownFile.replace('.md', '.html');
        }

        // 写入 HTML 文件
        fs.writeFileSync(outputFile, fullHtml, 'utf8');

        console.log(`✅ 转换完成！`);
        console.log(`📄 Markdown: ${markdownFile}`);
        console.log(`🌐 HTML: ${outputFile}`);

        return outputFile;
    } catch (error) {
        console.error('❌ 转换失败:', error.message);
        return null;
    }
}

// 如果直接运行此脚本
if (require.main === module) {
    const args = process.argv.slice(2);
    if (args.length === 0) {
        console.log('使用方法: node convert-md-to-html.js <markdown文件> [输出文件]');
        console.log('示例: node convert-md-to-html.js README.md');
        process.exit(1);
    }

    const markdownFile = args[0];
    const outputFile = args[1] || null;

    convertMarkdownToHtml(markdownFile, outputFile);
}

module.exports = { convertMarkdownToHtml, markdownToHtml, createHtmlDocument };