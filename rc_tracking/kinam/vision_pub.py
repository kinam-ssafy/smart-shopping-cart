import cv2
import numpy as np
import zmq
import json
import time
import torch
from ultralytics import YOLO
from deep_sort_realtime.deepsort_tracker import DeepSort

# hi

# ====================================================================
# 🎛️ [USER CONFIG] 여기서 모든 수치를 조정하세요!
# ====================================================================

# 1. 👁️ 탐지 (YOLO) 관련
MODEL_FILE = 'yolo26m.engine'   # 사용할 모델 파일명
CONF_THRESHOLD = 0.5            # (기본 0.4) 낮을수록 잘 잡지만, 엉뚱한 것도 잡을 수 있음
                                # 높으면 정확하지만, 옆모습이나 멀리 있는 걸 놓침

# 2. 🎯 추적 (DeepSORT) 관련 - "반응속도" 핵심
TRACK_MAX_AGE = 10              # (기본 15) 타겟 놓쳤을 때 박스 유지 시간 (프레임 수)
                                # 🔴 중요: 이 값을 줄이면(예: 5~10) 멈출 때 박스도 바로 사라짐 (즉각 반응)
                                # 늘리면(예: 60~90) 장애물 뒤에 숨어도 오래 기억함 (안정성)
TRACK_N_INIT = 5                # (기본 5) 처음 발견 시 몇 번 연속으로 보여야 인정할지
                                # 높이면(5~10) 깜빡이는 노이즈가 사라짐

# 3. 🔒 락온 (Lock-on) 로직
LOCK_FRAME_COUNT = 45           # (기본 30) 중앙에 몇 프레임(약 1초) 유지해야 락온 걸릴지
SIMILARITY_THRESHOLD = 0.5      # (기본 0.5) 옷 색깔 유사도 기준 (낮을수록 너그럽게 인정)

# 4. 📷 하드웨어 설정
USB_CAM_ID = 0                  # 카메라 번호 (0 또는 1)
SEND_IMG_QUALITY = 50           # (1~100) 웹 송출 화질 (높을수록 좋지만 느려짐)

# 5. 📡 통신 포트
PORT_DATA = 5555                # JSON 데이터 포트
PORT_VIDEO = 5556               # 영상 송출 포트

# ====================================================================
# (아래부터는 로직 코드입니다. 건드리지 않으셔도 됩니다)
# ====================================================================

# ZMQ 초기화
context = zmq.Context()
socket_data = context.socket(zmq.PUB)
socket_data.bind(f"tcp://*:{PORT_DATA}")
socket_video = context.socket(zmq.PUB)
socket_video.bind(f"tcp://*:{PORT_VIDEO}")

print(f"📡 비전 노드 시작! (Data: {PORT_DATA}, Video: {PORT_VIDEO})")

# 모델 로드
if torch.cuda.is_available():
    print(f"🚀 CUDA 감지됨! GPU({torch.cuda.get_device_name(0)}) 사용")
else:
    print("🚨 CUDA 감지 실패! CPU 모드 (느림)")

model = YOLO(MODEL_FILE, task='detect')

# DeepSORT 설정 (위의 CONFIG 변수 적용)
tracker = DeepSort(
    max_age=TRACK_MAX_AGE,
    n_init=TRACK_N_INIT,
    embedder='mobilenet',
    embedder_gpu=True,
    nms_max_overlap=1.0
)

# GStreamer 파이프라인 (GPU 가속 최적화)
def gstreamer_pipeline(sensor_id=0, capture_width=640, capture_height=480, framerate=30):
    return (
        "v4l2src device=/dev/video%d ! "
        "image/jpeg, width=(int)%d, height=(int)%d, framerate=(fraction)%d/1 ! "
        "nvv4l2decoder mjpeg=1 ! "
        "nvvidconv ! "
        "video/x-raw, format=(string)BGRx ! "
        "appsink drop=1 sync=0"
        % (sensor_id, capture_width, capture_height, framerate)
    )

# OpenCV GStreamer 지원 여부 확인
def check_gstreamer_support():
    build_info = cv2.getBuildInformation()
    return "GStreamer:                   YES" in build_info

