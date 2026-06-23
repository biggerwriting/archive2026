# Chrome 英语生词本插件

一个轻量级 Chrome 扩展：在网页中选中英文单词，按快捷键即可保存到生词库，并自动记录包含该词的句子。

## 功能

- 选中单词后按快捷键保存（默认：`Alt + Shift + A`）。
- 自动抓取上下文句子并与单词关联。
- 同一单词在多个句子中出现时，聚合到同一个词条下，句子自动去重。
- 独立页面展示 `单词 | 句子` 列表。
- 一键导出 Markdown 文件到本地。

## 安装（开发者模式）

1. 打开 Chrome，进入 `chrome://extensions/`。
2. 打开右上角「开发者模式」。
3. 点击「加载已解压的扩展程序」。
4. 选择本项目目录。

## 使用

1. 打开任意网页，选中一个英文单词。
2. 按 `Alt + Shift + A`（Mac 上也是该组合）保存到生词本。
3. 点击扩展图标可打开生词本页面查看历史记录。
4. 在生词本页面点击「导出 Markdown」下载 `.md` 文件。

## 修改快捷键

1. 打开 `chrome://extensions/shortcuts`。
2. 找到本扩展的 `Add selected word to wordbook`。
3. 设置你想要的快捷键组合。

> 说明：Chrome 对「单独 Option(Alt) 键」作为全局命令支持有限，建议使用组合键。

## 数据存储

- 使用 `chrome.storage.local` 本地保存：
  - `word`：标准化后的单词（小写）
  - `sentences`：该单词关联的句子数组（去重）
  - `createdAt` / `updatedAt`：时间戳

## 目录说明

- `manifest.json`：扩展清单（MV3）。
- `background.js`：处理快捷键命令与打开生词本页面。
- `content.js`：读取选中内容、提取句子、触发保存。
- `storage.js`：统一存储与 Markdown 生成逻辑。
- `wordbook.html` / `wordbook.js` / `styles.css`：生词本展示与导出页面。
