from paddleocr import PaddleOCR

ocr = PaddleOCR(use_angle_cls=True, lang='ch')  # 中文
result = ocr.predict('samples/note1.jpg')

for res in result:
    for item in res['rec_texts']:
        print(item)