# music-trans 音乐转谱工具

把一首 MP3，变成可以看、可以练的乐谱。

---

## 这是什么

一个用 Python 写的小工具，核心流程：

```
MP3 音频  →  MIDI 文件（AI 识别音符）  →  MusicXML 乐谱（可在 MuseScore 打开）
```

附带两个辅助脚本：
- 分析歌曲的 BPM 和每小节时间节点
- 用 FFmpeg 无损截取 MP3 片段

动机很简单：听到好听的钢琴段，想知道它弹的什么。

---

## 功能

| 脚本 | 做什么 |
|---|---|
| `trans_music.py` | 主流程：MP3 → MIDI → MusicXML 乐谱 |
| `beat.py` | 节奏分析：输出 BPM、总拍数、每小节开始时间 |
| `cut.py` | 无损截取 MP3 片段，方便只转某一段 |

---

## 技术栈

| 工具 | 用途 | 备注 |
|---|---|---|
| **Basic Pitch** (Spotify) | 音频 → MIDI | 基于 ICASSP 2022 论文的深度学习模型 |
| **TensorFlow 2.15 / Keras** | Basic Pitch 推理框架 | Mac 用 tensorflow-macos |
| **music21** | MIDI → MusicXML，节奏量化 | MIT 开发的音乐分析库 |
| **librosa** | BPM 检测、节拍帧提取 | 音频分析标准库 |
| **FFmpeg** | 无损音频截取 | `-c copy` 模式，不重新编码 |
| **Python 3.11** | 运行环境 | |

### 亮点

- **Spotify Basic Pitch** 是目前开源效果最好的音高识别模型之一，比传统方法准确很多
- **无损截取**：FFmpeg `-c copy` 直接复制音频流，不解码再编码，速度极快且无质量损失
- **节奏量化**：music21 的 `quantize([4])` 把 AI 识别出的"有点飘"的音符时值对齐到最近的节拍格，让乐谱更易读

---

## 部署 & 运行

### 环境准备

项目自带虚拟环境 `venv-final`（已装好所有依赖），直接用：

```bash
cd /path/to/music-trans
source venv-final/bin/activate
```

如果要从零创建（参考）：

```bash
python3.11 -m venv venv-final
source venv-final/bin/activate
pip install -r requirements.txt
```

> 注：`tensorflow-macos` 只适用于 Apple Silicon / Intel Mac，Windows/Linux 换成普通 `tensorflow`。

另外需要系统里装了 **FFmpeg**（`cut.py` 用到）：

```bash
brew install ffmpeg
```

可选：安装 **MuseScore**，`trans_music.py` 会自动调用它弹出乐谱预览。

---

### 运行

#### 音频转乐谱（主流程）

```bash
python trans_music.py
```

默认处理 `music/tonghua.mp3`，输出到 `output/`。

要换歌，改最后一行：

```python
audio_to_sheet_music('music/piano.mp3', './output')
```

输出文件：
- `output/<名称>_basic_pitch.mid` — MIDI 文件
- `output/<名称>.musicxml` — 乐谱文件，用 MuseScore 打开

---

#### 节奏 / BPM 分析

```bash
python beat.py
```

默认分析 `music/double.mp3`，输出类似：

```
估算 BPM (速度): 143.36
检测到的总拍数: 312
估算总小节数 (按 4/4 拍计算): 78
第 001 小节: 0.371 秒 (0分0.371秒)
第 002 小节: 1.487 秒 (0分1.487秒)
...
```

---

#### 截取音频片段

```bash
python cut.py
```

默认截取 `double.mp3` 第 143～155 秒，改参数：

```python
cut_mp3_lossless("music/piano.mp3", 30, 60, "music/piano-30s.mp3")
#                  源文件            起秒 止秒  输出路径
```

---

### 典型工作流

```bash
# 1. 分析歌曲节奏，找到想要的小节时间
python beat.py

# 2. 截取那一段
python cut.py   # 编辑里面的时间参数

# 3. 转成乐谱
# 编辑 trans_music.py，指向截取的片段
python trans_music.py

# 4. 用 MuseScore 打开 output/*.musicxml 查看 & 练习
```

---

## 已测试的音频

| 文件 | 说明 |
|---|---|
| `music/tonghua.mp3` | 童话（已有转谱输出）|
| `music/piano.mp3` | 钢琴曲（已有转谱输出）|
| `music/double.mp3` | 双节棍 |
| `music/night_chapter_7.mp3` | 夜的第七章 |

---

## 已知局限

- AI 识别对**纯乐器**（钢琴、吉他）效果好，**人声混音**识别会有偏差
- 节奏量化是简单对齐到四分音符，复杂切分节奏可能失真
- librosa 的 Downbeat（强拍）识别不一定准，第一个小节可能不是真正的第 1 拍
- Basic Pitch 跑起来需要 TensorFlow，首次推理有几秒加载时间
