"""
手写字提取工具
处理光线不均、输出统一颜色、边缘平滑无锯齿。
支持单张图片或整个文件夹批量处理。

算法：
  1. 大范围高斯模糊估算背景亮度（消除光照不均）
  2. 原图 ÷ 背景 → 归一化（墨迹变成相对暗区）
  3. 软阈值生成渐变 Alpha（边缘平滑，无锯齿）
  4. 对 Alpha 二次轻微模糊（进一步消锯齿）
  5. 输出：指定颜色 RGB + 平滑 Alpha

用法:
    # 单张图片
    uv run extract_handwriting.py photo.jpg [-o output/]

    # 整个文件夹（递归处理所有图片）
    uv run extract_handwriting.py photos/ [-o output/]

    # 常用选项
    uv run extract_handwriting.py photos/ --color 30 30 80 --sensitivity 0.6
"""

import argparse
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

# 支持的图片扩展名
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".webp", ".heic"}


# ─────────────────────────────────────────────
# 核心算法
# ─────────────────────────────────────────────

def load_image(path: Path) -> np.ndarray:
    """读取图片，返回灰度图"""
    img = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError(f"无法读取图片：{path}（格式不支持或文件损坏）")
    return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)


def extract(
    gray: np.ndarray,
    ink_color: tuple[int, int, int] = (0, 0, 0),
    bg_sigma: float = 80.0,
    low: float = 0.08,
    high: float = 0.45,
    edge_blur: float = 0.8,
) -> np.ndarray:
    """
    光照均匀化 + 软阈值提取，输出 RGBA。

    Parameters
    ----------
    gray       : 灰度输入图
    ink_color  : 墨迹 RGB 颜色，默认纯黑 (0,0,0)
    bg_sigma   : 背景估算高斯半径（px）。越大 → 能处理更大范围的光照渐变
    low        : 墨迹强度低于此值 → 完全透明（过滤背景噪点）
    high       : 墨迹强度高于此值 → 完全不透明（纯墨迹）
    edge_blur  : 对 Alpha 的二次平滑半径（px），消除边缘锯齿
    """
    gray_f = gray.astype(np.float32)

    # 步骤 1：估算背景亮度（大范围高斯模糊，把墨迹"化开"）
    bg = cv2.GaussianBlur(gray_f, (0, 0), sigmaX=bg_sigma)
    bg = np.maximum(bg, 1.0)

    # 步骤 2：归一化（消除光照不均）
    # normalized ≈ 1.0 → 纸张背景；< 1.0 → 墨迹（比背景更暗）
    normalized = gray_f / bg

    # 步骤 3：墨迹强度 [0, 1]
    ink = np.clip(1.0 - normalized, 0.0, 1.0)

    # 步骤 4：软阈值 → 渐变 Alpha（核心：消除锯齿）
    # low 以下：完全透明；high 以上：完全不透明；中间：线性过渡
    alpha_f = (ink - low) / max(high - low, 1e-6)
    alpha_f = np.clip(alpha_f, 0.0, 1.0)

    # 步骤 5：对 Alpha 二次高斯平滑（进一步消除边缘锯齿）
    if edge_blur > 0:
        alpha_f = cv2.GaussianBlur(alpha_f, (0, 0), sigmaX=edge_blur)
        alpha_f = np.clip(alpha_f, 0.0, 1.0)

    # 步骤 6：组装 RGBA（统一颜色 + 平滑 Alpha）
    r, g, b = ink_color
    alpha_u8 = (alpha_f * 255).astype(np.uint8)
    h, w = gray.shape
    rgba = np.zeros((h, w, 4), dtype=np.uint8)
    rgba[:, :, 0] = r
    rgba[:, :, 1] = g
    rgba[:, :, 2] = b
    rgba[:, :, 3] = alpha_u8

    return rgba


# ─────────────────────────────────────────────
# 单张处理
# ─────────────────────────────────────────────

def process_one(
    src: Path,
    out_dir: Path,
    ink_color: tuple[int, int, int],
    low: float,
    high: float,
) -> bool:
    """
    处理单张图片，保存到 out_dir。
    返回 True 表示成功，False 表示跳过/失败。
    """
    out_path = out_dir / f"{src.stem}_extracted.png"
    try:
        gray = load_image(src)
        rgba = extract(gray, ink_color=ink_color, low=low, high=high)
        Image.fromarray(rgba, mode="RGBA").save(str(out_path))
        return True
    except Exception as e:
        print(f"  ✗ 失败：{e}", file=sys.stderr)
        return False