if check_gstreamer_support():
    cap = cv2.VideoCapture(gstreamer_pipeline(sensor_id=USB_CAM_ID), cv2.CAP_GSTREAMER)
    if cap.isOpened():
        print("✅ GStreamer 파이프라인 성공 (GPU 가속)")
    else:
        print("🚨 GStreamer 파이프라인 실패 -> V4L2 전환")
        cap = cv2.VideoCapture(USB_CAM_ID, cv2.CAP_V4L2)
else:
    print("⚠️ OpenCV에 GStreamer 미지원 -> V4L2 사용")
    cap = cv2.VideoCapture(USB_CAM_ID, cv2.CAP_V4L2)

if not cap.isOpened():
    print("❌ 카메라 열기 실패!")
    exit(1)

# V4L2 설정 (MJPEG 우선 시도)
if cap.getBackendName() == "V4L2":
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 30)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # 지연 최소화
    print(f"📷 V4L2 설정: {int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))}x{int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))} @ {cap.get(cv2.CAP_PROP_FPS)}fps")

# 변수 초기화
target_hist = None
original_target_id = None   # 최초 락온 시 ID (화면 표시용, 변경 안됨)
current_track_id = None     # 현재 추적 중인 DeepSORT ID (재식별 시 변경됨)
is_locked = False
lock_counter = 0
last_print_time = time.time()

def get_color_histogram(img_crop):
    if img_crop is None or img_crop.size == 0: return None
    try:
        hsv = cv2.cvtColor(img_crop, cv2.COLOR_BGR2HSV)
        # bin 수 축소로 연산량 감소 (180,256 -> 30,32)
        hist = cv2.calcHist([hsv], [0, 1], None, [30, 32], [0, 180, 0, 256])
        cv2.normalize(hist, hist, 0, 1, cv2.NORM_MINMAX)
        return hist
    except Exception: return None

print("🎥 [튜닝 모드] 영상 처리 시작...")

