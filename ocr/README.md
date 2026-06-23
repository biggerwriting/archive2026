# OCR Image MVP (CPU)

Minimal runnable OCR baseline for images on a normal computer (no GPU).

## Features

- Input a single image or a directory of images.
- Run local OCR with PaddleOCR on CPU.
- Output:
  - `*.json` with text, confidence, and coordinates.
  - `*.vis.jpg` visualization image with boxes and labels.

## 1) Install

Python requirement: use Python `3.10` or `3.11` (recommended), not `3.14`.

```bash
# Example with python3.11
python3.11 -m venv .venv
source .venv/bin/activate
pip install -U pip
# If your default index does not provide Paddle packages, force pypi:
# pip install -i https://pypi.org/simple -r requirements.txt
pip install -r requirements.txt
```

## 2) Run

Single image:

```bash
python infer.py --input ./samples/note1.jpg --output ./outputs --use-textline-orientation
```

Directory:

```bash
python infer.py --input ./samples --output ./outputs --use-textline-orientation --min-score 0.5
```

If Chinese labels in `*.vis.jpg` render as `?`, pass a font file explicitly:

```bash
python infer.py --input ./samples --output ./outputs --font-path "/System/Library/Fonts/PingFang.ttc"
```

## 3) Output format

Example JSON:

```json
{
  "image": "/abs/path/samples/note1.jpg",
  "size": [1280, 720],
  "lines": [
    {
      "bbox": [100, 200, 260, 40],
      "quad": [[100, 200], [360, 200], [360, 240], [100, 240]],
      "text": "abc123",
      "score": 0.92
    }
  ],
  "full_text": "abc123"
}
```

## Notes

- First run may download OCR model files.
- For handwritten notes, this is a baseline; collect bad cases and iterate later.
