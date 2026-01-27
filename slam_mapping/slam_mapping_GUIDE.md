# SLAM Mapping System - 설치 및 실행 가이드

YDLidar X4-Pro와 ROS2 Cartographer를 사용한 2D SLAM 시스템입니다.
Jetson Nano 보드 및 일반 Ubuntu 환경에서 실행 가능합니다.

---

## 📋 시스템 요구사항

### 하드웨어
- **LiDAR**: YDLidar X4-Pro
- **컴퓨팅 보드**: Jetson Nano 또는 Ubuntu 22.04 PC
- **USB 포트**: LiDAR 연결용

### 소프트웨어
- **OS**: Ubuntu 22.04 (Jammy)
- **ROS**: ROS2 Humble
- **Python**: 3.10+

---

## 🚀 설치 가이드

### 1. 프로젝트 클론

```bash
cd ~
git clone <repository-url> S14P11A401
cd S14P11A401
git checkout mapping
cd slam_mapping
```

### 2. ROS2 Humble 설치

```bash
# ROS2 Humble 설치 (아직 설치 안 된 경우)
sudo apt update
sudo apt install software-properties-common
sudo add-apt-repository universe
sudo apt update && sudo apt install curl -y
sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key -o /usr/share/keyrings/ros-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu $(. /etc/os-release && echo $UBUNTU_CODENAME) main" | sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null

sudo apt update
sudo apt install ros-humble-desktop
```

### 3. 필수 ROS2 패키지 설치

```bash
# Cartographer SLAM
sudo apt install -y ros-humble-cartographer ros-humble-cartographer-ros

# Map Server
sudo apt install -y ros-humble-nav2-map-server

# RViz (시각화 - Jetson Nano에서는 선택사항)
sudo apt install -y ros-humble-rviz2

# CycloneDDS (더 안정적인 통신)
sudo apt install -y ros-humble-rmw-cyclonedds-cpp
```

### 4. YDLidar SDK 설치

```bash
# 반드시 홈 디렉토리에 설치
cd ~
git clone https://github.com/YDLIDAR/YDLidar-SDK.git
cd YDLidar-SDK/build
cmake ..
make
sudo make install
```

### 5. Python 패키지 설치

```bash
pip3 install numpy matplotlib pillow
```

### 6. USB 권한 설정

```bash
# 영구 권한 설정 (권장)
sudo usermod -aG dialout $USER

# 로그아웃 후 다시 로그인 필요
# 또는 재부팅
```

**임시 권한 (재부팅 시 초기화)**:
```bash
sudo chmod 666 /dev/ttyUSB0
```

---

## 🎮 실행 방법

### 방법 1: SLAM 맵 생성 (권장) ⭐

RC카 또는 로봇에서 실시간으로 맵을 생성합니다.

```bash
cd ~/S14P11A401/slam_mapping

# 1. SLAM 시작 (RViz 포함)
./scripts/create_slam_map.sh /dev/ttyUSB0

# 2. 로봇을 천천히 이동하며 맵 생성
#    - RViz에서 실시간 맵 확인 가능
#    - 같은 장소를 다시 방문하면 루프 클로저 발생

# 3. 다른 터미널에서 맵 저장
./scripts/save_map.sh my_map_name

# 4. 종료
# Ctrl+C
```

**생성된 파일**:
- `maps/my_map_name.pgm` - 맵 이미지
- `maps/my_map_name.yaml` - 맵 메타데이터

### 방법 2: ROS2 Launch 파일 사용

```bash
# 패키지 빌드 필요
./scripts/build.sh
source ~/ros2_ws/install/setup.bash

# SLAM 실행
./scripts/test_slam.sh

# 맵 저장 (다른 터미널)
./scripts/save_map.sh my_map
```

### 방법 3: 독립 실행 테스트 (ROS2 없이)

간단한 테스트용으로 ROS2 빌드 없이 실행 가능합니다.

```bash
python3 scripts/test_standalone.py --port /dev/ttyUSB0

# Matplotlib 창에서 맵 확인
# Ctrl+C로 종료 시 자동 저장
```

---

## 🤖 Jetson Nano 전용 설정

### 디스플레이 없는 환경 (헤드리스)

Jetson Nano가 디스플레이 없이 실행되는 경우:

#### 옵션 1: RViz 비활성화 (권장)

