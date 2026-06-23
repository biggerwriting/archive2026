import argparse
import json
import time
from pathlib import Path
from typing import Any, Dict, List, Sequence

import cv2
import numpy as np
from paddleocr import PaddleOCR
from PIL import Image, ImageDraw, ImageFont


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run OCR for image file(s), output JSON and visualization."
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Input image path or directory containing images.",
    )
    parser.add_argument(
        "--output",
        default="outputs",
        help="Output directory for JSON and visualization images.",
    )
    parser.add_argument(
        "--lang",
        default="ch",
        help="OCR language model, e.g. ch, en, chinese_cht.",
    )
    parser.add_argument(
        "--min-score",
        type=float,
        default=0.0,
        help="Filter out lines below this confidence score.",
    )
    parser.add_argument(
        "--use-textline-orientation",
        action="store_true",
        dest="use_textline_orientation",
        help="Enable text-line orientation classification for rotated text.",
    )
    # Backward-compatible alias for older docs/commands.
    parser.add_argument(
        "--use-angle-cls",
        action="store_true",
        dest="use_textline_orientation",
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--font-path",
        default="",
        help="Optional font file path (.ttf/.ttc) used for drawing labels.",
    )
    return parser.parse_args()


def collect_images(input_path: Path) -> List[Path]:
    image_exts = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
    if input_path.is_file():
        return [input_path]

    images = []
    for p in sorted(input_path.rglob("*")):
        if p.is_file() and p.suffix.lower() in image_exts:
            images.append(p)
    return images


def quad_to_bbox(quad: Sequence[Sequence[float]]) -> List[int]:
    pts = np.array(quad, dtype=np.float32)
    x_min = int(np.floor(pts[:, 0].min()))
    y_min = int(np.floor(pts[:, 1].min()))
    x_max = int(np.ceil(pts[:, 0].max()))
    y_max = int(np.ceil(pts[:, 1].max()))
    return [x_min, y_min, x_max - x_min, y_max - y_min]


def resolve_font(font_path: str, font_size: int) -> ImageFont.FreeTypeFont:
    candidates = []
    if font_path:
        candidates.append(font_path)
    candidates.extend(
        [
            "/System/Library/Fonts/PingFang.ttc",
            "/System/Library/Fonts/Hiragino Sans GB.ttc",
            "/System/Library/Fonts/STHeiti Medium.ttc",
            "/Library/Fonts/Arial Unicode.ttf",
        ]
    )
    for candidate in candidates:
        p = Path(candidate)
        if p.exists():
            try:
                return ImageFont.truetype(str(p), font_size)
            except OSError:
                continue
    return ImageFont.load_default()


