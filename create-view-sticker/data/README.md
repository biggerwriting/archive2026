# create-view

浏览器端场景拼贴 + 图像处理工具集。将商品照片经过**抠图 → 矢量化 → 拖入画板造景**，最终导出一张合成图。

---

## 项目结构

```
create-view/
├── index.html        # SceneBoard — 造景拼贴画板（主应用）
├── app.js            # SceneBoard 逻辑层
├── style.css         # 全局深色主题样式
├── sticker.html      # SceneBoard 贴纸管理版（独立页）
├── svg-editor.html   # SVGBoard — 矢量绘图编辑器
├── demo.html         # Fabric.js 基础演示（学习用）
├── remove_bg.py      # SAM 抠图工具（Python）
├── png2svg.py        # PNG → SVG 矢量化工具（Python）
├── sam/
│   └── models/       # SAM 权重文件（.pth）
└── data/             # 素材目录（原图、抠图输出等）
```

---

## 一、浏览器工具（无需安装，直接打开）

所有 HTML 工具通过 CDN 加载依赖，双击文件或用本地服务器打开均可。

> 推荐用本地服务器避免跨域限制：
> ```bash
> cd create-view
> npx serve .        # 或 python3 -m http.server 8080
> # 然后访问 http://localhost:3000
> ```

---

### 1. SceneBoard — 造景拼贴画板

**文件：** `index.html`

拖拽透明背景的贴纸图片，自由摆放、调整层级，最终导出合成 PNG。

**打开方式：**
```bash
open index.html
```

**核心操作：**

| 操作 | 说明 |
|---|---|
| 拖放图片 / 点击 `+` | 导入 PNG · JPG · WebP · GIF |
| 左侧图层面板 | 拖拽排序、切换显隐、删除图层 |
| 右侧属性面板 | 调整 X / Y / 宽 / 高 / 旋转 / 透明度 |
| 工具栏按钮 | 前移一层 / 后移一层 / 水平翻转 / 垂直翻转 |
| 画布设置 | 尺寸预设（800×600 / 1280×720 / 1080p）、透明或纯色背景 |
| `⌘ + 滚轮` | 缩放画布 |
| `← → ↑ ↓` | 微移选中图层（1px；按住 Shift 为 10px） |
| `Delete` | 删除选中图层 |
| 导出 PNG 按钮 | 合并所有图层导出为 PNG |

---

### 2. SceneBoard 贴纸版

**文件：** `sticker.html`

带贴纸库管理的造景画板变体，适合管理多个贴纸分组。

```bash
open sticker.html
```

---

### 3. SVGBoard — 矢量绘图编辑器

**文件：** `svg-editor.html`

基于 Fabric.js 的矢量图形编辑器，支持绘制形状、编辑路径、导出 SVG。

```bash
open svg-editor.html
```

---

### 4. Fabric.js 基础演示

**文件：** `demo.html`

带详细中文注释的 Fabric.js 入门示例，用于学习 Canvas 对象模型。

```bash
open demo.html
```

---

## 二、Python 工具（需要环境配置）

### 环境准备

```bash
# 在项目根目录创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate
```

---

### 5. remove_bg.py — SAM 智能抠图

基于 Meta SAM（Segment Anything Model）的背景去除工具。
自动识别前景物体，去掉背景后输出透明 PNG，适合纯色/渐变背景的商品图。

**安装依赖：**
```bash
pip install torch torchvision opencv-python pillow
pip install git+https://github.com/facebookresearch/segment-anything.git
```

> SAM 权重已放置在 `sam/models/sam_vit_b_01ec64.pth`，无需额外下载。

**基本用法：**
```bash
# 输出到同目录，文件名自动加 _nobg 后缀
.venv/bin/python3 remove_bg.py data/items/item_001.png

# 指定输出路径
.venv/bin/python3 remove_bg.py data/items/item_001.png data/output/item_001_nobg.png
```

**工作原理：**
1. SAM 自动分割图片中所有区域
2. 凡是接触图片边缘（上下左右）且面积 > 3% 的区域，判定为背景
3. 其余区域合并为前景，应用透明 alpha 通道
4. 自动裁剪透明边角，输出紧凑的透明 PNG

