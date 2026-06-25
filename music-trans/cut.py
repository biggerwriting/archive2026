import subprocess
import os

def cut_mp3_lossless(source_path, start_sec, end_sec, target_path):
    """
    使用 FFmpeg 命令行进行无损截取 (速度极快)
    """
    if not os.path.exists(source_path):
        print("文件不存在")
        return

    # 构建 ffmpeg 命令
    # -ss: 开始时间
    # -to: 结束时间
    # -c copy: 直接复制流，不重新编码 (关键!)
    cmd = [
        'ffmpeg',
        '-y',               # 覆盖输出文件不询问
        '-i', source_path,  # 输入文件
        '-ss', str(start_sec),
        '-to', str(end_sec),
        '-c', 'copy',       # 复制模式
        target_path
    ]
    
    try:
        # 运行命令，不显示冗余日志
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"无损截取成功: {target_path}")
    except subprocess.CalledProcessError:
        print("FFmpeg 执行出错，请检查是否安装了 FFmpeg 且路径包含在环境变量中。")

# 使用示例
cut_mp3_lossless("music/double.mp3", 143, 155, "music/double-143.mp3")