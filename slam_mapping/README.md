# RC Car SLAM & Navigation Project

YDLidar와 Google Cartographer를 사용한 2D SLAM 맵핑 및 Nav2 기반 자율 주행 프로젝트입니다.

## 목차
- [주요 기능](#주요-기능)
- [빠른 시작](#빠른-시작)
- [디렉토리 구조](#디렉토리-구조)
- [문서](#문서)

---

## 주요 기능

### 1. SLAM 맵 생성
LiDAR를 사용한 실시간 2D SLAM 맵핑

```bash
# 맵 생성
./scripts/create_slam_map.sh /dev/ttyUSB0

# 맵 저장
./scripts/save_map.sh <맵_이름>
```

### 2. 웹 내비게이션 (현재 위치 표시)
웹 브라우저에서 실시간으로 로봇 위치 확인

### 3. 클릭 기반 Nav2 자율 주행
웹에서 목표 지점 클릭 시 Nav2를 통한 장애물 회피 자율 주행

```bash
./scripts/start_full_navigation.sh /dev/ttyUSB0 my_map false /dev/ttyACM0
# 브라우저: http://localhost:8850
```

### 4. 자율 탐색 맵핑 (로봇 청소기 방식)
m-explore를 사용한 자율적인 환경 탐색 및 맵 생성

```bash
./scripts/start_autonomous_mapping.sh /dev/ttyUSB0 600 /dev/ttyACM0 false
# 브라우저: http://localhost:8849
```

---

## 시스템 구성

- **LiDAR**: YDLidar X4-Pro / S2PRO (360도 2D 레이저 스캐너)
- **SLAM**: Google Cartographer
- **Navigation**: Nav2 (Smac Hybrid-A* Planner)
- **ROS2**: Humble Hawksbill
- **DDS**: CycloneDDS
- **맵 해상도**: 5cm/pixel (0.05m)

---

## 빠른 시작

### 사전 요구사항

```bash
# ROS2 Humble 설치 확인
ros2 --version

# 필수 패키지 설치
sudo apt install -y ros-humble-cartographer-ros \
                    ros-humble-nav2-bringup \
                    ros-humble-rmw-cyclonedds-cpp
```

### 빌드

```bash
cd ~/S14P11A401/slam_mapping
colcon build --symlink-install
source install/setup.bash
```

### 실행

#### SLAM 맵 생성
```bash
./scripts/create_slam_map.sh /dev/ttyUSB0
./scripts/save_map.sh my_map
```

#### 웹 내비게이션
```bash
./scripts/start_full_navigation.sh /dev/ttyUSB0 my_map false /dev/ttyACM0
# 브라우저에서 http://localhost:8850 접속
```

---

## 디렉토리 구조

```
slam_mapping/
├── rccar_nodes/                     # ROS2 Python 패키지
│   ├── ydlidar_node.py              # YDLidar 드라이버
│   ├── cmd_vel_bridge.py            # /cmd_vel → 모터 제어
│   ├── goal_bridge.py               # 웹 API ↔ Nav2 브릿지
│   ├── tf_to_web.py                 # TF → 웹 서버 전송
│   └── odom_publisher.py            # 오도메트리 발행
│
├── config/                          # 설정 파일
│   ├── ydlidar_2d.lua               # Cartographer SLAM 설정
│   ├── ydlidar_2d_localization.lua  # Cartographer 위치추정 설정
│   ├── nav2_params.yaml             # Nav2 내비게이션 설정
│   ├── nav2_explore_params.yaml     # 자율 탐색 Nav2 설정
│   ├── explore_params.yaml          # m-explore 설정
│   └── cyclonedds_*.xml             # DDS 네트워크 설정
│
├── launch/                          # ROS2 런치 파일
│   ├── cartographer.launch.py       # Cartographer SLAM
│   ├── nav2_navigation.launch.py    # Nav2 스택
│   └── slam_mapping.launch.py       # 기본 SLAM
│
├── scripts/                         # 실행 스크립트
│   ├── create_slam_map.sh           # SLAM 맵 생성
│   ├── create_slam_map_headless.sh  # SLAM (디스플레이 없음)
│   ├── save_map.sh                  # 맵 저장
│   ├── start_full_navigation.sh     # 웹 내비게이션 시작
│   ├── start_autonomous_mapping.sh  # 자율 탐색 맵핑 시작
│   └── setup_*.sh                   # 환경 설정 스크립트
│
├── web/                             # 웹 인터페이스
│   ├── position_server.py           # HTTP 서버 (REST API)
│   └── index.html                   # 웹 UI
│
├── maps/                            # 저장된 맵 파일
│   ├── *.pgm                        # 맵 이미지
│   ├── *.yaml                       # 맵 메타데이터
│   └── *.pbstream                   # Cartographer 상태
│
├── docs/                            # 문서
│   ├── SLAM_MAPPING_GUIDE.md        # SLAM 가이드
│   ├── WEB_NAVIGATION_GUIDE.md      # 웹 내비게이션 가이드
│   ├── AUTONOMOUS_EXPLORATION_GUIDE.md  # 자율 탐색 가이드
│   ├── REMOTE_SLAM_VISUALIZATION_GUIDE.md
│   └── REMOTE_RVIZ_GUIDE.md
│
├── rviz/                            # RViz 설정
│   └── slam.rviz
│
├── urdf/                            # 로봇 모델
│   └── robot.urdf
│
├── package.xml                      # ROS2 패키지 정의
└── setup.py                         # Python 패키지 설정
```

---

## 문서

| 문서 | 설명 |
|------|------|
| [SLAM_MAPPING_GUIDE.md](docs/SLAM_MAPPING_GUIDE.md) | SLAM 맵 생성 및 저장 가이드 |
| [WEB_NAVIGATION_GUIDE.md](docs/WEB_NAVIGATION_GUIDE.md) | 웹 기반 내비게이션 시스템 가이드 |
| [AUTONOMOUS_EXPLORATION_GUIDE.md](docs/AUTONOMOUS_EXPLORATION_GUIDE.md) | 자율 탐색 맵핑 가이드 |
| [REMOTE_SLAM_VISUALIZATION_GUIDE.md](docs/REMOTE_SLAM_VISUALIZATION_GUIDE.md) | 원격 SLAM 시각화 가이드 |
| [REMOTE_RVIZ_GUIDE.md](docs/REMOTE_RVIZ_GUIDE.md) | 원격 RViz 연결 가이드 |

---

## 주요 토픽

| 토픽 | 타입 | 설명 |
|------|------|------|
| `/scan` | sensor_msgs/LaserScan | LiDAR 스캔 데이터 |
| `/map` | nav_msgs/OccupancyGrid | 2D 점유 격자 맵 |
| `/cmd_vel` | geometry_msgs/Twist | 속도 명령 |
| `/tf`, `/tf_static` | TF 변환 | 좌표계 변환 |

---

## TF 구조

```
map (Cartographer)
 └─ odom (Cartographer)
     └─ base_link (Static)
         └─ laser (Static)
```

---

## 포트 정보

| 서비스 | 포트 | 설명 |
|--------|------|------|
| 웹 내비게이션 | 8850 | 웹 UI 및 API |
| 자율 탐색 맵핑 | 8849 | 탐색 모니터링 |
| Goal Bridge | 8851 | Nav2 목표 수신 |

---

## 문제 해결

### LiDAR 연결 안 됨
```bash
sudo chmod 666 /dev/ttyUSB0
```

### 패키지 찾을 수 없음
```bash
source /opt/ros/humble/setup.bash
source ~/S14P11A401/slam_mapping/install/setup.bash
```

### 포트 충돌
```bash
fuser -k 8850/tcp
```

---

## 참고 자료

- [Cartographer ROS2](https://google-cartographer-ros.readthedocs.io/)
- [Nav2 Documentation](https://navigation.ros.org/)
- [m-explore-ros2](https://github.com/robo-friends/m-explore-ros2)
- [YDLidar SDK](https://github.com/YDLIDAR/YDLidar-SDK)

---

**테스트 환경**: Ubuntu 22.04 + ROS2 Humble + YDLidar X4-Pro