# ─────────────────────────────────────────────
# 收集图片文件
# ─────────────────────────────────────────────

def collect_images(root: Path, recursive: bool) -> list[Path]:
    """从文件夹收集所有支持的图片文件，按文件名排序。"""
    pattern = "**/*" if recursive else "*"
    files = [
        p for p in root.glob(pattern)
        if p.is_file() and p.suffix.lower() in IMAGE_EXTS
    ]
    return sorted(files)


# ─────────────────────────────────────────────
# 主逻辑
# ─────────────────────────────────────────────

def run(
    input_path: str,
    output_dir: str | None,
    ink_color: tuple[int, int, int],
    sensitivity: float,
    recursive: bool,
):
    p = Path(input_path).resolve()
    if not p.exists():
        print(f"错误：路径不存在 —— {p}", file=sys.stderr)
        sys.exit(1)

    # sensitivity → low / high 阈值
    low  = max(0.02, 0.14 - sensitivity * 0.10)        # 0.04 ~ 0.14
    high = max(low + 0.15, 0.55 - sensitivity * 0.20)  # 0.35 ~ 0.55

    # ── 单张图片 ──────────────────────────────────────────────────────
    if p.is_file():
        if p.suffix.lower() not in IMAGE_EXTS:
            print(f"错误：不支持的文件格式 {p.suffix}", file=sys.stderr)
            sys.exit(1)
        out_dir = Path(output_dir).resolve() if output_dir else p.parent
        out_dir.mkdir(parents=True, exist_ok=True)
        print(f"处理：{p.name}")
        ok = process_one(p, out_dir, ink_color, low, high)
        if ok:
            print(f"→ 已保存至 {out_dir / (p.stem + '_extracted.png')}")
        sys.exit(0 if ok else 1)

    # ── 文件夹批量处理 ────────────────────────────────────────────────
    images = collect_images(p, recursive)
    if not images:
        print(f"未在 {p} 中找到图片文件（支持格式：{', '.join(sorted(IMAGE_EXTS))}）")
        sys.exit(0)

    # 输出目录：未指定时在输入文件夹内创建 extracted/ 子目录
    out_root = Path(output_dir).resolve() if output_dir else p / "extracted"
    out_root.mkdir(parents=True, exist_ok=True)

    total = len(images)
    ok_count = 0
    fail_count = 0
    width = len(str(total))  # 进度数字宽度对齐

    print(f"找到 {total} 张图片，输出到：{out_root}")
    print(f"颜色={ink_color}，灵敏度={sensitivity:.1f}"
          f"{'，递归子目录' if recursive else ''}")
    print()

    for i, src in enumerate(images, 1):
        # 批量时保留相对目录结构（仅在递归模式下有意义）
        rel = src.relative_to(p)
        out_dir = out_root / rel.parent
        out_dir.mkdir(parents=True, exist_ok=True)

        label = f"[{i:{width}d}/{total}] {rel}"
        print(label, end="  ", flush=True)

        ok = process_one(src, out_dir, ink_color, low, high)
        if ok:
            ok_count += 1
            print("✓")
        else:
            fail_count += 1

    print()
    print(f"完成：{ok_count} 成功 / {fail_count} 失败 / {total} 总计")
    sys.exit(0 if fail_count == 0 else 1)


# ─────────────────────────────────────────────
# CLI 入口
# ─────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="手写字提取：光照均匀化 + 平滑无锯齿输出，支持批量处理",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""示例：
  uv run extract_handwriting.py photo.jpg
  uv run extract_handwriting.py photos/ -o output/
  uv run extract_handwriting.py photos/ -r --color 30 30 80 --sensitivity 0.7
""",
    )
    parser.add_argument("input",
                        help="输入图片路径 或 包含图片的文件夹")
    parser.add_argument("-o", "--output-dir", default=None,
                        help="输出目录（单张默认同目录；批量默认在输入文件夹内创建 extracted/）")
    parser.add_argument("-r", "--recursive", action="store_true",
                        help="递归处理子文件夹（仅批量模式有效）")
    parser.add_argument("--color", nargs=3, type=int, default=[0, 0, 0],
                        metavar=("R", "G", "B"),
                        help="墨迹颜色 RGB，默认纯黑 0 0 0")
    parser.add_argument("--sensitivity", type=float, default=0.5,
                        help="提取灵敏度 0.0~1.0（默认 0.5）")
    args = parser.parse_args()

    run(
        args.input,
        args.output_dir,
        ink_color=tuple(args.color),
        sensitivity=args.sensitivity,
        recursive=args.recursive,
    )


if __name__ == "__main__":
    main()
