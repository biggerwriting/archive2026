# 手写字提取工具 — 设计文档

**日期：** 2026-06-19  
**状态：** 已批准

---

## 目标

从手持拍摄的笔记本照片中提取手写字，输出透明背景的 PNG 文件，去除印刷横线，保留墨迹原色。

## 约束

- 单张图片处理（命令行传入路径）
- 不做透视矫正，保持原始拍摄角度
- 墨迹保留原色（深蓝/黑，有深浅变化）
- 去除笔记本印刷横线，只保留手写笔迹
- 用 `uv` 管理依赖
- Python 实现，依赖 `opencv-python` + `numpy`

## 架构

```
输入图片
   ├──→ 管线 A（自适应阈值 + 形态学去线） ──→ output_A.png
   └──→ 管线 B（背景估算 + 形态学去线）   ──→ output_B.png
```

两条管线共用输入读取、横线去除、RGBA 输出逻辑，仅墨迹掩码生成步骤不同。

## 项目结构

```
handwriting-pic/
├── pyproject.toml         # uv 项目配置
├── extract_handwriting.py # 主脚本
└── docs/
    └── superpowers/
        └── specs/
            └── 2026-06-19-handwriting-extractor-design.md
```

## 核心处理流程

### 共用步骤

1. **读取原图**：`cv2.imread`，保留 BGR 彩色
2. **转灰度**：用于掩码计算
3. **横线检测与去除**：
   - 用超宽水平结构元素（`1 × 80` 像素）做形态学开运算，提取出近似纯横线区域
   - 从墨迹掩码中减去横线掩码
4. **掩码后处理**：形态学闭运算填补笔画断裂（`3×3` 核）
5. **生成 RGBA PNG**：原图 RGB + 掩码作为 Alpha 通道

### 管线 A：自适应阈值

```
灰度图
  → cv2.adaptiveThreshold(blockSize=15, C=7, ADAPTIVE_THRESH_GAUSSIAN_C)
  → 反转（白纸→0，墨迹→255）
  → 去横线掩码
  → 闭运算
  → RGBA 输出
```

### 管线 B：背景估算

```
灰度图
  → 形态学膨胀（15×15 核）→ 估算背景
  → 原图灰度 - 背景 → 差值图（墨迹区域为亮）
  → 反转 → Otsu 阈值二值化
  → 去横线掩码
  → 闭运算
  → RGBA 输出
```

## 命令行接口

```bash
python extract_handwriting.py <input_image> [-o <output_dir>]
```

- `input_image`：输入图片路径（jpg/png 等）
- `-o`：可选输出目录，默认与输入图片同目录

**输出文件命名：**
- `{stem}_A.png`
- `{stem}_B.png`

## 错误处理

| 情形 | 处理方式 |
|------|----------|
| 文件不存在 | 打印清晰错误信息，退出码 1 |
| 无法解码为图片 | 捕获异常，提示格式不支持 |

## 依赖

```toml
[project]
dependencies = ["opencv-python", "numpy"]
```

通过 `uv` 管理，`uv run extract_handwriting.py` 自动安装依赖。
