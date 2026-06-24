# 手写字提取工具

从手持拍摄的照片中提取手写文字，输出**透明背景**的 PNG 图片。

专为「用手机/相机拍笔记本」的场景设计——自动消除光照不均、去除纸张背景，保留平滑清晰的墨迹，可直接用于排版、贴图、二次创作。

---

## ✨ 功能特点

- **消除光照不均** — 拍照时角落偏暗、背光发黄？算法自动估算背景亮度并归一化，不影响提取质量
- **边缘平滑无锯齿** — 使用软阈值渐变 Alpha，边缘自然过渡，放大也不会出现「马赛克」锯齿
- **统一墨迹颜色** — 输出纯色墨迹（默认纯黑），可自定义 RGB 颜色，适合不同风格需求
- **批量处理** — 指定文件夹一键处理所有图片，支持递归子文件夹，保留原始目录结构
- **格式全覆盖** — 支持 JPG、PNG、BMP、TIFF、WebP 等常见格式

---

## 🎯 应用场景

| 场景 | 说明 |
|------|------|
| **笔记数字化** | 拍摄手写笔记，提取文字后叠加到 PPT、Notion、设计稿中 |
| **手写签名** | 提取签名为透明 PNG，用于电子文档、合同盖章 |
| **艺术创作** | 提取手绘线稿、手写诗词，制作贴纸、表情包、印刷品 |
| **内容二创** | 将纸上文字/插图提取后与数字素材合成 |
| **教学素材** | 提取板书、批注，制作讲义或教学视频字幕 |

---

## ⚙️ 算法原理

```
原图（灰度）
    │
    ├─ 大范围高斯模糊 → 估算背景亮度（消除光照渐变）
    │
    ├─ 原图 ÷ 背景 → 归一化（纸张≈1.0，墨迹<1.0）
    │
    ├─ 1 - 归一化 → 墨迹强度图
    │
    ├─ 软阈值 [low, high] → 渐变 Alpha（边缘天然抗锯齿）
    │
    └─ Alpha 二次高斯平滑 → 进一步消锯齿
           │
           ▼
    RGBA PNG（指定颜色 + 平滑透明度）
```

---

## 🚀 快速开始

### 环境要求

- Python ≥ 3.13
- [uv](https://docs.astral.sh/uv/)（包管理器，自动安装依赖）

安装 uv：

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 克隆项目

```bash
git clone <仓库地址>
cd handwriting-pic
```

依赖会在第一次运行时由 uv 自动安装，无需手动 `pip install`。

---

## 📖 使用方法

### 单张图片

```bash
uv run extract_handwriting.py <图片路径>
```

输出文件保存在**与原图相同目录**，文件名为 `原文件名_extracted.png`。

```bash
# 示例：处理 note.jpg，输出 note_extracted.png（同目录）
uv run extract_handwriting.py note.jpg
```

### 批量处理文件夹

```bash
uv run extract_handwriting.py <文件夹路径>
```

默认在输入文件夹内创建 `extracted/` 子目录存放结果，并显示逐张进度。

```bash
# 示例：批量处理 photos/ 文件夹
uv run extract_handwriting.py photos/

# 输出目录结构：
# photos/
# ├── note1.jpg
# ├── note2.jpg
# └── extracted/
#     ├── note1_extracted.png
#     └── note2_extracted.png
```

### 递归处理子文件夹

```bash
uv run extract_handwriting.py photos/ -r
```

子文件夹的目录结构会原样保留到输出目录中。

---

## 🔧 参数说明

```
uv run extract_handwriting.py <input> [选项]
```

| 参数 | 简写 | 说明 | 默认值 |
|------|------|------|--------|
| `input` | — | 输入图片路径 或 文件夹路径 | 必填 |
| `--output-dir` | `-o` | 指定输出目录 | 单张：同输入目录；批量：输入目录下的 `extracted/` |
| `--recursive` | `-r` | 递归处理子文件夹（仅批量模式） | 关闭 |
| `--color R G B` | — | 墨迹颜色（RGB 三通道，0~255） | `0 0 0`（纯黑） |
| `--sensitivity` | — | 提取灵敏度（0.0~1.0）。值越高，提取越多细节，但也可能带入背景噪点 | `0.5` |

---

## 💡 使用示例

```bash
# 基本用法：单张图片，输出纯黑墨迹
uv run extract_handwriting.py handwriting.jpg

# 批量处理，输出到指定目录
uv run extract_handwriting.py photos/ -o output/

# 递归处理所有子文件夹
uv run extract_handwriting.py notes/ -r -o output/

# 自定义深蓝色墨迹（更接近钢笔质感）
uv run extract_handwriting.py note.jpg --color 20 30 80

# 提高灵敏度，提取更多细节（适合笔迹较浅的照片）
uv run extract_handwriting.py note.jpg --sensitivity 0.8

# 降低灵敏度，过滤背景杂点（适合纸张有纹理的情况）
uv run extract_handwriting.py note.jpg --sensitivity 0.3

# 组合使用
uv run extract_handwriting.py photos/ -r -o output/ --color 0 0 0 --sensitivity 0.6
```

---

## 📁 项目结构

```
handwriting-pic/
├── extract_handwriting.py   # 主脚本
├── pyproject.toml           # 项目配置与依赖
├── uv.lock                  # 依赖版本锁定
└── docs/
    └── superpowers/
        └── specs/           # 设计文档
```

---

## 📦 依赖

| 库 | 用途 |
|----|------|
| `opencv-python` | 图像读取、高斯模糊、形态学处理 |
| `numpy` | 数组运算（归一化、Alpha 计算） |
| `pillow` | RGBA PNG 写入 |
