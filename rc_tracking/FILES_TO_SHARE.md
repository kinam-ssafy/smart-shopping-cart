# 새로운 환경에 공유할 파일 목록

> **RC Tracking System을 다른 사용자/환경에 전달할 때 필요한 모든 파일**

---

## ✅ 필수 공유 파일

### 1. 실행 스크립트
```
run_full_system.sh          # 메인 실행 스크립트
```

### 2. YOLO 모델 파일
```
yolo26s.pt                  # 20MB, 정확도 높음 (권장)
yolo26n.pt                  # 5.5MB, 속도 빠름 (대안)
```

### 3. Python 의존성
```
requirements.txt            # pip install -r requirements.txt
```

### 4. ROS 2 패키지 전체 (`src/rc_detection/`)
```
src/rc_detection/
├── package.xml             # ROS2 패키지 메타데이터
├── setup.py                # Python 패키지 설정
├── CMakeLists.txt          # 빌드 설정
│
├── msg/                    # 커스텀 메시지 정의
│   ├── Detection.msg
│   └── DetectionArray.msg
│
├── resource/               # ROS2 리소스
│   └── rc_detection        # (빈 파일 또는 마커)
│
└── rc_detection/           # Python 노드 코드
    ├── __init__.py
    ├── webcam_publisher.py         ⭐ 필수
    ├── yolo_deepsort_node.py       ⭐ 필수
    └── distance_lidar_node.py      ⭐ 필수
```

### 5. 문서 파일
```
INSTALLATION_GUIDE.md       # 설치 가이드 (이 파일)
FILES_TO_SHARE.md           # 공유 파일 목록 (이 파일)
README.md                   # 프로젝트 개요 (선택)
```

---

## 📦 공유 패키지 생성 방법

### Option 1: ZIP 아카이브
```bash
cd ~/rc_tracking
tar -czf rc_tracking_system.tar.gz \
    run_full_system.sh \
    yolo26s.pt \
    requirements.txt \
    INSTALLATION_GUIDE.md \
    FILES_TO_SHARE.md \
    src/rc_detection/
```

### Option 2: Git 저장소
```bash
cd ~/rc_tracking
git init
git add run_full_system.sh requirements.txt src/
git add *.md

# .gitignore 설정 (불필요한 파일 제외)
cat > .gitignore << 'EOF'
build/
install/
log/
*.pyc
__pycache__/
.vscode/
*.log
*.pt  # 모델 파일은 별도 다운로드 권장
EOF

git commit -m "Initial commit: RC Tracking System"
```

---

## 🗂️ 전체 파일 체크리스트

### 루트 디렉토리
- [x] `run_full_system.sh` (실행 스크립트)
- [x] `yolo26s.pt` 또는 `yolo26n.pt` (YOLO 모델)
- [x] `requirements.txt` (Python 의존성)
- [x] `INSTALLATION_GUIDE.md` (설치 가이드)
- [x] `FILES_TO_SHARE.md` (이 파일)

### src/rc_detection/
- [x] `package.xml`
- [x] `setup.py`
- [x] `CMakeLists.txt`

### src/rc_detection/msg/
- [x] `Detection.msg`
- [x] `DetectionArray.msg`

### src/rc_detection/resource/
- [x] `rc_detection` (빈 파일 또는 마커)

### src/rc_detection/rc_detection/
- [x] `__init__.py`
- [x] `webcam_publisher.py` (156줄)
- [x] `yolo_deepsort_node.py` (295줄)
- [x] `distance_lidar_node.py` (404줄) ⭐ **매우 중요!**

---

## ⚠️ 공유하지 않아도 되는 파일

이 파일들은 빌드 시 자동 생성되므로 공유 불필요:

```
build/                      # colcon build 출력
install/                    # 설치된 패키지
log/                        # 빌드 로그
__pycache__/                # Python 캐시
*.pyc                       # Python 바이트코드
.vscode/                    # IDE 설정
/tmp/*.log                  # 실행 로그
```

---

## 📋 수신자가 해야 할 작업

공유받은 파일을 실행하려면:

### 1. 파일 압축 해제
```bash
cd ~
tar -xzf rc_tracking_system.tar.gz
cd rc_tracking
```

