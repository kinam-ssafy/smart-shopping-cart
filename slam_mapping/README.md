# SLAM Mapping Project

YDLidar S2PRO와 Google Cartographer를 사용한 2D SLAM 맵핑 프로젝트입니다.

## 목차
- [개요](#개요)
- [빠른 시작](#빠른-시작)
- [사용 시나리오](#사용-시나리오)
- [디렉토리 구조](#디렉토리-구조)
- [문서](#문서)

---

## 개요

### 시스템 구성
- **LiDAR**: YDLidar S2PRO (360도 2D 레이저 스캐너)
- **SLAM 알고리즘**: Google Cartographer
- **ROS2**: Humble Hawksbill
- **DDS**: CycloneDDS
- **맵 해상도**: 2.5cm/pixel (0.05m)

### 주요 기능
- ✅ 실시간 2D SLAM 맵핑
- ✅ RViz를 통한 실시간 시각화
- ✅ 원격 네트워크 통신 지원
- ✅ RC카와 원격 PC 간 토픽 공유
- ✅ 맵 저장 및 로드

---

## 빠른 시작

### 시나리오 1: 로컬 SLAM (디스플레이 있음)

**1. 포트 권한 설정**
```bash
sudo chmod 666 /dev/ttyUSB0
```

**2. SLAM 실행**
```bash
cd /home/seonil/slam_mapping
./scripts/create_slam_map.sh /dev/ttyUSB0
```

**3. 맵 저장**
```bash
./scripts/save_map.sh <맵_이름>
```

자세한 내용은 [SLAM_MAPPING_GUIDE.md](SLAM_MAPPING_GUIDE.md)를 참조하세요.

---

### 시나리오 2: 원격 SLAM (RC카 + 원격 PC)

#### RC카 설정 (한 번만 실행)

```bash
cd /home/seonil/slam_mapping
./scripts/setup_rc_car.sh
source ~/.bashrc
```

#### 원격 PC 설정 (한 번만 실행)

```bash
cd ~/slam_mapping
./scripts/setup_remote_pc.sh
source ~/.bashrc
```

#### SLAM 실행

**RC카에서:**
```bash
# 터미널 1: SLAM 실행
cd /home/seonil/slam_mapping
./scripts/create_slam_map_headless.sh /dev/ttyUSB0

# 터미널 2: RC카 조종
python3 control_car.py
```

**원격 PC에서:**
```bash
# 토픽 확인
ros2 topic list
ros2 topic hz /scan

# RViz 실행
rviz2 -d ~/slam_mapping/rviz/slam.rviz
```

자세한 내용은 [REMOTE_SLAM_VISUALIZATION_GUIDE.md](REMOTE_SLAM_VISUALIZATION_GUIDE.md)를 참조하세요.

---

## 사용 시나리오

### 1. 로컬 SLAM (디스플레이 연결)
- **대상**: 라즈베리파이 또는 PC에 모니터 연결
- **특징**: RViz가 로컬에서 실행
- **스크립트**: `create_slam_map.sh`
- **가이드**: [SLAM_MAPPING_GUIDE.md](SLAM_MAPPING_GUIDE.md)

### 2. 원격 SLAM (RC카 + 노트북)
- **대상**: RC카(Jetson Nano, 디스플레이 없음) + 원격 PC
- **특징**:
  - RC카에서 SLAM 실행 (RViz 없음)
  - 원격 PC에서 RViz로 시각화
  - RC카 조종하며 실시간 맵핑
- **스크립트**: `create_slam_map_headless.sh`
- **가이드**: [REMOTE_SLAM_VISUALIZATION_GUIDE.md](REMOTE_SLAM_VISUALIZATION_GUIDE.md)

---

## 디렉토리 구조

```
slam_mapping/
├── config/
│   ├── ydlidar_2d.lua              # Cartographer 설정
│   ├── cyclonedds_rc_car.xml       # CycloneDDS 설정 (RC카)
│   └── cyclonedds_remote_pc.xml    # CycloneDDS 설정 (원격 PC)
├── maps/                            # 저장된 맵 파일
│   ├── *.pgm                        # 맵 이미지
│   └── *.yaml                       # 맵 메타데이터
├── rviz/
│   └── slam.rviz                   # RViz 설정
├── scripts/
│   ├── create_slam_map.sh          # SLAM 실행 (로컬, RViz 포함)
│   ├── create_slam_map_headless.sh # SLAM 실행 (원격, RViz 없음)
│   ├── save_map.sh                 # 맵 저장
│   ├── setup_rc_car.sh             # RC카 환경 설정
│   └── setup_remote_pc.sh          # 원격 PC 환경 설정
├── slam_mapping2/                  # ROS2 패키지
│   ├── __init__.py
│   └── ydlidar_simple_node.py      # YDLidar ROS2 노드
├── package.xml                      # ROS2 패키지 정의
├── setup.py                         # Python 패키지 설정
├── control_car.py                   # RC카 조종 스크립트
├── README.md                        # 이 파일
├── SLAM_MAPPING_GUIDE.md           # 로컬 SLAM 가이드
└── REMOTE_SLAM_VISUALIZATION_GUIDE.md  # 원격 SLAM 가이드
```

---

## 문서

### 📘 [SLAM_MAPPING_GUIDE.md](SLAM_MAPPING_GUIDE.md)
로컬 SLAM 맵 생성 및 저장 가이드
- 초기 설정 (LiDAR 권한, CycloneDDS 설정)
- SLAM 실행 및 맵핑 팁
- 로컬/원격 RViz 시각화
- 맵 저장 방법
- 토픽 및 노드 확인
- 문제 해결

### 📗 [REMOTE_SLAM_VISUALIZATION_GUIDE.md](REMOTE_SLAM_VISUALIZATION_GUIDE.md)
원격 SLAM 시각화 가이드 (RC카 + 원격 PC)
- 네트워크 구성 (RC카: 70.12.247.62, 원격 PC: 70.12.246.46)
- RC카 설정 (CycloneDDS, 환경 변수)
- 원격 PC 설정 (ROS2 설치, CycloneDDS)
- SLAM 실행 및 원격 시각화
- 네트워크 진단 및 문제 해결
- 최적화 팁

---

## 필수 요구사항

### 하드웨어
- YDLidar S2PRO (USB 연결)
- 라즈베리파이 / Jetson Nano / Ubuntu PC

### 소프트웨어
- Ubuntu 22.04
- ROS2 Humble
- Cartographer ROS2
- YDLidar SDK
- CycloneDDS

---

## 빠른 명령어 참조

### SLAM 실행
```bash
# 로컬 (RViz 포함)
./scripts/create_slam_map.sh /dev/ttyUSB0

# 원격 (RViz 없음)
./scripts/create_slam_map_headless.sh /dev/ttyUSB0
```

### 맵 저장
```bash
./scripts/save_map.sh <맵_이름>
```

### 토픽 확인
```bash
# 토픽 리스트
ros2 topic list

# 스캔 데이터 확인
ros2 topic hz /scan
ros2 topic echo /scan --once

# 노드 확인
ros2 node list
ros2 node info /ydlidar_simple_node
```

### RViz 실행
```bash
# 로컬
rviz2 -d ./rviz/slam.rviz

# 원격
rviz2 -d ~/slam_mapping/rviz/slam.rviz
```

---

## 주요 토픽

- `/scan` - LiDAR 스캔 데이터 (sensor_msgs/LaserScan)
- `/map` - 2D 점유 격자 맵 (nav_msgs/OccupancyGrid)
- `/tf` - 동적 좌표 변환
- `/tf_static` - 정적 좌표 변환 (base_link → laser)
- `/trajectory_node_list` - 로봇 이동 경로
- `/constraint_list` - 루프 클로저 연결
- `/robot_marker` - 로봇 시각화 마커

---

## TF 구조

```
map (Cartographer)
 └─ odom (Cartographer)
     └─ base_link (Static)
         └─ laser (Static)
```

---

## 문제 해결

### 토픽이 보이지 않음
- CycloneDDS 설정 확인: `cat ~/cyclonedds/*.xml`
- 환경 변수 확인: `env | grep -E "RMW|CYCLONE|ROS_DOMAIN"`
- SLAM 재시작

### LiDAR 초기화 실패
```bash
# 포트 권한 설정
sudo chmod 666 /dev/ttyUSB0

# udev 규칙 설정 (영구)
sudo ./scripts/setup_rc_car.sh  # 또는 setup_remote_pc.sh
```

### 원격 통신 안 됨
- Ping 테스트: `ping 70.12.247.62` (또는 70.12.246.46)
- 방화벽 확인: `sudo ufw status`
- CycloneDDS Peer 설정 확인

자세한 문제 해결은 각 가이드 문서를 참조하세요.

---

## 라이선스

이 프로젝트는 교육 및 연구 목적으로 사용됩니다.

---

## 참고 자료

- [Cartographer ROS2 Documentation](https://google-cartographer-ros.readthedocs.io/)
- [YDLidar SDK GitHub](https://github.com/YDLIDAR/YDLidar-SDK)
- [CycloneDDS Documentation](https://cyclonedds.io/)
- [ROS2 Humble Documentation](https://docs.ros.org/en/humble/)

---

**작성일**: 2026-01-28
**버전**: 1.0
**테스트 환경**: Ubuntu 22.04 + ROS2 Humble + YDLidar S2PRO
