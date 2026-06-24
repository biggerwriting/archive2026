"""
基于 SAM 的背景去除 + 透明边角裁剪
适合背景相对干净（纯色/渐变墙面/地面）的图片

使用：.venv/bin/python3 remove_bg.py <输入图片> [输出路径]

依赖：sam/models/ 目录下有 SAM 权重文件（sam_vit_b_01ec64.pth 等）
"""
import sys
import json
from io import BytesIO
from pathlib import Path

import cv2
import numpy as np
from PIL import Image


# ──────────────────────────────────────────────────────────────────────────────
# MPS float64 补丁（Apple Silicon 兼容）
# ──────────────────────────────────────────────────────────────────────────────
def apply_mps_patch():
    import torch
    import numpy as np
    if not torch.backends.mps.is_available():
        return
    _orig = torch.as_tensor
    def _patched(data, dtype=None, device=None):
        is_mps = device is not None and "mps" in str(device)
        if is_mps and dtype is None:
            if isinstance(data, np.ndarray) and data.dtype == np.float64:
                data = data.astype(np.float32)
            elif isinstance(data, torch.Tensor) and data.dtype == torch.float64:
                data = data.float()
        return _orig(data, dtype=dtype, device=device)
    torch.as_tensor = _patched


# ──────────────────────────────────────────────────────────────────────────────
# 自动选 SAM 权重
# ──────────────────────────────────────────────────────────────────────────────
def find_checkpoint():
    script_dir = Path(__file__).parent
    candidates = sorted((script_dir / "sam" / "models").glob("*.pth"))
    if not candidates:
        sys.exit("❌ 没有找到 SAM 权重，请先把 .pth 文件放到 sam/models/ 目录")
    pth = candidates[0]
    name = pth.stem.lower()
    model_type = "vit_h" if "vit_h" in name else ("vit_l" if "vit_l" in name else "vit_b")
    return str(pth), model_type


# ──────────────────────────────────────────────────────────────────────────────
# 判断某个 mask 是否"接触边缘"（=很可能是背景）
# ──────────────────────────────────────────────────────────────────────────────
def touches_border(mask: np.ndarray, margin: int = 3) -> bool:
    """mask 形状 (H, W)，True 表示属于该区域。"""
    return (
        mask[:margin, :].any()     # 上边
        or mask[-margin:, :].any() # 下边
        or mask[:, :margin].any()  # 左边
        or mask[:, -margin:].any() # 右边
    )


# ──────────────────────────────────────────────────────────────────────────────
# 主流程
# ──────────────────────────────────────────────────────────────────────────────
def remove_bg_sam(input_path: str, output_path: str = None,
                  min_area: int = 1000, border_margin: int = 5):
    input_path = Path(input_path)
    if output_path is None:
        output_path = input_path.parent / f"{input_path.stem}_nobg.png"
    output_path = Path(output_path)

    # 1. 加载图片
    img_bgr = cv2.imread(str(input_path))
    if img_bgr is None:
        sys.exit(f"❌ 无法读取图片：{input_path}")
    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    H, W = img_rgb.shape[:2]
    print(f"图片尺寸：{W} × {H}")

    # 2. 加载 SAM
    import torch
    apply_mps_patch()
    from segment_anything import sam_model_registry, SamAutomaticMaskGenerator

    checkpoint, model_type = find_checkpoint()
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    print(f"加载 SAM（{model_type}，设备：{device}）…")

    sam = sam_model_registry[model_type](checkpoint=checkpoint)
    sam.to(device=device)
    sam.eval()

    # points_per_side 越大识别越细，但越慢
    mask_gen = SamAutomaticMaskGenerator(
        sam,
        points_per_side=32,
        pred_iou_thresh=0.88,
        stability_score_thresh=0.92,
        min_mask_region_area=min_area,
    )

    # 3. 分割
    print("正在分割…")
    masks = mask_gen.generate(img_rgb)
    print(f"SAM 共找到 {len(masks)} 个区域")

    # 4. 把"接触边缘的大块"判定为背景，其余合并为前景
    full_area = H * W
    foreground = np.zeros((H, W), dtype=bool)
    bg_count = 0

    # 按面积从大到小，优先处理大块
    masks_sorted = sorted(masks, key=lambda m: m["area"], reverse=True)

    for m in masks_sorted:
        seg: np.ndarray = m["segmentation"]     # bool (H, W)
        area_ratio = m["area"] / full_area

        # 跳过极小碎片
        if m["area"] < min_area:
            continue

        # 接触边缘 → 判定为背景（墙、地板、天花板通常都触及图边）
        # 面积 > 3% 才算（太小的边缘碎片可能是前景物体的一角，跳过）
        if touches_border(seg, border_margin) and area_ratio > 0.03:
            bg_count += 1
            continue

        # 面积 > 60% 直接当背景（整张图大的 mask）
        if area_ratio > 0.60:
            bg_count += 1
            continue

        foreground |= seg

    print(f"判定为背景的区域：{bg_count} 个，合并前景区域…")

    # 5. 形态学处理：填洞 + 轻微腐蚀，让边缘更干净
    fg_uint8 = foreground.astype(np.uint8) * 255
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    fg_uint8 = cv2.morphologyEx(fg_uint8, cv2.MORPH_CLOSE, kernel, iterations=2)
    fg_uint8 = cv2.morphologyEx(fg_uint8, cv2.MORPH_DILATE, kernel, iterations=1)

    # 6. 应用 alpha 通道
    img_pil = Image.open(str(input_path)).convert("RGBA")
    arr = np.array(img_pil)
    arr[:, :, 3] = fg_uint8           # alpha = 前景 mask

    # 7. 裁剪透明边角
    alpha = arr[:, :, 3]
    rows = np.any(alpha > 0, axis=1)
    cols = np.any(alpha > 0, axis=0)

    if not rows.any():
        print("⚠️  前景全透明，尝试调整 border_margin 参数或检查图片")
        Image.fromarray(arr).save(str(output_path))
    else:
        pad = 4
        top,    bottom = np.where(rows)[0][[0, -1]]
        left,   right  = np.where(cols)[0][[0, -1]]
        top    = max(0, top    - pad)
        left   = max(0, left   - pad)
        bottom = min(H, bottom + pad + 1)
        right  = min(W, right  + pad + 1)

        result = Image.fromarray(arr).crop((left, top, right, bottom))
        result.save(str(output_path))
        print(f"裁剪后尺寸：{result.width} × {result.height}")

    print(f"✅ 已保存：{output_path}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: .venv/bin/python3 remove_bg.py <输入图片> [输出路径]")
        sys.exit(1)
    inp = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else None
    remove_bg_sam(inp, out)