`scripts/create_slam_map.sh` 수정:
```bash
# 74-77줄 주석 처리
# echo "[4/4] Starting RViz..."
# rviz2 -d "$PROJECT_DIR/rviz/slam.rviz" &
# RVIZ_PID=$!
```

#### 옵션 2: 원격 RViz 사용 (윈도우/리눅스 노트북)

**방법 A: WSL2 Ubuntu에서 RViz 실행 (윈도우 사용자 권장)** ⭐

1. **RC카(우분투)에서 설정**:
```bash
# RC카 IP 확인
hostname -I  # 예: 192.168.0.100

# RViz 비활성화 상태로 SLAM 실행
./scripts/create_slam_map.sh /dev/ttyUSB0

# ROS_DOMAIN_ID 확인 (기본값: 0)
echo $ROS_DOMAIN_ID
```

2. **윈도우 노트북에서 WSL2 Ubuntu 설치** (아직 없는 경우):
```powershell
# PowerShell (관리자 권한)
wsl --install -d Ubuntu-22.04
```

3. **WSL2 Ubuntu에서 ROS2 및 RViz 설치**:
```bash
# WSL2 Ubuntu 터미널에서
sudo apt update
sudo apt install software-properties-common
sudo add-apt-repository universe

# ROS2 Humble 설치
sudo apt update && sudo apt install curl -y
sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key -o /usr/share/keyrings/ros-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu $(. /etc/os-release && echo $UBUNTU_CODENAME) main" | sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null

sudo apt update
sudo apt install ros-humble-rviz2 ros-humble-rmw-cyclonedds-cpp

# WSLg X11 지원 확인 (Windows 11 권장)
echo $DISPLAY  # :0 이 나와야 함
```

4. **WSL2에서 RViz 실행**:
```bash
# WSL2 Ubuntu에서
source /opt/ros/humble/setup.bash
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
export ROS_DOMAIN_ID=0

# CycloneDDS 설정 파일 생성 (네트워크 탐색 활성화)
mkdir -p ~/cyclonedds
cat > ~/cyclonedds/config.xml << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<CycloneDDS>
  <Domain>
    <General>
      <NetworkInterfaceAddress>auto</NetworkInterfaceAddress>
      <AllowMulticast>true</AllowMulticast>
    </General>
    <Discovery>
      <ParticipantIndex>auto</ParticipantIndex>
      <EnableTopicDiscoveryEndpoints>true</EnableTopicDiscoveryEndpoints>
    </Discovery>
  </Domain>
</CycloneDDS>
EOF

export CYCLONEDDS_URI=file://$HOME/cyclonedds/config.xml

# RViz 실행 (RC카의 rviz 설정 파일 다운로드 필요)
# 설정 파일이 없으면 기본 RViz 실행
rviz2

# 또는 RC카에서 설정 파일 복사 후
# scp ssafy@192.168.0.100:~/Desktop/seon-il/S14P11A401/slam_mapping/rviz/slam.rviz ~/slam.rviz
# rviz2 -d ~/slam.rviz
```

5. **RViz에서 토픽 확인**:
```bash
# 다른 WSL2 터미널에서 토픽 확인
source /opt/ros/humble/setup.bash
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
export ROS_DOMAIN_ID=0
export CYCLONEDDS_URI=file://$HOME/cyclonedds/config.xml

ros2 topic list
# /scan, /map, /tf, /tf_static 등이 보여야 함
```

**방법 B: SSH 터널링 + rosbridge (포트 8765) - 대체 방법**

네트워크 환경이 복잡한 경우 rosbridge를 사용합니다.

1. **RC카에서 rosbridge 설치 및 실행**:
```bash
# rosbridge 설치
sudo apt install ros-humble-rosbridge-suite

# SLAM 실행 (다른 터미널)
./scripts/create_slam_map.sh /dev/ttyUSB0

# rosbridge 실행
source /opt/ros/humble/setup.bash
ros2 launch rosbridge_server rosbridge_websocket_launch.xml port:=8765
```

2. **윈도우에서 SSH 터널링** (PowerShell):
```powershell
# RC카로 SSH 터널링 (포트 8765)
ssh -L 8765:localhost:8765 ssafy@192.168.0.100

# 연결 유지
```

