import json
from paddleocr import PaddleOCR

ocr = PaddleOCR(lang='ch', device='cpu')
raw = ocr.predict('samples/note1.jpg')

first = raw[0]
print("type(first):", type(first))

if hasattr(first, "json"):
    data = first.json
    print("keys in first.json:", list(data.keys()))
    res = data.get("res", {})
    print("keys in res:", list(res.keys()) if isinstance(res, dict) else type(res))
    for k, v in res.items():
        if isinstance(v, list):
            print(f"  {k}: len={len(v)}, first item={v[0] if v else 'empty'}")
        else:
            print(f"  {k}: {v}")
elif isinstance(first, dict):
    print("dict keys:", list(first.keys()))
