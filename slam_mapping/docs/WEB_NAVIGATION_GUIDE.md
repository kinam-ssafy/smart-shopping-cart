# RC Car Web-Based Navigation Guide

웹 기반 클릭-투-내비게이션 시스템 사용 가이드

## 목차

1. [시스템 개요](#시스템-개요)
2. [하드웨어 요구사항](#하드웨어-요구사항)
3. [소프트웨어 설치](#소프트웨어-설치)
4. [맵 생성 (SLAM)](#맵-생성-slam)
5. [내비게이션 실행](#내비게이션-실행)
6. [웹 UI 사용법](#웹-ui-사용법)
7. [파라미터 조정](#파라미터-조정)
8. [문제 해결](#문제-해결)

---

## 시스템 개요

### 아키텍처

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Web Browser    │────▶│  position_server │────▶│  goal_bridge    │
│  (localhost:8850)│     │  (Python HTTP)   │     │  (ROS2 Node)    │
│  - 맵 표시       │     │  - /api/goal     │     │  - Nav2 Action  │
│  - 클릭으로 목표 │     │  - /api/position │     │  - 피드백 전송   │
│  - 경로 표시     │     │  - /api/path     │     │                 │
└─────────────────┘     └──────────────────┘     └────────┬────────┘
                                                          │
                              ┌────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Nav2 Stack                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐   │
│  │ bt_navigator │─▶│ planner_srv │─▶│ controller_server    │   │
│  │ (행동 트리)   │  │ (경로 계획)  │  │ (DWB 로컬 플래너)    │   │
│  └──────────────┘  └──────────────┘  └──────────┬───────────┘   │
│                                                  │               │
│  ┌──────────────────┐  ┌──────────────────────┐  │               │
│  │ local_costmap    │  │ global_costmap       │  │               │
│  │ (실시간 장애물)   │  │ (정적 맵 + 장애물)   │  │               │
│  └──────────────────┘  └──────────────────────┘  │               │
└──────────────────────────────────────────────────┼───────────────┘
                                                   │
                                                   ▼
┌──────────────────┐     ┌──────────────────┐     ┌────────────────┐
│  YDLidar X4/S2   │────▶│  Cartographer    │────▶│  /cmd_vel      │
│  (/scan)         │     │  (위치 추정)      │     │  (Twist)       │
└──────────────────┘     └──────────────────┘     └───────┬────────┘
                                                          │
                                                          ▼
                                                 ┌────────────────┐
                                                 │ cmd_vel_bridge │
                                                 │ x=steer        │
                                                 │ z=forward      │
                                                 │ r=reverse      │
                                                 └───────┬────────┘
                                                         │
                                                         ▼
                                                 ┌────────────────┐
                                                 │    STM32       │
                                                 │  모터 드라이버  │
                                                 └────────────────┘
```

### 주요 기능

- **웹 기반 목표 설정**: 브라우저에서 맵 클릭으로 목표 지점 설정
- **실시간 위치 표시**: Cartographer 기반 위치 추정 결과 실시간 표시
- **자동 경로 계획**: Nav2 NavfnPlanner를 사용한 최적 경로 계획
- **장애물 회피**: DWB 컨트롤러를 사용한 실시간 장애물 회피
- **LiDAR 기반 SLAM**: YDLidar + Cartographer를 이용한 맵 생성 및 위치 추정

---

## 하드웨어 요구사항

### 필수 하드웨어

| 구성품 | 모델 | 설명 |
|--------|------|------|
| LiDAR | YDLidar X4-Pro 또는 S2-Pro | 360° 2D LiDAR, USB 연결 |
| MCU | STM32 | 모터 드라이버, UART 통신 |
| RC Car | - | 차동 구동 또는 Ackermann 조향 |
| 컴퓨터 | Jetson/PC | Ubuntu 22.04, ROS2 Humble |

### 연결 구성

```
컴퓨터
  ├── USB (/dev/ttyUSB0) ──── YDLidar
  └── USB (/dev/ttyACM0) ──── STM32
```

### STM32 통신 프로토콜

```
명령 형식: <axis>=<value>\n

조향:  x=-37 ~ 37    (음수=좌회전, 양수=우회전)
전진:  z=0 ~ 100     (속도)
후진:  r=0 ~ 100     (속도)

예시:
  x=15      # 우측 15도 조향
  z=50      # 전진 속도 50%
  r=0       # 후진 정지
```

---

## 소프트웨어 설치

### 1. ROS2 Humble 설치

```bash
# ROS2 Humble 설치 (Ubuntu 22.04)
sudo apt update && sudo apt install -y curl gnupg lsb-release
sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key -o /usr/share/keyrings/ros-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null
sudo apt update
sudo apt install -y ros-humble-desktop
```

### 2. Nav2 및 Cartographer 설치

```bash
# Nav2 스택
sudo apt install -y \
    ros-humble-nav2-bringup \
    ros-humble-nav2-bt-navigator \
    ros-humble-nav2-planner \
    ros-humble-nav2-controller \
    ros-humble-nav2-behaviors \
    ros-humble-nav2-lifecycle-manager \
    ros-humble-nav2-map-server \
    ros-humble-nav2-velocity-smoother \
    ros-humble-nav2-msgs

# Cartographer
sudo apt install -y \
    ros-humble-cartographer \
    ros-humble-cartographer-ros

# DDS (권장)
sudo apt install -y ros-humble-rmw-cyclonedds-cpp
```

### 3. YDLidar SDK 설치

```bash
cd ~
git clone https://github.com/YDLIDAR/YDLidar-SDK.git
cd YDLidar-SDK
mkdir build && cd build
cmake ..
make
sudo make install
```

### 4. Python 패키지 설치

```bash
pip3 install pyserial
```

### 5. 워크스페이스 빌드

```bash
cd ~/S14P11A401/slam_mapping
source /opt/ros/humble/setup.bash
colcon build --packages-select rccar_nodes --symlink-install
source install/setup.bash
```

### 6. USB 권한 설정

```bash
# LiDAR 및 STM32 USB 권한
sudo usermod -aG dialout $USER
sudo chmod 666 /dev/ttyUSB0
sudo chmod 666 /dev/ttyACM0

# 재로그인 필요
```

---

## 맵 생성 (SLAM)

내비게이션을 사용하기 전에 먼저 맵을 생성해야 합니다.

### 1. SLAM 매핑 실행

```bash
cd ~/S14P11A401/slam_mapping

# SLAM 매핑 시작 (웹 UI 포함)
./scripts/start_slam_web.sh /dev/ttyUSB0
```

### 2. 맵 생성

1. 웹 브라우저에서 `http://localhost:8850` 접속
2. RC카를 수동으로 조종하여 공간 전체를 탐색
3. 맵이 완성되면 저장

### 3. 맵 저장

```bash
# 새 터미널에서 맵 저장
cd ~/S14P11A401/slam_mapping
./scripts/save_map.sh my_map_name

# 저장되는 파일:
#   maps/my_map_name.pgm      - 맵 이미지
#   maps/my_map_name.yaml     - 맵 메타데이터
#   maps/my_map_name.pbstream - Cartographer 상태 (위치 추정용)
```

---

## 내비게이션 실행

### 시뮬레이션 모드 (테스트용)

모터 없이 경로 계획만 테스트:

```bash
cd ~/S14P11A401/slam_mapping

# 시뮬레이션 모드 (모터 명령 로그만 출력)
./scripts/start_full_navigation.sh /dev/ttyUSB0 my_map_name true
```

### 실제 주행 모드

```bash
cd ~/S14P11A401/slam_mapping

# 실제 모드 (STM32로 모터 명령 전송)
./scripts/start_full_navigation.sh /dev/ttyUSB0 my_map_name false /dev/ttyACM0
```

### 명령어 형식

```bash
./scripts/start_full_navigation.sh [LiDAR포트] [맵이름] [시뮬레이션] [STM32포트]

매개변수:
  LiDAR포트    - LiDAR 시리얼 포트 (기본값: /dev/ttyUSB0)
  맵이름       - maps/ 폴더의 맵 파일명 (기본값: s4_map)
  시뮬레이션   - true/false (기본값: true)
  STM32포트    - STM32 시리얼 포트 (기본값: /dev/ttyACM0)
```

### 시스템 종료

```bash
# Ctrl+C 또는
pkill -f "position_server"
pkill -f "ydlidar"
pkill -f "cartographer"
pkill -f "nav2"
pkill -f "goal_bridge"
pkill -f "cmd_vel_bridge"
```

---

## 웹 UI 사용법

### 접속

브라우저에서 `http://localhost:8850` 접속

### 인터페이스

```
┌─────────────────────────────────────────────┐
│  RC Car Navigation                          │
├─────────────────────────────────────────────┤
│                                             │
│     ┌─────────────────────────────┐         │
│     │                             │         │
│     │         맵 영역              │         │
│     │    (클릭하여 목표 설정)      │         │
│     │                             │         │
│     │    🔵 현재 위치              │         │
│     │    🟠 목표 지점              │         │
│     │    --- 계획된 경로           │         │
│     │                             │         │
│     └─────────────────────────────┘         │
│                                             │
│  상태: 주행 중  |  남은 거리: 2.5m          │
│  [목표 취소]                                │
│                                             │
└─────────────────────────────────────────────┘
```

### 조작 방법

1. **목표 설정**: 맵의 원하는 위치를 클릭
2. **경로 확인**: 보라색 점선으로 계획된 경로 표시
3. **진행 상황**: 하단 상태 패널에서 남은 거리 확인
4. **목표 취소**: "Cancel" 버튼 클릭

### 상태 표시

| 상태 | 설명 |
|------|------|
| idle | 대기 중 |
| navigating | 목표로 이동 중 |
| succeeded | 목표 도달 완료 |
| failed | 내비게이션 실패 |
| canceled | 사용자가 취소함 |

---

## 파라미터 조정

### 속도 조정 (config/nav2_params.yaml)

```yaml
controller_server:
  ros__parameters:
    FollowPath:
      max_vel_x: 0.22      # 최대 전진 속도 (m/s)
      max_vel_theta: 1.0   # 최대 회전 속도 (rad/s)
      min_vel_x: 0.0       # 최소 전진 속도
```

### 목표 허용 오차

```yaml
controller_server:
  ros__parameters:
    general_goal_checker:
      xy_goal_tolerance: 0.15    # 위치 허용 오차 (m)
      yaw_goal_tolerance: 0.25   # 방향 허용 오차 (rad)
```

### 장애물 감지 범위

```yaml
local_costmap:
  local_costmap:
    ros__parameters:
      width: 3              # costmap 너비 (m)
      height: 3             # costmap 높이 (m)
      resolution: 0.05      # 해상도 (m/pixel)
      robot_radius: 0.15    # 로봇 반경 (m)
      inflation_radius: 0.35  # 팽창 반경 (m)
```

### cmd_vel_bridge 파라미터

스크립트에서 직접 조정 또는 ros2 param으로 설정:

```bash
# 최대 조향각 (기본값: 37)
-p max_steer:=37

# 속도 범위 (기본값: 30~100)
-p min_speed:=30
-p max_speed:=100
```

---

## 문제 해결

### 포트 충돌 (Address already in use)

```bash
# 사용 중인 포트 확인 및 종료
fuser -k 8850/tcp
fuser -k 8851/tcp

# 또는 모든 관련 프로세스 종료
pkill -9 -f "position_server"
pkill -9 -f "goal_bridge"
```

### LiDAR 연결 실패

```bash
# 포트 확인
ls -la /dev/ttyUSB*

# 권한 설정
sudo chmod 666 /dev/ttyUSB0

# LiDAR 테스트
ros2 run rccar_nodes ydlidar_node --ros-args -p port:=/dev/ttyUSB0
```

### Nav2 노드 활성화 실패

```bash
# 노드 상태 확인
ros2 lifecycle list /bt_navigator
ros2 lifecycle get /bt_navigator

# 수동 활성화
ros2 lifecycle set /bt_navigator configure
ros2 lifecycle set /bt_navigator activate
```

### 경로 계획 실패

- 목표 지점이 장애물 위에 있는지 확인
- costmap이 제대로 로드되었는지 확인:
  ```bash
  ros2 topic echo /global_costmap/costmap --once
  ```

### STM32 통신 실패

```bash
# 포트 확인
ls -la /dev/ttyACM*

# 시리얼 테스트
echo "x=0" > /dev/ttyACM0
echo "z=0" > /dev/ttyACM0

# 권한 설정
sudo chmod 666 /dev/ttyACM0
```

### TF 변환 오류

```bash
# TF 트리 확인
ros2 run tf2_tools view_frames

# TF 모니터링
ros2 run tf2_ros tf2_echo map base_link
```

---

## 파일 구조

```
slam_mapping/
├── config/
│   ├── nav2_params.yaml          # Nav2 설정
│   ├── ydlidar_2d.lua            # Cartographer SLAM 설정
│   └── ydlidar_2d_localization.lua  # Cartographer 위치 추정 설정
├── maps/
│   ├── {map_name}.pgm            # 맵 이미지
│   ├── {map_name}.yaml           # 맵 메타데이터
│   └── {map_name}.pbstream       # Cartographer 상태
├── scripts/
│   ├── start_full_navigation.sh  # 전체 내비게이션 시작
│   ├── start_slam_web.sh         # SLAM 매핑 시작
│   └── save_map.sh               # 맵 저장
├── rccar_nodes/
│   ├── ydlidar_node.py           # LiDAR 드라이버
│   ├── tf_to_web.py              # TF → 웹 서버 전송
│   ├── goal_bridge.py            # 웹 → Nav2 브릿지
│   └── cmd_vel_bridge.py         # Nav2 → STM32 브릿지
├── web/
│   ├── index.html                # 웹 UI
│   └── position_server.py        # 웹 서버
└── docs/
    └── WEB_NAVIGATION_GUIDE.md   # 이 문서
```

---

## 라이선스

MIT License

## 기여

버그 리포트 및 기능 요청: [GitHub Issues](https://github.com/anthropics/claude-code/issues)