### 2. 시스템 환경 설정
**INSTALLATION_GUIDE.md를 따라 진행:**
- ROS 2 Humble 설치
- YDLiDAR SDK 설치 (Python 바인딩 포함)
- Python 패키지 설치 (`pip3 install -r requirements.txt`)

### 3. 프로젝트 빌드
```bash
cd ~/rc_tracking
colcon build --symlink-install
source install/setup.bash
```

### 4. 하드웨어 연결
- 웹캠 → USB
- YDLiDAR S2PRO → USB (권한 설정 필요)

### 5. 실행
```bash
./run_full_system.sh
```

---

## 🔍 핵심 파일 설명

### distance_lidar_node.py (404줄) ⭐
**역할:** YDLiDAR S2PRO에서 거리 데이터를 읽어 YOLO 추적 객체와 융합

**주요 기능:**
- YDLiDAR Python SDK 직접 사용 (`import ydlidar`)
- `/detections` 구독 → YOLO 추적 결과 수신
- 픽셀 좌표 → 각도 → LiDAR 인덱스 매핑
- ±10° 범위 내 거리 평균 계산
- `/closest_object_id` 발행

**의존성:**
- `ydlidar` Python 모듈 (YDLiDAR SDK 필수)
- `rc_detection.msg.DetectionArray` (커스텀 메시지)
- ROS 2 `rclpy`

### yolo_deepsort_node.py (295줄)
**역할:** YOLO 객체 감지 + DeepSORT 추적

**주요 기능:**
- `/camera/image_raw` 구독 → 웹캠 영상 수신
- YOLO 추론 (yolo26s.pt 사용)
- DeepSORT 추적 ID 할당
- `/detections` 발행 → distance_lidar_node로 전송
- OpenCV 창에 시각화 (빨간색=가장 가까운 객체, 초록색=기타)

**의존성:**
- `ultralytics` (YOLO)
- `deep-sort-realtime` (DeepSORT)
- `cv_bridge` (ROS-OpenCV 변환)

### webcam_publisher.py (156줄)
**역할:** 웹캠 영상을 ROS 2 토픽으로 퍼블리시

**주요 기능:**
- OpenCV로 웹캠 캡처
- `/camera/image_raw` 토픽 발행
- 30 FPS 목표

**의존성:**
- `cv2` (OpenCV)
- `cv_bridge`

---

## 📊 파일 크기 예상치

```
전체 패키지 크기: ~25-30 MB

├── yolo26s.pt              20 MB
├── Python 노드 (3개)       ~50 KB
├── 메시지 정의             ~1 KB
├── 설정 파일               ~10 KB
└── 문서                    ~20 KB
```

---

## 🚀 빠른 공유 명령어

```bash
cd ~/rc_tracking

# 필수 파일만 압축
tar -czf rc_tracking_minimal.tar.gz \
    --exclude='*.pt' \
    --exclude='build' \
    --exclude='install' \
    --exclude='log' \
    run_full_system.sh \
    requirements.txt \
    *.md \
    src/rc_detection/

# YOLO 모델 포함 (전체 패키지)
tar -czf rc_tracking_full.tar.gz \
    --exclude='build' \
    --exclude='install' \
    --exclude='log' \
    run_full_system.sh \
    yolo26s.pt \
    requirements.txt \
    *.md \
    src/rc_detection/

echo "✅ 패키지 생성 완료!"
ls -lh rc_tracking_*.tar.gz
```

---

## 📝 체크리스트 (공유 전 확인)

- [ ] `run_full_system.sh` 실행 권한 확인 (`chmod +x`)
- [ ] `yolo26s.pt` 파일 존재 확인 (또는 다운로드 링크 제공)
- [ ] `requirements.txt` 최신 버전 확인
- [ ] `distance_lidar_node.py`에 하드코딩된 경로 없는지 확인
- [ ] `INSTALLATION_GUIDE.md` 최신 정보 반영
- [ ] 모든 Python 노드에 실행 권한 있는지 확인
- [ ] 메시지 파일 (.msg) 포함 여부 확인

---

**중요:** `distance_lidar_node.py` 없이는 LiDAR 거리 측정이 불가능합니다!  
이 파일은 YDLiDAR Python SDK를 직접 사용하여 센서 데이터를 읽는 핵심 노드입니다.
