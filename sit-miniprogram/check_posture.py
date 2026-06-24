# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "opencv-python",
#     "mediapipe",
#     "numpy",
# ]
# ///
import cv2
import mediapipe as mp
import numpy as np
import urllib.request
import os
import time

from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision

# ── 模型下载（只需一次）────────────────────────────────────
MODEL_PATH = "pose_landmarker_lite.task"

def download_model():
    if os.path.exists(MODEL_PATH):
        return
    url = (
        "https://storage.googleapis.com/mediapipe-models/"
        "pose_landmarker/pose_landmarker_lite/float16/latest/"
        "pose_landmarker_lite.task"
    )
    print("正在下载模型文件（约 5MB），请稍候...")
    urllib.request.urlretrieve(url, MODEL_PATH)
    print("模型下载完成 ✅")

# ── 配置参数 ──────────────────────────────────────────────
HUNCH_THRESHOLD = 0.18   # 头肩距离（归一化），低于此值判定弓腰
ALERT_SECONDS   = 3.0    # 连续弓腰超过 N 秒才报警

# ── 关键点索引（MediaPipe 33点）────────────────────────────
IDX_NOSE        = 0
IDX_L_SHOULDER  = 11
IDX_R_SHOULDER  = 12
IDX_L_HIP       = 23
IDX_R_HIP       = 24
IDX_L_KNEE      = 25
IDX_R_KNEE      = 26
IDX_L_ANKLE     = 27
IDX_R_ANKLE     = 28

# 用于绘制骨架的连接线
CONNECTIONS = [
    (IDX_NOSE, IDX_L_SHOULDER), (IDX_NOSE, IDX_R_SHOULDER),
    (IDX_L_SHOULDER, IDX_R_SHOULDER),
    (IDX_L_SHOULDER, IDX_L_HIP), (IDX_R_SHOULDER, IDX_R_HIP),
    (IDX_L_HIP, IDX_R_HIP),
    (IDX_L_HIP, IDX_L_KNEE), (IDX_R_HIP, IDX_R_KNEE),
    (IDX_L_KNEE, IDX_L_ANKLE), (IDX_R_KNEE, IDX_R_ANKLE),
]


def get_pt(landmarks, idx):
    """返回归一化坐标 (x, y)"""
    lm = landmarks[idx]
    return np.array([lm.x, lm.y])


def analyze_posture(landmarks):
    """
    判断坐姿：
      - 头肩距离过小 → 弓腰/低头
      - 鼻子低于肩膀 → 严重趴伏
    返回 (is_hunching, head_shoulder_dist)
    """
    nose    = get_pt(landmarks, IDX_NOSE)
    l_sh    = get_pt(landmarks, IDX_L_SHOULDER)
    r_sh    = get_pt(landmarks, IDX_R_SHOULDER)
    sh_mid  = (l_sh + r_sh) / 2

    # y 轴向下为正，头在肩上方时 dist > 0
    dist = sh_mid[1] - nose[1]
    nose_below = nose[1] > sh_mid[1]

    is_hunching = dist < HUNCH_THRESHOLD or nose_below
    return is_hunching, dist


def draw_skeleton(frame, landmarks, w, h):
    """绘制关键点和连接线"""
    # 连接线
    for i, j in CONNECTIONS:
        a = landmarks[i]
        b = landmarks[j]
        pt1 = (int(a.x * w), int(a.y * h))
        pt2 = (int(b.x * w), int(b.y * h))
        cv2.line(frame, pt1, pt2, (100, 200, 100), 2)

    # 关键点圆点
    for idx in [IDX_NOSE, IDX_L_SHOULDER, IDX_R_SHOULDER,
                IDX_L_HIP, IDX_R_HIP,
                IDX_L_KNEE, IDX_R_KNEE,
                IDX_L_ANKLE, IDX_R_ANKLE]:
        lm = landmarks[idx]
        cx, cy = int(lm.x * w), int(lm.y * h)
        cv2.circle(frame, (cx, cy), 5, (50, 150, 255), -1)


def draw_feedback(frame, is_hunching, dist, hunch_seconds):
    """在画面上叠加状态文字和进度条"""
    h, w = frame.shape[:2]

    if is_hunching:
        color  = (0, 80, 255)
        status = f"Hunch: {hunch_seconds:.1f}s"
        cv2.rectangle(frame, (0, 0), (w - 1, h - 1), color, 8)
    else:
        color  = (0, 200, 80)
        status = "Good Posture"

    cv2.putText(frame, status, (20, 45),
                cv2.FONT_HERSHEY_SIMPLEX, 1.0, color, 2)

    # 头肩距离进度条
    bar = int(np.clip(dist / 0.35 * 200, 0, 200))
    cv2.rectangle(frame, (20, 65), (220, 82), (60, 60, 60), -1)
    cv2.rectangle(frame, (20, 65), (20 + bar, 82), color, -1)
    cv2.putText(frame, f"dist: {dist:.3f}  (min:{HUNCH_THRESHOLD})",
                (20, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (180, 180, 180), 1)


def run():
    download_model()

    options = vision.PoseLandmarkerOptions(
        base_options=mp_python.BaseOptions(model_asset_path=MODEL_PATH),
        running_mode=vision.RunningMode.VIDEO,
        num_poses=1,
        min_pose_detection_confidence=0.6,
        min_pose_presence_confidence=0.6,
        min_tracking_confidence=0.6,
    )

    cap         = cv2.VideoCapture(0)
    hunch_start = None
    hunch_secs  = 0.0
    start_time  = time.time()

    with vision.PoseLandmarker.create_from_options(options) as landmarker:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            frame = cv2.flip(frame, 1)
            h, w  = frame.shape[:2]

            # 新 API 需要传入毫秒时间戳
            timestamp_ms = int((time.time() - start_time) * 1000)
            rgb    = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_img = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
            result = landmarker.detect_for_video(mp_img, timestamp_ms)

            if result.pose_landmarks:
                landmarks = result.pose_landmarks[0]   # 第一个人

                is_hunching, dist = analyze_posture(landmarks)

                now = time.time()
                if is_hunching:
                    if hunch_start is None:
                        hunch_start = now
                    hunch_secs = now - hunch_start
                else:
                    hunch_start = None
                    hunch_secs  = 0.0

                # 持续弓腰超时 → 终端提示（可改为系统通知）
                if hunch_secs > ALERT_SECONDS:
                    print(f"\r⚠  弓腰已持续 {hunch_secs:.0f}s，请调整坐姿！", end="")

                draw_skeleton(frame, landmarks, w, h)
                draw_feedback(frame, is_hunching, dist, hunch_secs)

            else:
                cv2.putText(frame, "No person detected", (20, 45),
                            cv2.FONT_HERSHEY_SIMPLEX, 1.0, (120, 120, 120), 2)

            cv2.imshow("Posture Monitor", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    cap.release()
    cv2.destroyAllWindows()
    print("\n程序已退出")


if __name__ == "__main__":
    run()
