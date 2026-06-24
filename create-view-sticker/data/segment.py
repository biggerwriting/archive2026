"""
SAM 图片分割脚本
================
使用 Meta 的 Segment Anything Model (SAM) 自动识别图片中的所有物体，
将每个物体单独抠出，保存为带透明背景的 PNG 文件。

使用步骤：
  1. 下载模型权重文件（见下方说明），放入 models/ 目录
  2. 将要处理的图片放入 input/ 目录
  3. 运行：python3 segment.py
  4. 结果保存在 output/ 目录

模型权重下载（三选一，体积越大、效果越好）：
  - ViT-B（375MB，推荐新手）：
      https://dl.fbaipublicfiles.com/segment_anything/sam_vit_b_01ec64.pth
  - ViT-L（1.2GB）：
      https://dl.fbaipublicfiles.com/segment_anything/sam_vit_l_0b3195.pth
  - ViT-H（2.4GB，最高质量）：
      https://dl.fbaipublicfiles.com/segment_anything/sam_vit_h_4b8939.pth
"""

import os
import sys
import json
import argparse
import numpy as np
import cv2
from PIL import Image
from pathlib import Path


# ──────────────────────────────────────────────────────────────────────────────
# 参数配置
# ──────────────────────────────────────────────────────────────────────────────

def parse_args():
    parser = argparse.ArgumentParser(description="SAM 自动物体分割")

    parser.add_argument(
        "--input",  "-i",
        default="input",
        help="输入图片路径（单张图片或文件夹），默认：input/"
    )
    parser.add_argument(
        "--output", "-o",
        default="output",
        help="输出目录，默认：output/"
    )
    parser.add_argument(
        "--checkpoint", "-c",
        default=None,
        help="模型权重文件路径，不填则自动在 models/ 目录寻找"
    )
    parser.add_argument(
        "--model-type", "-m",
        choices=["vit_b", "vit_l", "vit_h"],
        default=None,
        help="模型类型（自动从文件名推断，或手动指定）"
    )
    parser.add_argument(
        "--min-area",
        type=int,
        default=2000,
        help="过滤掉面积小于此值（像素数）的碎片，默认：2000"
    )
    parser.add_argument(
        "--min-size",
        type=int,
        default=40,
        help="过滤掉宽或高小于此值（像素）的物体，默认：40"
    )
    parser.add_argument(
        "--max-objects",
        type=int,
        default=50,
        help="每张图最多提取多少个物体，默认：50（避免碎片过多）"
    )
    parser.add_argument(
        "--padding",
        type=int,
        default=4,
        help="每个物体裁剪时在边缘留白的像素数，默认：4"
    )
    parser.add_argument(
        "--device",
        default=None,
        help="推理设备：mps（Apple 芯片 GPU）、cuda、cpu；不填则自动选择"
    )
    parser.add_argument(
        "--preview",
        action="store_true",
        help="保存带有所有 mask 叠加的预览图"
    )

    return parser.parse_args()


# ──────────────────────────────────────────────────────────────────────────────
# 工具函数
# ──────────────────────────────────────────────────────────────────────────────

def auto_select_device():
    """
    自动选择最佳推理设备：
      优先 Apple Silicon MPS → CUDA → CPU
    """
    import torch
    if torch.backends.mps.is_available():
        print("  → 使用设备: MPS（Apple Silicon GPU）")
        return "mps"
    elif torch.cuda.is_available():
        print("  → 使用设备: CUDA GPU")
        return "cuda"
    else:
        print("  → 使用设备: CPU（速度较慢，建议等待）")
        return "cpu"


def find_checkpoint_in_models_dir():
    """
    在 models/ 目录自动寻找 .pth 文件，返回 (路径, 模型类型)。
    文件名需包含 vit_b / vit_l / vit_h 字样（官方下载文件默认包含）。
    """
    models_dir = Path(__file__).parent / "models"
    candidates = list(models_dir.glob("*.pth"))

    if not candidates:
        return None, None

    # 找到则取第一个（按文件名排序）
    candidates.sort()
    pth = candidates[0]
    name = pth.stem.lower()

    # 从文件名推断模型类型
    if "vit_h" in name:
        model_type = "vit_h"
    elif "vit_l" in name:
        model_type = "vit_l"
    else:
        model_type = "vit_b"   # 默认当 vit_b 处理

    return str(pth), model_type


def collect_images(input_path):
    """
    收集待处理的图片路径列表。
    支持传入单张图片路径或目录。
    """
    p = Path(input_path)
    exts = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}

    if p.is_file():
        return [p]
    elif p.is_dir():
        images = [f for f in sorted(p.iterdir()) if f.suffix.lower() in exts]
        return images
    else:
        print(f"[错误] 路径不存在：{input_path}")
        sys.exit(1)


