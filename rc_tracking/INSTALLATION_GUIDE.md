# RC Tracking System - 설치 및 실행 가이드

> **YDLiDAR S2PRO + YOLO + DeepSORT 기반 실시간 객체 추적 및 거리 측정 시스템**  
> 작성일: 2026년 1월 23일

---

## 📋 목차

1. [시스템 요구사항](#1-시스템-요구사항)
2. [사전 준비](#2-사전-준비)
3. [ROS 2 Humble 설치](#3-ros-2-humble-설치)
4. [YDLiDAR SDK 설치](#4-ydlidar-sdk-설치)
5. [Python 패키지 설치](#5-python-패키지-설치)
6. [프로젝트 설정](#6-프로젝트-설정)
7. [빌드 및 실행](#7-빌드-및-실행)
8. [트러블슈팅](#8-트러블슈팅)

---

## 1. 시스템 요구사항

### 운영체제
- **Ubuntu 22.04 LTS** (권장)
- **ROS 2 Humble Hawksbill**

### 하드웨어
- **웹캠** (USB 카메라, /dev/video0 이상)
- **YDLiDAR S2PRO** 센서 (/dev/ttyUSB0)
- **USB 포트** 2개 이상
- **GPU** (선택사항, CUDA 지원 시 YOLO 속도 향상)

### 최소 사양
- RAM: 4GB 이상
- 디스크: 10GB 이상 여유 공간

---

## 2. 사전 준비

### 2.1 시스템 업데이트
```bash
sudo apt update
sudo apt upgrade -y
```

### 2.2 기본 도구 설치
```bash
sudo apt install -y \
    software-properties-common \
    curl \
    wget \
    git \
    build-essential \
    cmake \
    python3-pip \
    python3-dev \
    python3-setuptools
```

---

## 3. ROS 2 Humble 설치

### 3.1 Locale 설정
```bash
sudo apt update && sudo apt install locales
sudo locale-gen en_US en_US.UTF-8
sudo update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8
export LANG=en_US.UTF-8
```

### 3.2 ROS 2 Repository 추가
```bash
sudo apt install software-properties-common
sudo add-apt-repository universe

sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key \
    -o /usr/share/keyrings/ros-archive-keyring.gpg

echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu $(. /etc/os-release && echo $UBUNTU_CODENAME) main" | \
    sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null
```

### 3.3 ROS 2 패키지 설치
```bash
sudo apt update
sudo apt install -y ros-humble-desktop
sudo apt install -y ros-dev-tools
```

### 3.4 환경 설정
```bash
echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc
source ~/.bashrc
```

### 3.5 ROS 2 의존성 설치
```bash
sudo apt install -y \
    ros-humble-rclpy \
    ros-humble-cv-bridge \
    ros-humble-sensor-msgs \
    ros-humble-std-msgs \
    ros-humble-geometry-msgs \
    python3-colcon-common-extensions
```

---

## 4. YDLiDAR SDK 설치

⚠️ **매우 중요!** 이 단계 없이는 LiDAR 노드가 실행되지 않습니다.

### 4.1 SDK 다운로드 및 빌드
```bash
cd ~/Downloads
git clone https://github.com/YDLIDAR/YDLidar-SDK.git
cd YDLidar-SDK

mkdir build && cd build
cmake ..
make
sudo make install
```

### 4.2 Python 바인딩 설치
```bash
cd ~/Downloads/YDLidar-SDK/python
sudo python3 setup.py install
```

### 4.3 설치 확인
```bash
python3 -c "import ydlidar; print('✅ YDLiDAR SDK 설치 성공')"
```

### 4.4 USB 권한 설정
```bash
# udev 규칙 생성
echo 'KERNEL=="ttyUSB*", MODE="0666"' | sudo tee /etc/udev/rules.d/99-ydlidar.rules

# 규칙 적용
sudo udevadm control --reload-rules
sudo udevadm trigger

# 확인 (LiDAR 연결 후)
ls -l /dev/ttyUSB0
# 출력 예: crw-rw-rw- 1 root dialout ... /dev/ttyUSB0
```

⚠️ **권한 설정 후 시스템 재부팅 권장**

---

## 5. Python 패키지 설치

### 5.1 requirements.txt 확인
프로젝트의 `requirements.txt` 파일:
```
ultralytics>=8.0.0
torch>=2.0.0
torchvision>=0.15.0
deep-sort-realtime>=1.3.2
opencv-python>=4.8.0
opencv-contrib-python>=4.8.0
numpy>=1.24.0
scipy>=1.10.0
pyyaml>=6.0
```

### 5.2 패키지 설치
```bash
cd ~/rc_tracking
pip3 install -r requirements.txt
```

또는 수동 설치:
```bash
pip3 install ultralytics torch torchvision deep-sort-realtime \
    opencv-python opencv-contrib-python numpy scipy pyyaml
```

### 5.3 설치 확인
```bash
python3 << 'EOF'
import ydlidar
import ultralytics
import cv2
from deep_sort_realtime.deepsort_tracker import DeepSort
print("✅ 모든 Python 패키지 설치 완료")
EOF
```

---

## 6. 프로젝트 설정

### 6.1 프로젝트 구조
전체 파일 구조는 다음과 같아야 합니다:
```
~/rc_tracking/
├── run_full_system.sh          # 메인 실행 스크립트
├── yolo26s.pt                  # YOLO 모델 (20MB)
├── requirements.txt            # Python 의존성
│
└── src/
    └── rc_detection/
        ├── package.xml         # ROS2 패키지 메타데이터
        ├── setup.py            # Python 패키지 설정
        ├── CMakeLists.txt      # 빌드 설정
        │
        ├── msg/
        │   ├── Detection.msg
        │   └── DetectionArray.msg
        │
        ├── resource/
        │   └── rc_detection    # (빈 파일)
        │
        └── rc_detection/
            ├── __init__.py
            ├── webcam_publisher.py
            ├── yolo_deepsort_node.py
            └── distance_lidar_node.py
```

### 6.2 YOLO 모델 다운로드
```bash
cd ~/rc_tracking

# Option 1: YOLOv11 nano 모델 (5.5MB, 빠름)
wget https://github.com/ultralytics/assets/releases/download/v8.3.0/yolo11n.pt \
    -O yolo26n.pt

# Option 2: YOLOv11 small 모델 (20MB, 정확함)
wget https://github.com/ultralytics/assets/releases/download/v8.3.0/yolo11s.pt \
    -O yolo26s.pt
```

### 6.3 실행 권한 부여
```bash
chmod +x ~/rc_tracking/run_full_system.sh
```

---

## 7. 빌드 및 실행

### 7.1 프로젝트 빌드
```bash
cd ~/rc_tracking
colcon build --symlink-install
```

빌드 성공 메시지 예:
```
Summary: 1 package finished [5.23s]
```

### 7.2 환경 소싱
```bash
source install/setup.bash
```

### 7.3 하드웨어 연결 확인
```bash
# 웹캠 확인
ls /dev/video*
v4l2-ctl --list-devices

# LiDAR 확인
ls -l /dev/ttyUSB*
# 예상 출력: crw-rw-rw- 1 root dialout ... /dev/ttyUSB0
```

### 7.4 시스템 실행
```bash
cd ~/rc_tracking
source install/setup.bash
./run_full_system.sh
```

### 7.5 실행 순서
스크립트는 다음 순서로 노드를 실행합니다:

1. **웹캠 노드** (3초 대기)
   - `/camera/image_raw` 토픽 발행
   
2. **YOLO + DeepSORT 노드** (5초 대기)
   - `/detections` 토픽 발행
   - OpenCV 창에 추적 결과 표시
   
3. **Distance LiDAR 노드**
   - `/closest_object_id` 토픽 발행
   - 터미널에 거리 정보 출력

### 7.6 실행 확인
새 터미널에서:
```bash
# 토픽 확인
ros2 topic list
# 출력 예:
# /camera/image_raw
# /detections
# /closest_object_id

# 실시간 모니터링
tail -f /tmp/distance.log | grep -E "Track|LiDAR"
```

---

## 8. 트러블슈팅

### 8.1 YDLiDAR 관련

#### 문제: `ModuleNotFoundError: No module named 'ydlidar'`
**해결:**
```bash
cd ~/Downloads/YDLidar-SDK/python
sudo python3 setup.py install
python3 -c "import ydlidar; print('OK')"
```

#### 문제: `Failed to open lidar port /dev/ttyUSB0`
**해결:**
```bash
# 권한 확인
ls -l /dev/ttyUSB0

# 권한 없으면
sudo chmod 666 /dev/ttyUSB0

# 영구 해결
echo 'KERNEL=="ttyUSB*", MODE="0666"' | sudo tee /etc/udev/rules.d/99-ydlidar.rules
sudo udevadm control --reload-rules
```

#### 문제: LiDAR 회전하지만 데이터 없음
**해결:** `distance_lidar_node.py`에서 포트 설정 확인
```python
self.laser.setlidaropt(ydlidar.LidarPropSerialPort, "/dev/ttyUSB0")
```

### 8.2 YOLO 관련

#### 문제: `FileNotFoundError: yolo26s.pt not found`
**해결:**
```bash
cd ~/rc_tracking
ls -la *.pt  # 모델 파일 확인

# 없으면 다운로드
wget https://github.com/ultralytics/assets/releases/download/v8.3.0/yolo11s.pt \
    -O yolo26s.pt
```

#### 문제: YOLO 실행 시 `CUDA out of memory`
**해결:** `yolo_deepsort_node.py`에서 device 변경
```python
# GPU 대신 CPU 사용
self.model = YOLO(args.model_path)
results = self.model(frame, device='cpu')
```

### 8.3 ROS 2 관련

#### 문제: `package 'rc_detection' not found`
**해결:**
```bash
cd ~/rc_tracking
colcon build --symlink-install
source install/setup.bash
ros2 pkg list | grep rc_detection
```

#### 문제: `No module named 'rc_detection.msg'`
**해결:** 메시지 파일 빌드 확인
```bash
cd ~/rc_tracking
colcon build --packages-select rc_detection
source install/setup.bash
```

### 8.4 카메라 관련

#### 문제: `Failed to open camera`
**해결:**
```bash
# 카메라 장치 확인
v4l2-ctl --list-devices

# webcam_publisher.py에서 카메라 인덱스 변경
self.cap = cv2.VideoCapture(0)  # 0, 1, 2 등 시도
```

### 8.5 로그 확인

각 노드의 로그 위치:
```bash
tail -f /tmp/webcam.log    # 웹캠 노드
tail -f /tmp/yolo.log      # YOLO 노드
tail -f /tmp/distance.log  # LiDAR 노드
```

---

## 9. 시스템 종료

```bash
# 전체 시스템 종료
pkill -9 -f "webcam_publisher|yolo_deepsort|distance_lidar"

# 또는 각 프로세스 개별 종료
kill -9 $WEBCAM_PID
kill -9 $YOLO_PID
kill -9 $DISTANCE_PID
```

---

## 10. 추가 정보

### ROS 2 토픽 구조
```
webcam_publisher → /camera/image_raw → yolo_deepsort_node
                                              ↓
                                        /detections
                                              ↓
                                   distance_lidar_node
                                              ↓
                                     /closest_object_id
```

### 메시지 타입
- `/camera/image_raw`: `sensor_msgs/Image`
- `/detections`: `rc_detection/DetectionArray`
- `/closest_object_id`: `std_msgs/Int32`

### 시스템 성능
- YOLO 추론: ~30-60 FPS (GPU), ~10-15 FPS (CPU)
- LiDAR 스캔: 6 Hz (S2PRO 기본 설정)
- 거리 측정 정확도: ±2cm (0.1-10m 범위)

---

## 11. 참고 자료

- **ROS 2 Humble 문서**: https://docs.ros.org/en/humble/
- **Ultralytics YOLO**: https://docs.ultralytics.com/
- **YDLiDAR SDK**: https://github.com/YDLIDAR/YDLidar-SDK
- **DeepSORT**: https://github.com/levan92/deep_sort_realtime

---

**문의 및 버그 리포트:** GitHub Issues 또는 이메일로 연락 주세요.
