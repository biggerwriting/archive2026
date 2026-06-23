# Plugin Icon Generator — Chrome 插件图标生成工具

一行命令，从任意图片生成完整的 Chrome 插件图标集（16×16 / 32×32 / 48×48 / 128×128）。

---

## 功能介绍

Chrome 扩展程序要求提供四种标准尺寸的 PNG 图标。本工具自动完成以下步骤：

1. 读取你提供的源图片（支持 JPEG、PNG、WebP 等常见格式）
2. 自动将非正方形图片**居中裁剪**为正方形
3. 将图片缩放至四个标准尺寸，并转换为 **RGBA PNG** 格式
4. 输出到指定目录（默认为 `icons/`）

生成的文件：

```
icons/
├── icon16.png    (16×16)
├── icon32.png    (32×32)
├── icon48.png    (48×48)
└── icon128.png   (128×128)
```

---

## 环境要求

- Python 3.7+
- [Pillow](https://pillow.readthedocs.io/) 图像处理库

---

## 安装依赖

```bash
pip install Pillow
```

---

## 使用方法

### 基本用法

```bash
python generate_icons.py <源图片路径>
```

图标将默认输出到源图片**同级目录**下的 `icons/` 文件夹中。

**示例：**

```bash
python generate_icons.py logo.png
```

输出：

```
Source: logo.png (512x512)
Output: icons/

  icon16.png   (16x16)
  icon32.png   (32x32)
  icon48.png   (48x48)
  icon128.png  (128x128)

Done.
```

---

### 指定输出目录

```bash
python generate_icons.py <源图片路径> <输出目录>
```

**示例：**

```bash
python generate_icons.py walle.jpeg ./my_extension/icons
```

---

## 实际演示

本仓库包含一张示例图片 `walle.jpeg`，可直接运行体验：

```bash
python generate_icons.py walle.jpeg
```

生成结果存放在 `icons/` 目录中。

---

## 在 Chrome 插件中使用

将生成的图标路径写入 `manifest.json`：

```json
{
  "name": "My Extension",
  "version": "1.0",
  "manifest_version": 3,
  "icons": {
    "16":  "icons/icon16.png",
    "32":  "icons/icon32.png",
    "48":  "icons/icon48.png",
    "128": "icons/icon128.png"
  }
}
```

---

## 注意事项

- **源图片建议尺寸**：128×128 px 以上，越大效果越好（128px 是最大输出尺寸，源图过小会导致放大模糊）
- **非正方形图片**：工具会自动以中心为基准裁剪为正方形，裁剪前请确认主体内容居中
- **透明背景**：输出为 RGBA 格式，原图的透明通道会被保留

---

## 文件结构

```
plugin-icon-generator/
├── generate_icons.py   # 主脚本
├── walle.jpeg          # 示例源图片
├── icons/              # 生成的图标目录（示例）
│   ├── icon16.png
│   ├── icon32.png
│   ├── icon48.png
│   └── icon128.png
└── README.md           # 本文档
```