# ──────────────────────────────────────────────────────────────────────────────
# SAM 加载
# ──────────────────────────────────────────────────────────────────────────────

def apply_mps_float32_patch():
    """
    MPS（Apple Silicon GPU）不支持 float64（双精度浮点）。
    SAM 内部坐标变换时会产生 float64 张量，在 MPS 上触发报错。

    修复思路：拦截 torch.as_tensor，在"把 numpy 数组送上 MPS"之前，
    如果数组是 float64 就预先转成 float32，避免 MPS 拒绝接受。
    对分割精度几乎没有影响。
    """
    import torch
    import numpy as np
    _orig = torch.as_tensor

    def _patched(data, dtype=None, device=None):
        # 判断目标设备是否是 MPS（device 可能是字符串或 torch.device 对象）
        is_mps = device is not None and "mps" in str(device)

        # 如果目标是 MPS、没有指定 dtype、且输入是 float64 的 numpy 数组
        # → 提前转成 float32，避免 MPS 报错
        if is_mps and dtype is None:
            if isinstance(data, np.ndarray) and data.dtype == np.float64:
                data = data.astype(np.float32)
            elif isinstance(data, torch.Tensor) and data.dtype == torch.float64:
                data = data.float()

        return _orig(data, dtype=dtype, device=device)

    torch.as_tensor = _patched


def load_sam(checkpoint, model_type, device):
    """
    加载 SAM 模型并移动到指定设备。

    SAM 有两种使用方式：
      1. SamPredictor     — 手动指定点/框来分割，需要人工交互
      2. SamAutomaticMaskGenerator — 全自动扫描整张图，不需要任何提示

    这里使用第 2 种（Automatic），适合批量处理。
    """
    from segment_anything import sam_model_registry, SamAutomaticMaskGenerator

    if device == "mps":
        apply_mps_float32_patch()

    print(f"  → 加载模型：{checkpoint}（类型：{model_type}）")
    sam = sam_model_registry[model_type](checkpoint=checkpoint)
    sam.to(device=device)
    sam.eval()   # 推理模式，关闭 dropout 等训练专用层

    # SamAutomaticMaskGenerator 的关键参数：
    #
    #   points_per_side       : 在图上放多密的采样点网格（越大越慢但更全面）
    #   pred_iou_thresh       : mask 预测质量阈值，越高=只保留高置信度 mask
    #   stability_score_thresh: mask 稳定性阈值（多个阈值下 mask 是否一致）
    #   min_mask_region_area  : 后处理时去掉小于此面积的碎洞/碎片
    #
    mask_gen = SamAutomaticMaskGenerator(
        model=sam,
        points_per_side=32,             # 32×32 = 1024 个采样点
        pred_iou_thresh=0.88,
        stability_score_thresh=0.95,
        min_mask_region_area=500,        # SAM 内部也会过滤，之后我们还会再过滤一次
    )

    return mask_gen


# ──────────────────────────────────────────────────────────────────────────────
# 核心：从一张图中分割出所有物体
# ──────────────────────────────────────────────────────────────────────────────

