# YDLidar Cartographer SLAM (slam_mapping2)

YDLidar X4-Pro와 ROS2 Cartographer를 사용한 2D SLAM 시스템입니다.

## 패키지 구조

```
slam_mapping2/
├── slam_mapping2/          # Python 노드
│   ├── ydlidar_node.py     # YDLidar 드라이버
│   └── odom_publisher.py   # 가상 오도메트리 (테스트용)
├── config/
│   └── ydlidar_2d.lua      # Cartographer 설정
├── launch/
│   ├── slam_mapping.launch.py   # SLAM 실행
│   └── save_map.launch.py       # 맵 저장
├── rviz/
│   └── slam.rviz           # RViz 설정
├── urdf/
│   └── robot.urdf          # 로봇 모델
├── maps/                   # 저장된 맵
└── scripts/                # 테스트 스크립트
    ├── test_slam.sh        # ROS2 SLAM 테스트
    ├── test_standalone.py  # 독립 실행 테스트
    ├── create_slam_map.sh  # SLAM 맵 생성 (권장)
    ├── save_map.sh         # 맵 저장
    └── build.sh            # 패키지 빌드
```

---

## 설치

### 1. 프로젝트 클론

```bash
# 어디든 원하는 위치에 클론 가능
cd ~
git clone <your-repo-url> slam_mapping2
cd slam_mapping2
```

### 2. 필수 패키지

```bash
# Cartographer
sudo apt install ros-humble-cartographer ros-humble-cartographer-ros

# Map Server
sudo apt install ros-humble-nav2-map-server

# RViz
sudo apt install ros-humble-rviz2

# CycloneDDS (선택사항, 더 안정적)
sudo apt install ros-humble-rmw-cyclonedds-cpp

# Python 패키지
pip3 install numpy matplotlib pillow
```

### 3. YDLidar SDK 설치

```bash
# 반드시 홈 디렉토리에 설치
cd ~
git clone https://github.com/YDLIDAR/YDLidar-SDK.git
cd YDLidar-SDK/build
cmake ..
make
sudo make install
```

### 4. USB 권한 설정

```bash
# 영구 권한 (권장)
sudo usermod -aG dialout $USER
# 로그아웃 후 다시 로그인

# 또는 임시 권한
sudo chmod 666 /dev/ttyUSB0
```

**참고**: 이제 프로젝트는 어떤 사용자 환경에서도 작동합니다. 경로가 자동으로 감지됩니다!

---

## 사용법

### 방법 1: SLAM 맵 생성 (권장)

```bash
# 1. SLAM 실행 (RViz 포함)
./scripts/create_slam_map.sh /dev/ttyUSB0

# 2. LiDAR를 손에 들고 방 안을 돌아다님
#    RViz에서 실시간으로 맵이 그려지는 것 확인

# 3. 맵 저장 (다른 터미널에서)
./scripts/save_map.sh my_map
```

### 방법 2: ROS2 Cartographer SLAM

```bash
# 1. SLAM 실행 (RViz 포함)
./scripts/test_slam.sh

# 2. LiDAR를 손에 들고 방 안을 돌아다님
#    RViz에서 실시간으로 맵이 그려지는 것 확인

# 3. 맵 저장 (다른 터미널에서)
./scripts/save_map.sh my_map
```

### 방법 3: 독립 실행 테스트 (ROS2 빌드 없이)

```bash
# ROS2 없이 바로 테스트
python3 ~/slam_mapping2/scripts/test_standalone.py --port /dev/ttyUSB0

# matplotlib 창에서 맵 생성 확인
# Ctrl+C로 종료 시 맵 자동 저장
```

---

## 테스트 흐름

```
┌─────────────────────────────────────────────────────────┐
│                    노트북 테스트                          │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  [YDLidar X4-Pro] ──USB──▶ [노트북]                     │
│                              │                          │
│                              ▼                          │
│                    ┌─────────────────┐                  │
│                    │ test_slam.sh    │                  │
│                    │ 또는            │                  │
│                    │ test_standalone │                  │
│                    └────────┬────────┘                  │
│                              │                          │
│                              ▼                          │
│                    ┌─────────────────┐                  │
│                    │  RViz / Plot    │                  │
│                    │  실시간 맵 표시  │                  │
│                    └────────┬────────┘                  │
│                              │                          │
│                              ▼                          │
│                    ┌─────────────────┐                  │
│                    │  맵 저장        │                  │
│                    │  .pgm + .yaml   │                  │
│                    └─────────────────┘                  │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## 저장된 맵 파일

```
maps/
├── my_map.pgm      # 맵 이미지 (흑백)
└── my_map.yaml     # 메타데이터 (해상도, 원점)
```

### YAML 형식

```yaml
image: my_map.pgm
resolution: 0.05        # 5cm per pixel
origin: [0.0, 0.0, 0.0] # 맵 원점 [x, y, yaw]
negate: 0
occupied_thresh: 0.65   # 장애물 판정 임계값
free_thresh: 0.196      # 자유공간 판정 임계값
```

---

## 문제 해결

### LiDAR 연결 안됨

```bash
# 포트 확인
ls /dev/ttyUSB*

# 권한 설정
sudo chmod 666 /dev/ttyUSB0

# 또는 영구 설정
sudo usermod -aG dialout $USER
```

### Cartographer 오류

```bash
# 패키지 재설치
sudo apt install --reinstall ros-humble-cartographer-ros
```

---

## 참고

- omo_r1mini 패키지 구조 참고 (GMapping → Cartographer로 변경)
- YDLidar SDK: `/home/seonil/YDLidar-SDK`
