# ClipboardHistoryMac 产品使用说明书

> macOS 剪贴板历史管理工具 · 让复制粘贴回到你手中

---

## 目录

1. [产品简介](#一产品简介)
2. [系统要求](#二系统要求)
3. [安装与启动](#三安装与启动)
4. [首次配置（辅助功能权限）](#四首次配置辅助功能权限)
5. [功能使用指南](#五功能使用指南)
6. [快捷键速查表](#六快捷键速查表)
7. [后台运行与开机自启](#七后台运行与开机自启)
8. [常见问题 FAQ](#八常见问题-faq)
9. [附录 A：从源码构建](#附录-a从源码构建)
10. [附录 B：LaunchAgent 配置详解](#附录-blaunchagent-配置详解)
11. [附录 C：数据存储位置](#附录-c数据存储位置)
12. [附录 D：完全卸载](#附录-d完全卸载)

---

## 一、产品简介

**ClipboardHistoryMac** 是一款轻量级的 macOS 菜单栏工具，让你随时访问最近复制过的文本内容。

就像 Windows 的 `Win+V` 剪贴板历史，ClipboardHistoryMac 在 macOS 上带来同样的体验：

- 你复制过的每一段文字都被悄悄记录下来
- 任何时刻按 **⌥V**（Option + V）即可唤出历史面板
- 选择任意一条，按回车即刻粘贴到当前应用

App 常驻菜单栏，不占 Dock 位置，安静地在后台工作。

---

## 二、系统要求

| 项目 | 要求 |
|------|------|
| 操作系统 | macOS 13 Ventura 或更高版本 |
| 芯片 | Apple Silicon（M 系列）或 Intel 均支持 |
| 磁盘空间 | < 5 MB |
| 网络 | 不需要 |
| 特殊权限 | 辅助功能权限（自动粘贴时需要，见第四节） |

---

## 三、安装与启动

### 3.1 启动已编译的程序

如果你已经获得了编译好的二进制文件，直接在终端运行：

```bash
/path/to/ClipboardHistoryMac
```

启动成功后，菜单栏右侧会出现 **"CL"** 图标，表示 App 正在运行。

### 3.2 首次启动流程

1. 启动程序
2. 菜单栏出现 **CL** 图标 ✅
3. 系统可能弹出辅助功能权限请求 → 点击"打开系统设置"完成授权（见第四节）
4. 之后即可正常使用

> ⚠️ **如果菜单栏没有出现 CL 图标**，说明程序未成功启动。请检查是否有其他同名进程在运行：`pgrep ClipboardHistoryMac`

---

## 四、首次配置（辅助功能权限）

ClipboardHistoryMac 通过模拟 **Command+V** 按键将文字粘贴到当前应用，这需要 macOS 的辅助功能权限。

**⚠️ 不授权则只能查看历史，无法自动粘贴。**

### 步骤

1. 打开 **系统设置**（点击左上角苹果菜单 → 系统设置）

2. 点击左侧 **隐私与安全性**

3. 点击右侧 **辅助功能**

4. 点击右下角 **锁形图标** 解锁（输入 Mac 密码）

5. 点击 **+** 按钮，找到并添加 `ClipboardHistoryMac` 可执行文件

   - 如果通过终端运行，需要添加 `Terminal`（终端）应用
   - 如果使用编译好的独立程序，直接添加该程序文件

6. 确保开关已 **打开**（蓝色）✅

7. 重新触发一次粘贴操作验证权限已生效

> 💡 **提示**：如果之前已添加但仍报错，先删除再重新添加，macOS 有时需要重新注册权限。

---

## 五、功能使用指南

### 5.1 自动记录复制内容

只需像平时一样使用 **Command+C** 复制文字，ClipboardHistoryMac 会在约 0.5 秒内自动将内容存入历史记录。

**记录规则：**
- ✅ 纯文本内容均被记录
- ✅ 自动去除首尾空白字符
- ✅ 重复内容自动去重（相同内容复制多次只保留最新一条）
- ✅ 记录来源应用名称和复制时间
- ✅ 最多保留 **200 条**历史记录，超出后自动删除最旧的
- ❌ 图片、文件、非文本内容暂不支持

---

### 5.2 唤出历史面板

按下全局快捷键 **⌥V**（Option + V），历史面板立即出现在屏幕中央。

面板显示效果如下：

```
┌─────────────────────────────────────────┐
│  Clipboard History              [Clear] │
├─────────────────────────────────────────┤
│ ▶ 这是最近复制的一段文字                │
│   14:23:05 · Safari                     │
├─────────────────────────────────────────┤
│   Hello, World!                         │
│   14:20:11 · Xcode                      │
├─────────────────────────────────────────┤
│   https://example.com/some/url          │
│   13:55:40 · Chrome                     │
└─────────────────────────────────────────┘
  快捷键: Option+V 打开历史，方向键选择，回车粘贴，Esc 关闭
```

每条记录展示：
- **复制的文字内容**（最多显示 2 行）
- **复制时间**（时:分:秒）
- **来源应用**（从哪个 App 复制的）
- **蓝色高亮** 当前选中项

---

### 5.3 选择历史记录

面板打开后，有两种选择方式：

**方式一：键盘**
- 按 **↑** / **↓** 方向键上下移动选中项（高亮跟随移动）

**方式二：鼠标**
- **单击**某条记录 → 选中（高亮）

---

### 5.4 粘贴选中内容

选中目标内容后：

| 操作 | 效果 |
|------|------|
| 按 **Enter（回车）** | 关闭面板 + 粘贴到当前应用光标处 |
| **双击**某条记录 | 直接粘贴（无需先选中）|

> ⚠️ **如果出现红色错误提示**："请在系统设置 -> 隐私与安全性 -> 辅助功能中允许本应用"  
> → 请参考 [第四节](#四首次配置辅助功能权限) 完成权限配置。

---

### 5.5 删除历史记录

**删除单条：**
- 在面板中 **右键点击**某条记录 → 选择"删除"

**清空全部：**
- 点击面板右上角 **Clear** 按钮
- 或在面板打开时按 **Command + Delete**

---

### 5.6 菜单栏操作

点击菜单栏的 **CL** 图标，弹出菜单：

| 菜单项 | 功能 |
|--------|------|
| 打开历史 (Option+V) | 等同于按 ⌥V 快捷键 |
| 退出 | 完全退出 ClipboardHistoryMac |

---

### 5.7 关闭面板

| 操作 | 效果 |
|------|------|
| 按 **Esc** | 关闭面板，App 继续后台运行 |
| 点击面板右上角 **×** | 关闭面板，App 继续后台运行 |
| 点击菜单栏 → 退出 | 关闭面板 + 退出 App |

> ✅ 关闭面板 ≠ 退出 App。关闭后 CL 图标仍在菜单栏，继续记录历史。

---

## 六、快捷键速查表

| 快捷键 | 场景 | 效果 |
|--------|------|------|
| **⌥V**（Option + V） | 任意应用 | 唤出 / 关闭历史面板 |
| **↑ / ↓** | 面板打开时 | 上下选择历史记录 |
| **Enter（回车）** | 面板打开时 | 粘贴选中内容并关闭面板 |
| **Esc** | 面板打开时 | 关闭面板（不粘贴）|
| **双击** | 面板打开时 | 直接粘贴该条内容 |
| **右键** | 面板打开时 | 弹出删除菜单 |
| **⌘ + Delete** | 面板打开时 | 清空所有历史记录 |

---

## 七、后台运行与开机自启

### 7.1 后台运行（不占终端窗口）

在终端运行以下命令，App 将在后台静默运行：

```bash
nohup /path/to/ClipboardHistoryMac > /tmp/clipboard-history.log 2>&1 &
echo "ClipboardHistoryMac 已在后台启动，PID: $!"
```

查看运行状态：

```bash
pgrep -a ClipboardHistoryMac
```

手动停止：

```bash
pkill -f ClipboardHistoryMac
```

---

### 7.2 开机自动启动

使用 macOS LaunchAgent 实现开机自启：

**第一步：创建配置文件**

```bash
cat > ~/Library/LaunchAgents/com.user.clipboardhistory.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.user.clipboardhistory</string>
    <key>ProgramArguments</key>
    <array>
        <string>/path/to/ClipboardHistoryMac</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/tmp/clipboard-history.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/clipboard-history-error.log</string>
</dict>
</plist>
EOF
```

> ⚠️ 将 `/path/to/ClipboardHistoryMac` 替换为实际的可执行文件路径。

**第二步：加载并启动**

```bash
launchctl load ~/Library/LaunchAgents/com.user.clipboardhistory.plist
```

**验证是否成功启动：**

```bash
launchctl list | grep clipboardhistory
# 输出示例：759  0  com.user.clipboardhistory
# 第一列是 PID，非 0 表示正在运行
```

**常用管理命令：**

| 操作 | 命令 |
|------|------|
| 停止 | `launchctl unload ~/Library/LaunchAgents/com.user.clipboardhistory.plist` |
| 重新启动 | `launchctl kickstart -k gui/$UID/com.user.clipboardhistory` |
| 查看状态 | `launchctl list \| grep clipboard` |
| 查看日志 | `tail -f /tmp/clipboard-history.log` |
| 查看错误日志 | `tail -f /tmp/clipboard-history-error.log` |

---

## 八、常见问题 FAQ

**Q1：按 ⌥V 没有反应，面板没有出现？**

检查 App 是否在运行：
```bash
pgrep ClipboardHistoryMac
```
如果没有输出，说明 App 未运行，请重新启动。  
如果有输出但快捷键无效，可能与其他 App 的快捷键冲突，检查是否有其他 App 占用了 ⌥V。

---

**Q2：粘贴时出现红色错误"请在系统设置 -> 辅助功能中允许本应用"？**

参考 [第四节](#四首次配置辅助功能权限) 完成权限配置。如已添加但仍报错：
1. 在辅助功能列表中找到该条目
2. 关闭开关，然后重新打开
3. 或删除后重新添加

---

**Q3：重启 Mac 后历史记录还在吗？**

✅ 在。历史记录持久化保存在本地，重启 App 后自动恢复（最多 200 条）。  
存储位置：`~/Library/Application Support/ClipboardHistoryMac/history.json`

---

**Q4：复制了内容但面板里没有出现？**

可能原因：
- 复制的是图片或文件（当前版本仅支持纯文本）
- App 未在运行
- 监听器正在启动中（冷启动后等待约 1 秒）

---

**Q5：某些应用里粘贴没有效果？**

少数受系统保护的应用（如密码管理器输入框、某些安全应用）会阻止模拟按键输入。此类场景可以：
1. 从面板中单击选中内容
2. 手动按 **Command+V** 粘贴（内容已写入剪贴板）

---

## 附录 A：从源码构建

适用于开发者或希望自行编译的用户。

**前提条件：**
- macOS 13+
- Xcode Command Line Tools：`xcode-select --install`

**构建步骤：**

```bash
# 1. 进入项目目录
cd ClipboardHistoryMac

# 2. Debug 构建（开发用）
swift build

# 3. Release 构建（生产用，体积小、性能好）
swift build -c release

# 4. 直接运行（Debug）
swift run

# 5. 运行编译好的 Release 二进制
.build/release/ClipboardHistoryMac
```

**二进制文件位置：**

| 构建类型 | 路径 |
|----------|------|
| Debug | `.build/debug/ClipboardHistoryMac` |
| Release | `.build/release/ClipboardHistoryMac` |

> 💡 **建议**：日常使用请用 Release 版本，性能更好，体积更小。

---

## 附录 B：LaunchAgent 配置详解

LaunchAgent 是 macOS 的用户级后台任务机制，配置文件为 plist 格式，存放于 `~/Library/LaunchAgents/`。

**关键字段说明：**

| 字段 | 含义 |
|------|------|
| `Label` | 服务唯一标识符，建议用反域名格式 |
| `ProgramArguments` | 可执行文件路径（必须是绝对路径） |
| `RunAtLoad` | `true` = 加载配置时立即启动 |
| `KeepAlive` | `true` = 进程意外退出后自动重启 |
| `StandardOutPath` | 标准输出日志文件路径 |
| `StandardErrorPath` | 错误输出日志文件路径 |

**完整生命周期：**

```
登录 macOS
  └→ launchd 读取 ~/Library/LaunchAgents/*.plist
       └→ RunAtLoad=true → 启动进程
            └→ 进程退出 → KeepAlive=true → 自动重启
```

**禁用开机自启（但保留配置文件）：**

```bash
launchctl unload ~/Library/LaunchAgents/com.user.clipboardhistory.plist
```

**永久删除开机自启：**

```bash
launchctl unload ~/Library/LaunchAgents/com.user.clipboardhistory.plist
rm ~/Library/LaunchAgents/com.user.clipboardhistory.plist
```

---

## 附录 C：数据存储位置

| 内容 | 路径 |
|------|------|
| 历史记录 | `~/Library/Application Support/ClipboardHistoryMac/history.json` |
| 运行日志 | `/tmp/clipboard-history.log` |
| 错误日志 | `/tmp/clipboard-history-error.log` |
| LaunchAgent 配置 | `~/Library/LaunchAgents/com.user.clipboardhistory.plist` |

**查看历史记录文件：**

```bash
cat ~/Library/"Application Support"/ClipboardHistoryMac/history.json | python3 -m json.tool | head -50
```

**手动清空历史记录（App 运行时不建议）：**

```bash
rm ~/Library/"Application Support"/ClipboardHistoryMac/history.json
```

---

## 附录 D：完全卸载

如需彻底删除 ClipboardHistoryMac：

```bash
# 1. 停止并移除开机自启
launchctl unload ~/Library/LaunchAgents/com.user.clipboardhistory.plist 2>/dev/null
rm -f ~/Library/LaunchAgents/com.user.clipboardhistory.plist

# 2. 终止正在运行的进程
pkill -f ClipboardHistoryMac 2>/dev/null

# 3. 删除历史数据
rm -rf ~/Library/"Application Support"/ClipboardHistoryMac

# 4. 删除日志文件
rm -f /tmp/clipboard-history.log /tmp/clipboard-history-error.log

# 5. 删除程序文件（替换为实际路径）
rm -f /path/to/ClipboardHistoryMac
```

执行完毕后，ClipboardHistoryMac 的所有文件和数据均已从系统中清除。

---

*ClipboardHistoryMac · macOS 剪贴板历史管理工具*