def segment_image(image_path, mask_gen, args, output_dir):
    """
    处理单张图片，返回保存的文件列表。

    SAM 返回的每个 mask 数据结构（字典）：
      {
        "segmentation"       : np.ndarray (H, W, bool) — 哪些像素属于这个物体
        "area"               : int  — 物体像素数
        "bbox"               : [x, y, w, h] — 边界框（XYWH 格式）
        "predicted_iou"      : float — SAM 自评的 mask 质量分
        "stability_score"    : float — 稳定性分数
        "crop_box"           : ...（内部用）
        "point_coords"       : ... — 触发此 mask 的提示点坐标
      }
    """
    print(f"\n处理: {image_path.name}")

    # ── 读图 ──────────────────────────────────────────────────
    # OpenCV 默认读取 BGR，SAM 需要 RGB
    img_bgr = cv2.imread(str(image_path))
    if img_bgr is None:
        print(f"  [跳过] 无法读取图片：{image_path}")
        return []

    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    H, W = img_rgb.shape[:2]
    print(f"  图片尺寸：{W} × {H}")

    # ── 运行 SAM 自动分割 ──────────────────────────────────────
    print("  正在分割（首次运行可能需要数十秒）…")
    masks = mask_gen.generate(img_rgb)
    print(f"  SAM 原始找到 {len(masks)} 个 mask")

    # ── 过滤 ──────────────────────────────────────────────────
    # 1. 按面积从大到小排序，大物体排前面
    masks = sorted(masks, key=lambda m: m["area"], reverse=True)

    # 2. 去掉面积太小的（噪点、纹理碎片）
    masks = [m for m in masks if m["area"] >= args.min_area]

    # 3. 去掉宽/高太小的（细条、点）
    def is_big_enough(m):
        _, _, w, h = m["bbox"]
        return w >= args.min_size and h >= args.min_size
    masks = [m for m in masks if is_big_enough(m)]

    # 4. 去掉几乎覆盖整张图的 mask（通常是背景）
    full_area = H * W
    masks = [m for m in masks if m["area"] < full_area * 0.9]

    # 5. 限制数量上限（取质量最高的前 N 个）
    masks = masks[: args.max_objects]

    print(f"  过滤后保留 {len(masks)} 个物体")

    if not masks:
        print("  [警告] 没有找到符合条件的物体，尝试降低 --min-area 参数")
        return []

    # ── 打开原图（RGBA 模式，支持透明通道）────────────────────
    img_pil = Image.open(str(image_path)).convert("RGBA")
    img_arr = np.array(img_pil)    # shape: (H, W, 4)

    saved_files = []
    stem = image_path.stem         # 不含扩展名的文件名

    # ── 准备标注图（在原图上画框 + 序号）─────────────────────
    # img_bgr 是 OpenCV 格式，拷贝一份用于绘制，不影响原图
    annotated = img_bgr.copy()

    # 配色板（BGR 格式，供 OpenCV 使用）
    # 序号多时循环使用这些颜色
    PALETTE = [
        (0,  212, 255),   # 青色
        (140, 60, 240),   # 紫色
        (0,  200,  80),   # 绿色
        ( 20, 170, 255),  # 橙黄
        (100, 100, 255),  # 粉红
        ( 60, 220, 180),  # 青绿
        (255, 180,  40),  # 蓝色
        (180, 255,  80),  # 青柠
    ]

    # ── 第一遍：画半透明填充（先把所有填充叠到一张 overlay 上再合并）
    # 如果在循环里每次都 addWeighted，填充会越叠越不透明，
    # 所以统一收集到 overlay 再一次性混合。
    overlay = annotated.copy()
    for i, mask_data in enumerate(masks):
        x, y, w, h = [int(v) for v in mask_data["bbox"]]
        color = PALETTE[i % len(PALETTE)]
        cv2.rectangle(overlay, (x, y), (x + w, y + h), color, thickness=-1)

    # alpha=0.12 表示填充只占 12% 的不透明度，其余 88% 保留原图
    cv2.addWeighted(overlay, 0.12, annotated, 0.88, 0, annotated)

    # ── 第二遍：画边框 + 序号徽章 ──────────────────────────────
    FONT       = cv2.FONT_HERSHEY_SIMPLEX
    FONT_SCALE = 0.52
    FONT_THICK = 1

    for i, mask_data in enumerate(masks):
        mask: np.ndarray = mask_data["segmentation"]   # shape: (H, W)
        x, y, w, h = [int(v) for v in mask_data["bbox"]]
        color = PALETTE[i % len(PALETTE)]

        # ── 画边框 ──────────────────────────────────────────
        cv2.rectangle(annotated, (x, y), (x + w, y + h), color, thickness=2)

        # ── 序号徽章 ────────────────────────────────────────
        label = str(i + 1)
        (tw, th), baseline = cv2.getTextSize(label, FONT, FONT_SCALE, FONT_THICK)
        pad_x, pad_y = 5, 3

        # 徽章宽高
        badge_w = tw + pad_x * 2
        badge_h = th + pad_y * 2 + baseline

        # 优先放在边框正下方；如果超出图片底部，改放到边框内部右下角
        bx = x                        # 徽章左边对齐 bbox 左边
        by = y + h + 1                # 紧贴 bbox 下方
        if by + badge_h > H:          # 放不下 → 放到 bbox 内部底部
            by = y + h - badge_h - 1

        # 防止徽章超出右边界
        bx = min(bx, W - badge_w)

        # 画实心背景矩形
        cv2.rectangle(
            annotated,
            (bx, by),
            (bx + badge_w, by + badge_h),
            color,
            thickness=-1,
        )
        # 在背景上写黑色序号（黑色在彩色背景上对比度最好）
        cv2.putText(
            annotated,
            label,
            (bx + pad_x, by + th + pad_y),
            FONT, FONT_SCALE,
            (0, 0, 0),           # 黑色文字
            FONT_THICK,
            cv2.LINE_AA,         # 抗锯齿
        )

        # ── 保存单个物体的透明 PNG ───────────────────────────
        pad = args.padding
        x1 = max(0, x - pad)
        y1 = max(0, y - pad)
        x2 = min(W, x + w + pad)
        y2 = min(H, y + h + pad)

        cropped   = img_arr[y1:y2, x1:x2].copy()
        mask_crop = mask[y1:y2, x1:x2]
        cropped[~mask_crop, 3] = 0

        out_name = f"{stem}_{i+1:03d}.png"
        Image.fromarray(cropped).save(str(output_dir / out_name))
        saved_files.append(out_name)

        iou  = mask_data.get("predicted_iou",   0)
        stab = mask_data.get("stability_score", 0)
        print(f"  [{i+1:02d}] {out_name}  {w}×{h}  置信度:{iou:.2f}  稳定性:{stab:.2f}")

    # ── 保存标注图 ──────────────────────────────────────────────
    ann_path = output_dir / f"{stem}_annotated.jpg"
    cv2.imwrite(str(ann_path), annotated, [cv2.IMWRITE_JPEG_QUALITY, 95])
    print(f"  标注图: {ann_path.name}")

    # ── 可选：额外保存 mask 色块叠加图（--preview 时启用）──────
    if args.preview:
        preview = img_rgb.copy()
        for mask_data in masks:
            mask = mask_data["segmentation"]
            color = np.random.randint(50, 220, 3)
            preview[mask] = (preview[mask] * 0.5 + color * 0.5).astype(np.uint8)
        prev_path = output_dir / f"{stem}_preview.jpg"
        cv2.imwrite(str(prev_path), cv2.cvtColor(preview, cv2.COLOR_RGB2BGR))
        print(f"  mask预览: {prev_path.name}")

    return saved_files


