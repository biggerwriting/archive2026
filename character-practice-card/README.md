# 九阵字帖

> 将楷书字形压入 8×8 方格（9×9 顶点），笔画起点对齐笔顺数据，便于对照练习。

一个运行于浏览器的汉字练字卡生成器。输入任意汉字，即可导出带栅格参考线的点阵练字卡图片，支持三种楷体字库、两种渲染风格与笔画起点标注。

---

## 功能特性

| 功能 | 说明 |
|------|------|
| **8×8 栅格采样** | 将字形像素分布映射到 8×8 方格，呈现汉字骨架结构 |
| **多字体支持** | 霞鹜文楷 / 思源宋体 / 系统楷书，三选一 |
| **双渲染模式** | 方格填充（高亮深色格）或顶点点阵（标注边角点） |
| **栅格阈值调节** | 通过滑块（8%–45%）控制像素深色判定灵敏度 |
| **笔画起点标注** | 联网拉取 hanzi-writer-data 笔顺中线，用朱红圆圈标注每笔起点 |
| **灯箱大图预览** | 点击卡片放大查看细节，支持 ESC / 点击背景关闭 |
| **批量导出 PNG** | 一键打包下载当前批次全部卡片（文件名含序号） |

---

## 技术栈

- **框架**：原生 JavaScript（无 UI 框架依赖）
- **构建工具**：[Vite](https://vite.dev/) 6
- **渲染**：HTML5 Canvas API
- **字体**：LXGW WenKai、Noto Serif SC、Fraunces、Syne（均通过 CDN 加载）
- **笔顺数据**：[hanzi-writer-data](https://github.com/chanind/hanzi-writer-data)（jsDelivr CDN，简体字库）

---

## 快速开始

### 环境要求

- Node.js ≥ 18
- npm ≥ 9（或 pnpm / yarn）

### 安装与运行

```bash
# 克隆项目
git clone <仓库地址>
cd character-practice-card

# 安装依赖
npm install

# 启动开发服务器（默认 http://localhost:5173）
npm run dev
```

### 构建生产包

```bash
npm run build       # 输出到 dist/
npm run preview     # 本地预览生产构建
```

---

## 使用说明

1. **输入汉字**：在文本框中粘贴或键入任意汉字（支持多字、整段文字，自动过滤空白和非汉字字符）。
2. **选择字体**：下拉菜单切换三种楷书字体，效果略有差异。
3. **选择呈现模式**：
   - *方格填充*：深色像素占比超过阈值的格子整体填黑。
   - *顶点点阵*：在被激活格的顶角绘制小圆点。
4. **调整栅格阈值**：拖动滑块，数值越小越灵敏（捕捉更多细笔画），数值越大越粗犷。默认 22%。
5. **笔画起点**：勾选后，每张卡片会叠加朱红色编号圆圈，指示各笔笔画的起始位置（需联网，且仅简体字库覆盖范围内有效）。
6. **生成卡片**：点击「生成卡片」，稍等片刻即可在右侧看到字卡阵列。
7. **放大预览**：点击任意卡片，灯箱模式展示 2× 高分辨率大图。
8. **下载图片**：点击「打包下载 PNG」，所有卡片依次触发下载，文件命名格式为 `练字卡-01.png`、`练字卡-02.png`……

---

## 项目结构

```
character-practice-card/
├── index.html          # 页面入口，包含控制面板与画廊 HTML
├── src/
│   ├── main.js         # 核心逻辑：栅格采样、Canvas 渲染、交互事件
│   └── styles.css      # 全局样式（暗色主题，楷书风格配色）
├── vite.config.js      # Vite 配置
├── package.json
└── dist/               # 构建产物（git 忽略，运行 build 后生成）
```

---

## 参数说明

| 参数 | 默认值 | 范围 | 作用 |
|------|--------|------|------|
| `GRID` | 8 | — | 栅格边长（格数），决定精度 |
| `RENDER_SIZE` | 640 px | — | 离屏 Canvas 采样分辨率 |
| `CARD_BASE` | 360 px | — | 导出卡片基础尺寸（下载 1×，预览 2×）|
| 栅格阈值 | 22% | 8–45% | 格子内深色像素占比达此值则激活 |

---

## 注意事项

- **笔顺标注联网**：笔画起点数据通过 jsDelivr CDN 实时拉取，离线环境或网络受限时该功能不可用，卡片仍可正常生成（无标注）。
- **字体加载**：首次生成时如字体尚未完全加载，卡片会稍作等待（约 120 ms），以保证字形正确采样。
- **字库覆盖**：hanzi-writer-data 主要覆盖常用简体汉字，生僻字可能无笔顺数据，状态栏会提示缺失数量。
- **浏览器兼容**：依赖 HTML5 Canvas、`document.fonts` API 及 ES Module，推荐 Chrome / Edge / Firefox / Safari 最新版本。

---

## License

本项目仅供学习与个人练字使用。字体版权归各自作者所有：
- **霞鹜文楷**：[LXGW WenKai](https://github.com/lxgw/LxgwWenKai)（SIL Open Font License 1.1）
- **思源宋体**：[Noto Serif SC](https://fonts.google.com/noto/specimen/Noto+Serif+SC)（SIL Open Font License 1.1）
- **笔顺数据**：[hanzi-writer-data](https://github.com/chanind/hanzi-writer-data)（MIT）
