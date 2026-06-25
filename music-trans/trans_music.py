import os
from basic_pitch.inference import predict_and_save
from basic_pitch import ICASSP_2022_MODEL_PATH
from music21 import converter, environment

def audio_to_sheet_music(audio_path, output_directory='./output'):
    # 1. 使用 Basic Pitch AI 模型将 MP3 转为 MIDI
    # predict_and_save 会自动生成 MIDI 文件
    print("正在进行AI转录 (Audio -> MIDI)...")
    predict_and_save(
        [audio_path],
        output_directory,
        save_midi=True,
        sonify_midi=False,
        save_model_outputs=False,
        save_notes=False,
        model_or_model_path=ICASSP_2022_MODEL_PATH
    )
    
    # 获取生成的 MIDI 文件路径 (Basic Pitch 默认使用原文件名)
    base_name = os.path.splitext(os.path.basename(audio_path))[0]
    midi_path = os.path.join(output_directory, base_name + "_basic_pitch.mid")
    
    if not os.path.exists(midi_path):
        print("MIDI 生成失败")
        return

    # 2. 使用 Music21 将 MIDI 转为乐谱 (MusicXML/PDF)
    print("正在生成乐谱 (MIDI -> Sheet Music)...")
    try:
        # 加载 MIDI 文件
        score = converter.parse(midi_path)
        
        # 简单量化（修正节奏，使谱面更易读）
        score.quantize([4], processOffsets=True, processDurations=True, inPlace=True)
        
        # 方式A: 直接弹出 MuseScore 查看 (需要电脑上安装了 MuseScore)
        score.show() 
        
        # 方式B: 保存为 MusicXML (通用乐谱格式)
        xml_path = os.path.join(output_directory, base_name + ".musicxml")
        score.write('musicxml', fp=xml_path)
        print(f"乐谱已保存至: {xml_path}")
        
    except Exception as e:
        print(f"乐谱生成出错: {e}")

if __name__ == "__main__":
    # 使用示例
    audio_to_sheet_music('tonghua.mp3', './output')
