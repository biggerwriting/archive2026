import librosa
import numpy as np
import os

def analyze_song_structure(file_path, time_signature=4):
    """
    分析音频的 BPM 和小节信息
    :param file_path: 音频文件路径
    :param time_signature: 拍号，流行歌通常为 4 (即 4/4 拍)
    """
    
    # 1. 检查文件是否存在
    if not os.path.exists(file_path):
        print(f"错误: 找不到文件 {file_path}")
        return

    print(f"正在加载音频: {file_path} ... (这可能需要几秒钟)")
    
    # 2. 加载音频
    # y 是音频时间序列，sr 是采样率
    y, sr = librosa.load(file_path)

    print("正在分析节奏和节拍...")

    # 3. 提取 BPM 和 节拍帧 (Beat Frames)
    # tempo: 估算的 BPM
    # beat_frames: 每一拍对应的帧索引
    tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)

    # 4. 将帧索引转换为时间戳 (秒)
    beat_times = librosa.frames_to_time(beat_frames, sr=sr)

    # 5. 推算小节 (Bars)
    # 逻辑：假设 4/4 拍，每 4 个 Beat 组成一个 Bar
    # 注意：Librosa 不一定能完美识别出第一拍是强拍(Downbeat)，这里默认从检测到的第一拍开始计算
    
    total_beats = len(beat_times)
    total_bars = int(total_beats / time_signature)
    
    # 收集每小节的开始时间
    bar_start_times = []
    for i in range(0, total_beats, time_signature):
        # 确保不会越界
        if i < len(beat_times):
            bar_start_times.append(beat_times[i])

    # --- 输出结果 ---
    print("-" * 30)
    print(f"分析结果: {os.path.basename(file_path)}")
    print("-" * 30)
    # 新版本 librosa 返回的 tempo 可能是数组，取出第一个元素
    actual_tempo = tempo[0] if isinstance(tempo, np.ndarray) else tempo
    print(f"估算 BPM (速度): {actual_tempo:.2f}")
    print(f"检测到的总拍数: {total_beats}")
    print(f"估算总小节数 (按 {time_signature}/4 拍计算): {total_bars}")
    print("-" * 30)
    print("每小节开始的时间节点 (秒):")
    
    for i, time_point in enumerate(bar_start_times):
        # 格式化时间为 分:秒.毫秒
        m, s = divmod(time_point, 60)
        print(f"第 {i+1:03d} 小节: {time_point:.3f} 秒 ({int(m)}分{s:.3f}秒)")

    return bar_start_times

# ==========================================
# 执行测试
# ==========================================
if __name__ == "__main__":
    # 请将此处替换为你本地的实际文件路径
    mp3_file = "music/double.mp3" 
    
    # 如果你没有 song1.mp3，代码会报错，请确保文件在同目录下或使用绝对路径
    analyze_song_structure(mp3_file)