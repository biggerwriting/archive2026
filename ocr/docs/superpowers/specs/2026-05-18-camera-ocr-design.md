# 实时摄像头 OCR 设计文档

**日期**：2026-05-18
**状态**：已批准

## 背景

在现有 `infer.py`（基于 PaddleOCR 的静态图片 OCR 工具）基础上，增加实时摄像头输入支持，用于手写文字的实时识别。

## 目标

- 打开摄像头，持续显示实时画面
- 每隔 N 秒（默认 10 秒）自动抓帧送入 PaddleOCR 识别
- 识别结果（检测框 + 文字标签）实时叠加在摄像头画面上
- 按 `q` 键退出

## 不在范围内

- 识别结果保存到文件
- 多摄像头同时处理
- GPU 加速

## 架构

新建 `camera.py`，复用 `infer.py` 中的 `draw_result` 和 `resolve_font`。

### 线程模型

```
主线程：VideoCapture → 读帧 → 叠加最新结果 → imshow → 按 q 退出
OCR线程：每 N 秒取最新帧 → PaddleOCR.predict() → 更新共享结果
```

两个线程通过 `SharedState` 共享数据，使用 `threading.Lock` 保护写操作。

### SharedState

```python
@dataclass
class SharedState:
    lock: threading.Lock
    latest_frame: Optional[np.ndarray]   # 主线程写，OCR线程读
    latest_lines: List[Dict]             # OCR线程写，主线程读
    exit_flag: bool                      # 主线程写，OCR线程读
```

## 组件

| 组件 | 文件 | 职责 |
|------|------|------|
| `SharedState` | `camera.py` | 线程安全的共享状态容器 |
| `ocr_worker(state, ocr, interval)` | `camera.py` | OCR 后台线程：定时推理，更新 `latest_lines` |
| `main()` | `camera.py` | 主循环：读帧、叠加结果、显示、处理退出 |

## 命令行接口

```bash
python camera.py [OPTIONS]

选项：
  --camera INT      摄像头索引（默认 0）
  --interval FLOAT  识别间隔秒数（默认 10）
  --lang STR        OCR 语言（默认 ch）
  --min-score FLOAT 置信度过滤（默认 0.0）
  --font-path STR   中文字体路径（可选）
```

## 显示说明

- 画面左上角显示倒计时："下次识别：Xs"
- 识别中时显示："识别中..."
- 识别框和文字标签持续叠加，直到下次识别刷新
- 首次识别前不显示任何框

## 错误处理

| 情形 | 处理方式 |
|------|----------|
| 摄像头打不开 | 启动时检查 `cap.isOpened()`，报错退出 |
| 帧读取失败 | 跳过该帧，继续循环 |
| OCR 推理异常 | try/except 打印错误，保留上次结果，继续下一轮 |
| 识别结果为空 | 保留上一次叠加结果，不清空 |
| 按 q 退出 | 设置 `exit_flag=True`，OCR 线程自行退出，主线程 join 后清理 |

## 文件变更

- **新增** `camera.py`：摄像头实时 OCR 主脚本
- **不修改** `infer.py`：直接 import 复用其函数