# ──────────────────────────────────────────────────────────────────────────────
# 主入口
# ──────────────────────────────────────────────────────────────────────────────

def main():
    args = parse_args()

    # ── 解析设备 ──────────────────────────────────────────────
    device = args.device or auto_select_device()

    # ── 找到模型权重 ───────────────────────────────────────────
    checkpoint = args.checkpoint
    model_type = args.model_type

    if checkpoint is None:
        checkpoint, inferred_type = find_checkpoint_in_models_dir()
        if checkpoint is None:
            print(
                "\n[错误] 没有找到模型权重文件。\n"
                "请下载后放入 models/ 目录：\n"
                "  ViT-B（375MB）: https://dl.fbaipublicfiles.com/segment_anything/sam_vit_b_01ec64.pth\n"
                "  ViT-L（1.2GB）: https://dl.fbaipublicfiles.com/segment_anything/sam_vit_l_0b3195.pth\n"
                "  ViT-H（2.4GB）: https://dl.fbaipublicfiles.com/segment_anything/sam_vit_h_4b8939.pth\n"
            )
            sys.exit(1)
        if model_type is None:
            model_type = inferred_type
            print(f"  → 自动推断模型类型：{model_type}")

    if model_type is None:
        # 最后保底：从文件名猜
        name = Path(checkpoint).stem.lower()
        model_type = "vit_h" if "vit_h" in name else ("vit_l" if "vit_l" in name else "vit_b")

    # ── 准备输入/输出目录 ──────────────────────────────────────
    script_dir = Path(__file__).parent
    # 如果传入的是相对路径，相对于脚本所在目录解析
    input_path  = Path(args.input)  if Path(args.input).is_absolute()  else script_dir / args.input
    output_dir  = Path(args.output) if Path(args.output).is_absolute() else script_dir / args.output
    output_dir.mkdir(parents=True, exist_ok=True)

    images = collect_images(input_path)
    if not images:
        print(f"[错误] 在 {input_path} 中没有找到图片文件")
        sys.exit(1)

    print(f"\n找到 {len(images)} 张图片，输出目录：{output_dir}\n")

    # ── 加载 SAM 模型（只加载一次，复用） ─────────────────────
    print("加载 SAM 模型…")
    mask_gen = load_sam(checkpoint, model_type, device)

    # ── 逐张处理 ──────────────────────────────────────────────
    all_results = {}
    total_saved = 0

    for img_path in images:
        saved = segment_image(img_path, mask_gen, args, output_dir)
        all_results[img_path.name] = saved
        total_saved += len(saved)

    # ── 保存汇总 JSON（方便后续程序读取） ─────────────────────
    manifest_path = output_dir / "manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)

    print(f"\n{'─'*50}")
    print(f"完成！共提取 {total_saved} 个物体")
    print(f"输出目录：{output_dir}")
    print(f"索引文件：{manifest_path}")


if __name__ == "__main__":
    main()