> **提示：** 如前景识别不准，可调整源码中的 `border_margin`（默认 5）或 `min_area`（默认 1000）参数。


python3 -m venv .venv
source .venv/bin/activate

pip install torch torchvision
pip install opencv-python
pip install pillow
pip install numpy
pip install git+https://github.com/facebookresearch/segment-anything.git

需要手动准备的文件

脚本会在 运行目录的 sam/models/ 下查找 .pth 权重文件：

新目录/
├── remove_bg.py
└── sam/
    └── models/
        └── sam_vit_b_01ec64.pth   ← 需要手动放置

权重文件可从 Meta 官方下载（选一个即可）：

┌─────────────────────┬────────┬──────┐
│        模型         │  大小  │ 下载 │
├─────────────────────┼────────┼──────┤
│ ViT-B（轻量，推荐） │ 375 MB │ 下载 │
├─────────────────────┼────────┼──────┤
│ ViT-L（中等）       │ 1.2 GB │ 下载 │
├─────────────────────┼────────┼──────┤
│ ViT-H（最强）       │ 2.4 GB │ 下载 │
└─────────────────────┴────────┴──────┘

---
脚本会自动识别 models/ 目录里放的是哪个型号，无需额外配置。

---

### 6. png2svg.py — PNG 矢量化

将位图 PNG 转换为 SVG 矢量路径，依赖 [vtracer](https://github.com/visioncortex/vtracer) 库。

> ⚠️ vtracer 在 Python 3.14+ 会崩溃，脚本会自动切换到 Python 3.11。

**安装依赖：**
```bash
# 必须使用 Python 3.11
brew install python@3.11
python3.11 -m pip install vtracer
```

**基本用法：**
```bash
# 使用默认预设（cartoon）
python3.11 png2svg.py data/items/item_001.png

# 指定输出路径
python3.11 png2svg.py data/items/item_001.png -o data/output/item_001.svg

# 使用内置预设
python3.11 png2svg.py input.png -p cartoon   # 卡通插图，保留颜色细节（默认）
python3.11 png2svg.py input.png -p photo     # 照片，减少路径数量
python3.11 png2svg.py input.png -p logo      # Logo/Icon，极简风格
python3.11 png2svg.py input.png -p bw        # 黑白线稿

# 生成所有预设版本对比（方便挑选）
python3.11 png2svg.py input.png --compare

# 手动调参（覆盖预设）
python3.11 png2svg.py input.png --color 6 --speckle 8
```

**参数说明：**

| 参数 | 说明 | 范围 |
|---|---|---|
| `--color` | 颜色精度（越大颜色越丰富） | 1–8 |
| `--diff` | 颜色合并阈值（越大路径越少） | 1–255 |
| `--speckle` | 碎点过滤（像素，越大越干净） | ≥ 0 |
| `--corner` | 拐角检测阈值（越大转角越少） | 1–180 |
| `--length` | 最短路径（像素，越大细节越少） | ≥ 0 |
| `--mode` | 曲线类型 | `spline` / `polygon` / `none` |
| `--bw` | 强制黑白模式 | — |

---

## 三、典型工作流

```
商品原图 (JPG/PNG)
    │
    ▼
remove_bg.py          ← SAM 抠图，输出透明背景 PNG
    │
    ▼
png2svg.py（可选）   ← 需要矢量版本时转换为 SVG
    │
    ▼
SceneBoard (index.html)  ← 拖入贴纸，摆放造景
    │
    ▼
导出 PNG              ← 最终合成图
```

---

## 技术栈

| 模块 | 技术 |
|---|---|
| 浏览器工具 | 原生 HTML / CSS / JS，无构建步骤 |
| Canvas 交互 | [Fabric.js 5.3.1](http://fabricjs.com/)（CDN） |
| 字体 | JetBrains Mono · Space Grotesk（Google Fonts） |
| 抠图 | Python · [SAM](https://github.com/facebookresearch/segment-anything) · OpenCV · PyTorch |
| 矢量化 | Python · [vtracer](https://github.com/visioncortex/vtracer) |
