# SLAM 맵 생성 및 저장 가이드

YDLidar와 Cartographer를 사용한 실시간 SLAM 맵핑 가이드입니다.

## 목차
1. [개요](#개요)
2. [필수 요구사항](#필수-요구사항)
3. [초기 설정](#초기-설정)
4. [SLAM 맵 생성](#slam-맵-생성)
5. [RViz 시각화](#rviz-시각화)
6. [맵 저장](#맵-저장)
7. [문제 해결](#문제-해결)

---

## 개요

### 시스템 구성
- **LiDAR**: YDLidar S2PRO (360도 2D 스캔)
- **SLAM 알고리즘**: Google Cartographer
- **ROS2**: Humble Hawksbill
- **DDS**: CycloneDDS (로컬 및 원격 통신 지원)
- **맵 해상도**: 2.5cm/pixel (0.05m)

### TF 구조
```
map -> odom -> base_link -> laser
```
- `map -> odom`: Cartographer가 관리
- `base_link -> laser`: Static TF (고정)

---

## 필수 요구사항

### 하드웨어
- YDLidar S2PRO (USB 연결)
- 라즈베리파이 또는 Ubuntu 컴퓨터

### 소프트웨어
- Ubuntu 22.04
- ROS2 Humble
- Cartographer ROS2
- YDLidar SDK
- CycloneDDS

### 설치 확인
```bash
# ROS2 설치 확인
ros2 --version

# Cartographer 설치 확인
ros2 pkg list | grep cartographer

# YDLidar SDK 확인
ls ~/YDLidar-SDK/build/python
```

---

## 초기 설정

### 1. LiDAR 포트 권한 설정

#### 방법 1: 영구적 설정 (권장)
```bash
# udev 규칙 생성
echo 'KERNEL=="ttyUSB*", ATTRS{idVendor}=="10c4", ATTRS{idProduct}=="ea60", MODE="0666", GROUP="dialout"' | sudo tee /etc/udev/rules.d/99-ydlidar.rules

# 규칙 적용
sudo udevadm control --reload-rules
sudo udevadm trigger

# LiDAR USB 재연결 (뽑았다 꽂기)
```

#### 방법 2: 임시 설정 (매번 실행)
```bash
sudo chmod 666 /dev/ttyUSB0
```

### 2. CycloneDDS 설정

`~/cyclonedds/config.xml` 파일 생성:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CycloneDDS>
  <Domain>
    <General>
      <AllowMulticast>true</AllowMulticast>
      <NetworkInterfaceAddress>auto</NetworkInterfaceAddress>
    </General>
    <Discovery>
      <ParticipantIndex>auto</ParticipantIndex>
      <MaxAutoParticipantIndex>100</MaxAutoParticipantIndex>
      <Peers>
        <Peer address="localhost"/>
      </Peers>
    </Discovery>
  </Domain>
</CycloneDDS>
```

**중요:**
- `AllowMulticast: true` - 로컬 discovery 지원
- `localhost` Peer 추가 - 같은 컴퓨터 내 통신 지원
- 원격 컴퓨터와 통신하려면 `<Peer address="원격_IP"/>` 추가

### 3. 환경 변수 설정

`~/.bashrc`에 추가:
```bash
# ROS2 환경
source /opt/ros/humble/setup.bash

# CycloneDDS 설정
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
export CYCLONEDDS_URI=file://$HOME/cyclonedds/config.xml
export ROS_DOMAIN_ID=0
```

적용:
```bash
source ~/.bashrc
```

---

## SLAM 맵 생성

### 1. SLAM 시작

```bash
cd /home/seonil/slam_mapping
./scripts/create_slam_map.sh /dev/ttyUSB0
```

### 실행 과정
1. **포트 권한 확인**: `/dev/ttyUSB0` 접근 권한 체크
2. **빌드**: `colcon build --symlink-install` 실행
3. **환경 소스**: `install/setup.bash` 로드
4. **노드 시작**:
   - YDLidar Simple Node (스캔 발행)
   - Cartographer Node (SLAM 처리)
   - Occupancy Grid Node (맵 생성)
   - RViz (시각화)

### 실행 확인

**정상 로그:**
```
[INFO] [ydlidar_simple_node]: YDLidar ready on /dev/ttyUSB0
[INFO] [ydlidar_simple_node]: Scans: 100, Points: 1191
[INFO] [cartographer logger]: Added trajectory with ID '0'
```

### 2. 맵핑 팁

- **천천히 이동**: LiDAR를 천천히 이동시켜 세밀한 맵 생성
- **중복 스캔**: 같은 영역을 여러 번 지나가면 정확도 향상
- **루프 클로저**: 시작 지점으로 돌아오면 맵 보정
- **조명**: 어두운 환경에서도 작동 (LiDAR는 빛에 영향 없음)

---

## RViz 시각화

### 로컬 RViz (라즈베리파이)

스크립트 실행 시 자동으로 RViz가 시작됩니다.

### 원격 RViz (노트북에서 접속)

#### 1. 노트북 설정

**환경 변수** (`~/.bashrc`):
```bash
source /opt/ros/humble/setup.bash
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
export CYCLONEDDS_URI=file://$HOME/cyclonedds/config.xml
export ROS_DOMAIN_ID=0
```

**CycloneDDS 설정** (`~/cyclonedds/config.xml`):
```xml
<?xml version="1.0" encoding="UTF-8"?>
<CycloneDDS>
  <Domain>
    <General>
      <AllowMulticast>true</AllowMulticast>
      <NetworkInterfaceAddress>auto</NetworkInterfaceAddress>
    </General>
    <Discovery>
      <ParticipantIndex>auto</ParticipantIndex>
      <MaxAutoParticipantIndex>100</MaxAutoParticipantIndex>
      <Peers>
        <Peer address="localhost"/>
        <Peer address="라즈베리파이_IP"/>
      </Peers>
    </Discovery>
  </Domain>
</CycloneDDS>
```

#### 2. RViz 실행

```bash
source /opt/ros/humble/setup.bash
rviz2 -d ~/slam_mapping/rviz/slam.rviz
```

### RViz 화면 구성

- **Grid**: 맵 기준 격자
- **TF**: 좌표계 표시 (map, odom, base_link, laser)
- **LaserScan (밝은 녹색)**: 현재 LiDAR 스캔
- **Map (회색)**: 생성된 2D 점유 격자 맵
- **Trajectory (빨간색)**: 로봇 이동 경로
- **Constraints**: 루프 클로저 연결선
- **Robot Pose**: 로봇 현재 위치 (화살표)
- **Robot Shape (파란 원)**: 로봇 형태 시각화

---

## 맵 저장

### 1. 맵 저장 스크립트 실행

**새 터미널**에서:
```bash
cd /home/seonil/slam_mapping
./scripts/save_map.sh <맵_이름>
```

예시:
```bash
./scripts/save_map.sh office_floor1
```

### 2. 저장 파일

`maps/` 디렉토리에 다음 파일이 생성됩니다:
- `<맵_이름>.pgm` - 맵 이미지 (Portable Gray Map)
- `<맵_이름>.yaml` - 맵 메타데이터

### 3. YAML 파일 내용

```yaml
image: office_floor1.pgm
resolution: 0.05           # 2.5cm/pixel
origin: [-10.0, -10.0, 0.0]
negate: 0
occupied_thresh: 0.65
free_thresh: 0.196
```

### 4. 저장된 맵 확인

```bash
# 이미지 뷰어로 확인
eog maps/<맵_이름>.pgm

# 또는
gimp maps/<맵_이름>.pgm
```

---

## 토픽 확인

### 토픽 리스트

```bash
ros2 topic list
```

**출력 예시:**
```
/scan                    # LiDAR 스캔
/tf                      # 동적 좌표 변환
/tf_static               # 정적 좌표 변환
/map                     # 점유 격자 맵
/trajectory_node_list    # 이동 경로
/constraint_list         # 루프 클로저
/robot_marker            # 로봇 마커
/tracked_pose            # 로봇 위치
/submap_list             # Cartographer 서브맵
```

### 토픽 데이터 확인

```bash
# 스캔 데이터 한 번 출력
ros2 topic echo /scan --once

# 스캔 발행 주파수 확인 (10Hz 예상)
ros2 topic hz /scan

# 맵 데이터 확인
ros2 topic echo /map --once
```

### 노드 확인

```bash
# 실행 중인 노드 리스트
ros2 node list

# 특정 노드 정보
ros2 node info /ydlidar_simple_node
ros2 node info /cartographer_node
```

### TF 확인

```bash
# TF 트리 출력
ros2 run tf2_tools view_frames

# TF 관계 확인
ros2 run tf2_ros tf2_echo map base_link
```

---

## 문제 해결

### 1. 토픽이 보이지 않음

**증상:**
```bash
ros2 topic list
# /parameter_events
# /rosout
```

**원인:** CycloneDDS discovery 설정 문제

**해결:**
1. CycloneDDS 설정 확인:
   ```bash
   cat ~/cyclonedds/config.xml
   ```
2. `AllowMulticast: true` 확인
3. `<Peer address="localhost"/>` 확인
4. SLAM 재시작

### 2. YDLidar 초기화 실패

**증상:**
```
[error] Error, cannot bind to the specified [serial port:/dev/ttyUSB0]
[ERROR] [ydlidar_simple_node]: Failed to init YDLidar
```

**원인:** 포트 권한 문제

**해결:**
```bash
# 포트 확인
ls -l /dev/ttyUSB0

# 권한 설정
sudo chmod 666 /dev/ttyUSB0

# 영구 설정 (udev 규칙)
echo 'KERNEL=="ttyUSB*", ATTRS{idVendor}=="10c4", ATTRS{idProduct}=="ea60", MODE="0666", GROUP="dialout"' | sudo tee /etc/udev/rules.d/99-ydlidar.rules
sudo udevadm control --reload-rules
sudo udevadm trigger
```

### 3. LiDAR 포트를 찾을 수 없음

**증상:**
```
Warning: LiDAR not found at /dev/ttyUSB0
No ttyUSB devices
```

**해결:**
```bash
# USB 장치 확인
lsusb | grep -i "Silicon Labs"

# 시리얼 포트 확인
ls -la /dev/ttyUSB* /dev/ttyACM*

# LiDAR USB 재연결 (뽑았다 꽂기)
```

### 4. 빌드 실패

**증상:**
```
Error: colcon build failed
```

**해결:**
```bash
# 빌드 캐시 삭제
cd /home/seonil/slam_mapping
rm -rf build install log

# 의존성 확인
rosdep install --from-paths . --ignore-src -r -y

# 다시 빌드
colcon build --symlink-install
```

### 5. RViz가 실행되지 않음

**증상:**
```
qt.qpa.xcb: could not connect to display
```

**원인:** X11 디스플레이 문제 (원격 SSH 접속 시)

**해결:**

**로컬 실행:**
- 모니터를 라즈베리파이에 직접 연결

**원격 실행:**
- 노트북에서 RViz 실행 (위 "원격 RViz" 섹션 참조)

**SSH X11 포워딩:**
```bash
ssh -X seonil@라즈베리파이_IP
```

### 6. 환경 변수 불일치

**증상:**
- 한 터미널에서는 토픽이 보이지만 다른 터미널에서는 안 보임

**해결:**
모든 터미널에서 동일한 환경 변수 설정:
```bash
source /opt/ros/humble/setup.bash
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
export CYCLONEDDS_URI=file://$HOME/cyclonedds/config.xml
export ROS_DOMAIN_ID=0
```

또는 `~/.bashrc`에 추가하고 새 터미널 열기

---

## 디렉토리 구조

```
slam_mapping/
├── config/
│   ├── ydlidar_2d.lua          # Cartographer 설정
│   └── fastdds.xml             # FastDDS 설정 (사용 안 함)
├── maps/                        # 저장된 맵 파일
│   ├── SEOUL_4.pgm
│   └── SEOUL_4.yaml
├── rviz/
│   └── slam.rviz               # RViz 설정
├── scripts/
│   ├── create_slam_map.sh      # SLAM 실행 스크립트
│   └── save_map.sh             # 맵 저장 스크립트
├── slam_mapping2/              # ROS2 패키지
│   ├── __init__.py
│   └── ydlidar_simple_node.py  # YDLidar 노드
├── urdf/
│   └── robot.urdf              # 로봇 모델 (사용 안 함)
├── package.xml                  # ROS2 패키지 정의
├── setup.py                     # Python 패키지 설정
└── SLAM_MAPPING_GUIDE.md       # 이 파일
```

---

## 추가 리소스

### 관련 문서
- [Cartographer ROS2 문서](https://google-cartographer-ros.readthedocs.io/)
- [YDLidar SDK GitHub](https://github.com/YDLIDAR/YDLidar-SDK)
- [CycloneDDS 설정 가이드](https://github.com/eclipse-cyclonedds/cyclonedds)

### 유용한 명령어

```bash
# 모든 ROS2 프로세스 종료
pkill -f ros2
pkill -f rviz2
pkill -f cartographer
pkill -f ydlidar

# 실시간 로그 확인
ros2 topic echo /rosout

# Cartographer 상태 확인
ros2 service list | grep cartographer
```

---

## 요약

### SLAM 맵 생성 워크플로우

1. **초기 설정** (한 번만)
   - LiDAR udev 규칙 설정
   - CycloneDDS 설정
   - 환경 변수 설정

2. **SLAM 실행**
   ```bash
   cd /home/seonil/slam_mapping
   ./scripts/create_slam_map.sh /dev/ttyUSB0
   ```

3. **맵핑**
   - LiDAR를 천천히 이동
   - RViz에서 실시간 확인

4. **맵 저장**
   ```bash
   ./scripts/save_map.sh <맵_이름>
   ```

5. **종료**
   - SLAM 터미널에서 `Ctrl+C`

---

**작성일**: 2026-01-28
**버전**: 1.0
**테스트 환경**: Ubuntu 22.04 + ROS2 Humble + YDLidar S2PRO