3. **웹 기반 Visualizer 사용**:
- [ROS3D](http://robotwebtools.org/tools.html) 또는 [Foxglove Studio](https://foxglove.dev/) 사용
- WebSocket 연결: `ws://localhost:8765`

**방법 C: 리눅스 노트북에서 직접 실행**

```bash
# 노트북 (Ubuntu)에서
source /opt/ros/humble/setup.bash
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
export ROS_DOMAIN_ID=0

# CycloneDDS 설정
export CYCLONEDDS_URI=file:///path/to/cyclonedds/config.xml

# RViz 실행
rviz2 -d slam.rviz
```

### 성능 최적화

Jetson Nano의 제한된 리소스를 고려한 설정:

```bash
# CPU 성능 모드 설정
sudo nvpmodel -m 0
sudo jetson_clocks

# 스왑 메모리 증가 (권장)
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

---

## 📁 프로젝트 구조

```
slam_mapping/
├── slam_mapping2/          # Python 노드
│   ├── ydlidar_node.py        # 메인 드라이버
│   ├── ydlidar_simple_node.py # 간소화 버전 (권장)
│   └── odom_publisher.py      # 테스트용 오도메트리
├── config/
│   └── ydlidar_2d.lua         # Cartographer 설정
├── launch/
│   ├── slam_mapping.launch.py # SLAM 실행
│   └── save_map.launch.py     # 맵 저장
├── scripts/
│   ├── create_slam_map.sh     # SLAM 맵 생성 (권장) ⭐
│   ├── save_map.sh            # 맵 저장
│   ├── test_slam.sh           # ROS2 SLAM 테스트
│   └── test_standalone.py     # 독립 실행 테스트
├── rviz/
│   └── slam.rviz              # RViz 설정
├── urdf/
│   └── robot.urdf             # 로봇 모델
└── maps/                      # 저장된 맵
```

---

## 🔧 문제 해결

### LiDAR 연결 안됨

```bash
# USB 포트 확인
ls -la /dev/ttyUSB*

# 권한 확인
sudo chmod 666 /dev/ttyUSB0

# 또는 영구 권한
sudo usermod -aG dialout $USER
# 재로그인 필요
```

### Cartographer 오류

```bash
# 패키지 재설치
sudo apt install --reinstall ros-humble-cartographer-ros

# ROS2 환경 확인
source /opt/ros/humble/setup.bash
```

### YDLidar SDK 오류

```bash
# SDK 경로 확인
ls ~/YDLidar-SDK/build/python

# 재설치
cd ~/YDLidar-SDK/build
cmake .. && make && sudo make install
```

### 메모리 부족 (Jetson Nano)

```bash
# 스왑 메모리 확인
free -h

# 스왑 추가
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# 영구 설정
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

---

## 📊 맵 파일 형식

### PGM 파일
- 흑백 이미지 형식
- 0 (검정) = 장애물
- 254 (흰색) = 자유 공간
- 205 (회색) = 미지 영역

### YAML 파일
```yaml
image: my_map.pgm
resolution: 0.05        # 5cm per pixel
origin: [0.0, 0.0, 0.0] # 맵 원점 [x, y, yaw]
negate: 0
occupied_thresh: 0.65   # 장애물 판정 임계값
free_thresh: 0.196      # 자유공간 판정 임계값
```

---

## 💡 팁

### 좋은 맵을 만들기 위한 팁

1. **천천히 이동**: 급격한 움직임은 맵 품질 저하
2. **루프 클로저**: 같은 장소를 다시 방문하여 오차 보정
3. **충분한 특징점**: 빈 벽보다는 가구나 구조물이 있는 곳이 좋음
4. **일정한 속도**: 갑작스러운 가속/감속 피하기
5. **조명 일정**: LiDAR는 조명에 영향 없지만 일관성 유지

### RC카 운용 팁

1. **배터리 확인**: SLAM은 계산량이 많아 배터리 소모가 큼
2. **냉각**: Jetson Nano 과열 주의 (팬 권장)
3. **안정적인 마운팅**: LiDAR 진동 최소화
4. **높이 일정**: LiDAR 높이를 일정하게 유지

---

## 🔄 업데이트

프로젝트 업데이트:
```bash
cd ~/S14P11A401
git pull origin mapping
```

---

## 📞 지원

문제가 발생하면 다음을 확인하세요:
1. USB 연결 및 권한
2. ROS2 환경 설정
3. YDLidar SDK 설치
4. 메모리 및 CPU 사용량 (Jetson Nano)

---

**버전**: 1.0.0  
**최종 업데이트**: 2026-01-26  
**호환성**: ROS2 Humble, Ubuntu 22.04, Jetson Nano