def draw_result(
    image: np.ndarray,
    lines: List[Dict[str, Any]],
    font_path: str = "",
    font_size: int = 20,
) -> np.ndarray:
    vis = image.copy()
    overlay = vis.copy()
    label_items: List[Dict[str, Any]] = []

    for line in lines:
        score = line["score"]
        text = line["text"]
        quad = line.get("quad")
        color = (0, 200, 0)  # BGR

        if quad and len(quad) >= 4:
            pts = np.array(quad, dtype=np.int32).reshape((-1, 1, 2))
            cv2.fillPoly(overlay, [pts], color)
            cv2.polylines(vis, [pts], True, color, 2)
            anchor_x = int(np.min(pts[:, 0, 0]))
            anchor_y = int(np.min(pts[:, 0, 1]))
        else:
            x, y, w, h = line["bbox"]
            cv2.rectangle(overlay, (x, y), (x + w, y + h), color, -1)
            cv2.rectangle(vis, (x, y), (x + w, y + h), color, 2)
            anchor_x, anchor_y = x, y

        label = f"{score:.2f} {text[:20]}"
        label_items.append(
            {
                "x": max(0, anchor_x + 2),
                "y": max(0, anchor_y + 2),
                "label": label,
            }
        )

    vis = cv2.addWeighted(overlay, 0.22, vis, 0.78, 0.0)

    pil_img = Image.fromarray(cv2.cvtColor(vis, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(pil_img)
    font = resolve_font(font_path, font_size)
    img_w, img_h = pil_img.size

    for item in label_items:
        label_x = item["x"]
        label_y = item["y"]
        label = item["label"]
        left, top, right, bottom = draw.textbbox((label_x, label_y), label, font=font)
        box_w = right - left
        box_h = bottom - top
        if label_x + box_w + 4 > img_w:
            label_x = max(0, img_w - box_w - 4)
        if label_y + box_h + 4 > img_h:
            label_y = max(0, img_h - box_h - 4)
        left, top, right, bottom = draw.textbbox((label_x, label_y), label, font=font)
        draw.rectangle(
            [left - 2, top - 2, right + 2, bottom + 2],
            fill=(255, 255, 255),
        )
        draw.text((label_x, label_y), label, fill=(220, 20, 60), font=font)

    return cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)


def run_ocr_on_image(
    ocr: PaddleOCR, image_path: Path, min_score: float
) -> Dict[str, Any]:
    img = cv2.imread(str(image_path))
    if img is None:
        raise ValueError(f"Failed to read image: {image_path}")

    lines: List[Dict[str, Any]] = []
    full_text_parts: List[str] = []

    raw = ocr.predict(str(image_path))
    if raw:
        first = raw[0]
        data = None

        # PaddleOCR 3.x result object
        if hasattr(first, "json"):
            data = first.json.get("res", {})
        # Defensive compatibility for dict-style returns
        elif isinstance(first, dict):
            data = first.get("res", first)

        if isinstance(data, dict):
            # rec_polys is strictly aligned with rec_texts/rec_scores.
            polys = data.get("rec_polys", []) or data.get("dt_polys", [])
            rec_texts = data.get("rec_texts", [])
            rec_scores = data.get("rec_scores", [])
            for quad, text, score in zip(polys, rec_texts, rec_scores):
                score = float(score)
                if score < min_score:
                    continue

                bbox = quad_to_bbox(quad)
                line = {
                    "bbox": bbox,
                    "quad": [[float(p[0]), float(p[1])] for p in quad],
                    "text": str(text),
                    "score": score,
                }
                lines.append(line)
                full_text_parts.append(str(text))
        # PaddleOCR 2.x legacy return format
        elif first:
            for item in first:
                quad = item[0]
                text, score = item[1]
                score = float(score)
                if score < min_score:
                    continue

                bbox = quad_to_bbox(quad)
                line = {
                    "bbox": bbox,
                    "quad": [[float(p[0]), float(p[1])] for p in quad],
                    "text": text,
                    "score": score,
                }
                lines.append(line)
                full_text_parts.append(text)

    return {
        "image": str(image_path),
        "size": [int(img.shape[1]), int(img.shape[0])],
        "lines": lines,
        "full_text": "\n".join(full_text_parts),
    }


def save_output(
    image_path: Path,
    result: Dict[str, Any],
    output_dir: Path,
    font_path: str,
) -> None:
    stem = image_path.stem
    json_path = output_dir / f"{stem}.json"
    vis_path = output_dir / f"{stem}.vis.jpg"

    with json_path.open("w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    img = cv2.imread(str(image_path))
    vis = draw_result(img, result["lines"], font_path=font_path)
    cv2.imwrite(str(vis_path), vis)


def main() -> None:
    args = parse_args()
    input_path = Path(args.input).expanduser().resolve()
    output_dir = Path(args.output).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    if not input_path.exists():
        raise FileNotFoundError(f"Input path does not exist: {input_path}")

    image_paths = collect_images(input_path)
    if not image_paths:
        raise RuntimeError("No supported images found.")

    print("Initializing PaddleOCR (first run may download models)...")
    ocr = PaddleOCR(
        use_textline_orientation=args.use_textline_orientation,
        lang=args.lang,
        device="cpu",
        use_doc_orientation_classify=False,
        use_doc_unwarping=False,
    )

    print(f"Found {len(image_paths)} image(s).")
    for idx, image_path in enumerate(image_paths, start=1):
        start_t = time.perf_counter()
        try:
            result = run_ocr_on_image(ocr, image_path, min_score=args.min_score)
            save_output(image_path, result, output_dir, font_path=args.font_path)
            elapsed_ms = (time.perf_counter() - start_t) * 1000.0
            print(
                f"[{idx}/{len(image_paths)}] OK: {image_path.name} "
                f"-> {image_path.stem}.json / {image_path.stem}.vis.jpg "
                f"({elapsed_ms:.1f} ms)"
            )
        except Exception as e:
            print(f"[{idx}/{len(image_paths)}] FAIL: {image_path.name}: {e}")

    print(f"Done. Outputs in: {output_dir}")


if __name__ == "__main__":
    main()