while True:
    success, frame = cap.read()
    if not success:
        time.sleep(0.001)
        continue

    # BGRx(4채널) -> BGR(3채널) 변환 (numpy slicing이 cvtColor보다 빠름)
    if frame.shape[2] == 4:
        frame = frame[:, :, :3]

    height, width, _ = frame.shape
    center_x, center_y = width // 2, height // 2

    # ========== [1단계] YOLO 추론 ==========
    # 매 프레임마다 사람(class 0)을 탐지
    # half=True: FP16으로 GPU 메모리 절약 & 속도 향상
    results = model(frame, device=0, half=True, classes=[0], verbose=False)

    # YOLO 결과 -> DeepSORT 입력 포맷으로 변환
    # DeepSORT는 [x, y, w, h] 형식을 요구함 (xyxy가 아님)
    detections = []
    for result in results:
        for box in result.boxes:
            conf = float(box.conf[0].cpu().numpy())
            if conf > CONF_THRESHOLD:
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                detections.append(([x1, y1, x2-x1, y2-y1], conf, 0))

    # ========== [2단계] DeepSORT 추적 ==========
    # 칼만 필터로 위치 예측 + 헝가리안 알고리즘으로 ID 매칭
    # 같은 사람이면 동일 track_id 유지
    tracks = tracker.update_tracks(detections, frame=frame)

    # ========== [3단계] 타겟 매칭 로직 ==========
    best_match_track = None
    best_match_box = None
    found_person_in_center = False

    send_data = {"status": "SEARCHING", "cx": 320}

    for track in tracks:
        # is_confirmed(): n_init 프레임 연속 탐지되어야 True
        # 깜빡이는 오탐지 필터링 역할
        if not track.is_confirmed(): continue

        # ltrb = [left, top, right, bottom] 좌표
        ltrb = track.to_ltrb()
        x1, y1, x2, y2 = map(int, ltrb)

        # 바운딩 박스가 화면 밖으로 나가지 않도록 클램핑
        x1 = max(0, min(x1, width - 1))
        y1 = max(0, min(y1, height - 1))
        x2 = max(0, min(x2, width - 1))
        y2 = max(0, min(y2, height - 1))

        if x2 <= x1 or y2 <= y1: continue

        # 사람 영역 잘라서 색상 히스토그램 추출 (재식별용)
        person_crop = frame[y1:y2, x1:x2]
        current_hist = get_color_histogram(person_crop)
        if current_hist is None: continue

        # -------- [모드 A] 락온 대기 상태 --------
        # 화면 중앙에 사람이 일정 시간 머물면 락온
        if not is_locked:
            # 바운딩 박스가 화면 중앙점을 포함하는지 체크
            if (x1 < center_x < x2) and (y1 < center_y < y2):
                found_person_in_center = True

                # 노란 박스 + 진행률 바 표시
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 255), 3)
                progress = lock_counter / LOCK_FRAME_COUNT
                bar_w = int((x2 - x1) * progress)
                cv2.rectangle(frame, (x1, y1-20), (x1 + bar_w, y1-10), (0, 255, 255), -1)

                # 카운터가 차면 락온 확정
                if lock_counter >= LOCK_FRAME_COUNT:
                    target_hist = current_hist          # 타겟 색상 저장
                    original_target_id = track.track_id # 화면 표시용 ID (고정)
                    current_track_id = track.track_id   # 실제 추적용 ID (재식별 시 변경됨)
                    is_locked = True
                    print(f"\n✅ 락온 완료! Target ID: {original_target_id}")

        # -------- [모드 B] 락온 후 추적 상태 --------
        else:
            is_match = False

            # 방법1: DeepSORT ID가 같으면 바로 매칭 (가장 신뢰도 높음)
            if track.track_id == current_track_id:
                is_match = True
                # 타겟 히스토그램을 서서히 업데이트 (조명 변화 대응)
                cv2.accumulateWeighted(current_hist, target_hist, 0.1)
                cv2.normalize(target_hist, target_hist, 0, 1, cv2.NORM_MINMAX)

            # 방법2: ID가 다르면 색상 유사도로 재식별 시도
            # (DeepSORT가 ID를 잃어버렸을 때 복구용)
            else:
                similarity = cv2.compareHist(target_hist, current_hist, cv2.HISTCMP_CORREL)
                if similarity > SIMILARITY_THRESHOLD:
                    is_match = True
                    current_track_id = track.track_id  # 새 ID로 갱신
                    print(f"🔄 재식별 성공! (원본 ID:{original_target_id} 유지, DeepSORT ID:{current_track_id})")

            if is_match:
                best_match_track = track
                best_match_box = (x1, y1, x2, y2)
                break  # 첫 매칭에서 종료 

    # ========== [4단계] 상태별 처리 & 조향값 계산 ==========

    # --- 락온 전: 카운터 관리 ---
    if not is_locked:
        if found_person_in_center:
            lock_counter += 1
        else:
            lock_counter = max(0, lock_counter - 2)  # 벗어나면 빠르게 감소

        cv2.putText(frame, f"LOCK: {lock_counter}/{LOCK_FRAME_COUNT}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        cv2.circle(frame, (center_x, center_y), 5, (0, 0, 255), -1)

    # --- 락온 성공 + 타겟 발견 ---
    if is_locked and best_match_track:
        bx1, by1, bx2, by2 = best_match_box
        target_cx = (bx1 + bx2) / 2  # 타겟 중심 x좌표

        # 조향값 계산: 화면 중앙 기준 -34 ~ +34 범위로 정규화
        # 타겟이 왼쪽이면 음수(좌회전), 오른쪽이면 양수(우회전)
        steer_val = (target_cx - center_x) / (width / 2) * 34
        steer_val = max(-34, min(34, steer_val))

        send_data["status"] = "LOCKED"
        send_data["cx"] = float(steer_val)

        # 초록 박스로 타겟 표시
        cv2.rectangle(frame, (bx1, by1), (bx2, by2), (0, 255, 0), 3)
        cv2.putText(frame, f"ID:{original_target_id}", (bx1, by1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

    # --- 락온 상태인데 타겟을 못 찾음 ---
    elif is_locked and not best_match_track:
        send_data["status"] = "LOST"
        cv2.putText(frame, "LOST TARGET!", (50, 240),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 255), 3)

    # ZMQ로 상태 전송 (컨트롤러가 수신)
    socket_data.send_json(send_data)

    # ========== [5단계] 영상 송출 ==========
    ret, buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), SEND_IMG_QUALITY])
    if ret:
        socket_video.send(buffer.tobytes())

    # 로그
    if time.time() - last_print_time > 1.0:
        if is_locked:
            status_msg = f"🔒 LOCKED (ID:{original_target_id}) - Steer:{int(send_data['cx'])}"
        else:
            status_msg = f"👀 SEARCHING... ({lock_counter}/{LOCK_FRAME_COUNT})"
        
        print(f"[RUNNING] {status_msg}")
        last_print_time = time.time()