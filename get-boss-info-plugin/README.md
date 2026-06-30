# BOSS直聘职位收集器

浏览 BOSS 直聘时，点击插件图标 → 一键保存感兴趣的职位 → 批量导出 CSV。

## 安装步骤

1. 打开 Chrome，地址栏输入 `chrome://extensions`
2. 右上角打开「开发者模式」
3. 点击「加载已解压的扩展程序」
4. 选择本目录（`get-boss-info-plugin`）

安装成功后，工具栏会出现蓝色 💼 图标。

## 使用方法

1. 打开 [BOSS直聘职位列表页](https://www.zhipin.com/web/geek/jobs)
2. 点击任意一个职位，等右侧详情面板加载完毕
3. 点击工具栏的插件图标，弹出面板会显示当前职位信息
4. 点击「💾 保存此职位」
5. 重复 2-4，积攒完所有感兴趣的职位后，点击「📊 导出 CSV」

## 文件结构

```
get-boss-info-plugin/
├── manifest.json          # 扩展配置（MV3）
├── content/
│   ├── interceptor.js     # 注入页面 MAIN world，劫持 fetch/XHR
│   └── receiver.js        # 解析 API 响应，写入 storage
├── popup/
│   ├── popup.html         # 弹出面板
│   ├── popup.css          # 样式
│   └── popup.js           # 面板逻辑（保存 / 导出 / 删除）
└── icons/
    ├── icon16.png
    ├── icon48.png
    └── icon128.png
```

## 工作原理

BOSS 直聘屏蔽了 F12 开发者工具，但 Chrome 扩展运行在独立的特权上下文中，不受此限制。

插件通过在页面 MAIN world 注入脚本，在 BOSS 直聘自己的 JS 执行之前劫持 `window.fetch`
和 `XMLHttpRequest`，从而拦截所有 API 响应，提取结构化的职位数据，完全不依赖
CSS 选择器，页面改版也不影响数据提取。

## 故障排查

**弹出面板显示"未检测到职位"**
- 确认当前标签页是 `zhipin.com` 域名
- 点击职位后等 1-2 秒再打开插件面板（等 API 响应回来）
- 重新加载扩展（`chrome://extensions` → 点刷新图标）

**导出的 CSV 在 Excel 中乱码**
- 文件已包含 UTF-8 BOM，直接双击应能正常显示
- 若仍乱码：Excel → 数据 → 从文本/CSV → 选择 UTF-8 编码

**想查看捕获到了哪些 API**
- `chrome://extensions` → 找到本插件 → 点「检查视图 Service Worker」（若有）
- 或在 receiver.js 的 `logApiCapture` 中查看 `debugLogs`（chrome.storage.local）
