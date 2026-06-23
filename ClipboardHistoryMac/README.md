# ClipboardHistoryMac

一个 macOS 菜单栏剪贴板历史工具（MVP），目标是提供类似 Windows `Win+V` 的体验。

## 当前能力（MVP）

- 监听并记录文本复制历史（`Command+C` 后自动入库）
- 去重与上限控制（默认最多 200 条）
- 全局快捷键 `Option+V` 呼出历史面板
- 方向键选择历史，`Enter` 直接粘贴到当前应用
- 本地持久化历史（重启后可恢复）

## 目录结构

- `Package.swift`：SwiftPM 配置
- `Sources/App/MainApp.swift`：应用入口与菜单栏
- `Sources/Core/`：监听、存储、热键、粘贴注入、应用编排
- `Sources/UI/`：历史面板界面与键盘交互

## 运行方式

1. 打开终端进入项目目录：
   - `cd ClipboardHistoryMac`
2. 构建：
   - `swift build`
3. 运行：
   - `swift run ClipboardHistoryMac`

## 权限说明

自动粘贴依赖模拟 `Command+V` 按键，需要在系统中授予辅助功能权限：

1. 打开 `系统设置 -> 隐私与安全性 -> 辅助功能`
2. 允许 `Terminal`（如果你通过终端运行）或你的宿主应用
3. 重新触发一次粘贴操作

## 已知限制（MVP）

- 当前仅记录文本，不包含图片与文件路径
- 某些受保护应用可能阻止自动输入
- 全局快捷键固定为 `Option+V`（后续可做配置）

## 验收建议

1. 在任意应用复制几段文本，确认 1 秒内出现在历史面板
2. 按 `Option+V`，使用上下方向键选择项并按回车
3. 在输入框中确认内容已被粘贴
4. 重启应用，确认历史已恢复
