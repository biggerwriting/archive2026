# 当前页批量选图下载

一个轻量实用的 Chrome 浏览器扩展，用于批量选取并下载当前网页上的图片。多图自动打包为 ZIP，单图直接下载，无需后端、无需登录，完全在浏览器本地运行。

---

## 功能特性

- **自动收集图片**：扫描当前页所有 `<img>`（含 `src`、`srcset`、`currentSrc`）及 `<picture source>` 中的图片，自动去重
- **可视化选图**：以缩略图 + URL + alt 文字列表展示，默认全选，支持一键全选 / 全不选
- **单图下载**：仅选 1 张时直接触发浏览器下载
- **批量 ZIP 打包**：选 2 张及以上时自动打包为 ZIP 文件，文件名可自定义
- **智能文件名**：从 URL 路径和 `Content-Type` 响应头推断扩展名，文件名自动编号（`001_xxx.jpg`）
- **错误容忍**：单张抓取失败时跳过并提示，其余图片正常打包
- **按需授权**：批量下载时才动态申请网络访问权限，安装时不要求过多权限

---

## 项目结构

```
cursor-dev-word-plugin/
├── manifest.json        # 扩展配置（Manifest V3）
├── popup.html           # 弹窗 UI 结构
├── popup.css            # 弹窗样式
├── popup.js             # 弹窗交互逻辑
├── content.js           # 注入页面，负责收集图片
├── background.js        # Service Worker，负责打包与下载
└── vendor/
    └── jszip.min.js     # ZIP 打包库
```

---

## 安装方式

1. 下载或克隆本仓库到本地
2. 打开 Chrome，进入 `chrome://extensions/`
3. 开启右上角「开发者模式」
4. 点击「加载已解压的扩展程序」，选择本项目目录
5. 扩展图标出现在工具栏即安装成功

---

## 使用方式

1. 打开任意 `http` / `https` 网页
2. 点击工具栏中的扩展图标，Popup 自动收集当前页所有图片
3. 勾选需要下载的图片（默认全选）
4. 可选：在输入框中填写 ZIP 文件名（不含 `.zip`，默认按日期命名）
5. 点击「下载选中」
   - 选了 1 张：直接下载该图片
   - 选了 2 张及以上：打包为 ZIP 文件后下载，首次使用时会弹出权限授权提示

---

## 技术说明

### Manifest V3 兼容
`background.js` 以 Service Worker 运行。MV3 Service Worker 不支持 `URL.createObjectURL`，因此 ZIP 生成后以 `base64 + data URL` 形式传给 `chrome.downloads` API，绕过此限制。

### 内容脚本防重入
`content.js` 通过 `globalThis.__BATCH_IMG_DL_INSTALLED__` 标志防止被多次注入同一页面。

### 权限声明

| 权限 | 用途 |
|------|------|
| `activeTab` | 访问当前标签页信息 |
| `scripting` | 向页面注入 `content.js` |
| `downloads` | 触发文件下载 |
| `<all_urls>`（可选） | 批量下载时 fetch 跨域图片资源 |

---

## 开发说明

项目为纯静态文件，无构建步骤，修改代码后在 `chrome://extensions/` 页面点击「重新加载」即可生效。
