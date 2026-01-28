# 원격 SLAM 시각화 가이드

RC카(Jetson Nano)에서 SLAM을 실행하고 원격 PC에서 RViz로 실시간 시각화하는 가이드입니다.

## 목차
1. [네트워크 구성](#네트워크-구성)
2. [RC카 설정](#rc카-설정)
3. [원격 PC 설정](#원격-pc-설정)
4. [SLAM 실행 및 시각화](#slam-실행-및-시각화)
5. [문제 해결](#문제-해결)

---

## 네트워크 구성

### 환경
- **RC카 (Jetson Nano)**: 70.12.247.62
- **원격 PC (노트북)**: 70.12.246.46
- **사용 가능 포트**: 8700-8999
- **DDS**: CycloneDDS
- **ROS2**: Humble

### 통신 구조
```
RC카 (70.12.247.62)                    원격 PC (70.12.246.46)
├─ YDLidar Node                        ├─ RViz2
├─ Cartographer Node                   └─ (토픽 구독)
├─ Occupancy Grid Node
└─ 토픽 발행 (/scan, /map, /tf)
        │
        └──────── CycloneDDS ─────────>
              (포트: 8700-8999)
```

---

## RC카 설정

### 1. 프로젝트 클론

```bash
cd /home/seonil/S14P11A401
git clone <repository_url> slam_mapping
cd slam_mapping
```

### 2. CycloneDDS 설정 (RC카용)

`~/cyclonedds/cyclonedds_rc_car.xml` 파일 생성:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CycloneDDS>
  <Domain>
    <Id>0</Id>
    <General>
      <AllowMulticast>false</AllowMulticast>
      <NetworkInterfaceAddress>70.12.247.62</NetworkInterfaceAddress>
    </General>
    <Discovery>
      <ParticipantIndex>auto</ParticipantIndex>
      <MaxAutoParticipantIndex>100</MaxAutoParticipantIndex>
      <Peers>
        <Peer address="70.12.246.46"/>
        <Peer address="localhost"/>
      </Peers>
    </Discovery>
    <Internal>
      <MaxMessageSize>65500</MaxMessageSize>
      <SocketReceiveBufferSize>10MB</SocketReceiveBufferSize>
    </Internal>
    <Tracing>
      <Verbosity>warning</Verbosity>
    </Tracing>
  </Domain>
</CycloneDDS>
```

**주요 설정:**
- `AllowMulticast: false` - 멀티캐스트 비활성화 (유니캐스트만 사용)
- `NetworkInterfaceAddress: 70.12.247.62` - RC카 IP 명시
- `Peer: 70.12.246.46` - 원격 PC IP 등록
- `localhost` - RC카 내부 통신 지원

### 3. 환경 변수 설정

RC카의 `~/.bashrc`에 추가:

```bash
# ROS2 환경
source /opt/ros/humble/setup.bash

# CycloneDDS 설정 (RC카용)
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
export CYCLONEDDS_URI=file://$HOME/cyclonedds/cyclonedds_rc_car.xml
export ROS_DOMAIN_ID=0

# 네트워크 설정
export ROS_LOCALHOST_ONLY=0
```

적용:
```bash
source ~/.bashrc
```

### 4. LiDAR 포트 권한 설정

```bash
# 영구 설정 (권장)
echo 'KERNEL=="ttyUSB*", ATTRS{idVendor}=="10c4", ATTRS{idProduct}=="ea60", MODE="0666", GROUP="dialout"' | sudo tee /etc/udev/rules.d/99-ydlidar.rules

sudo udevadm control --reload-rules
sudo udevadm trigger

# 또는 임시 설정
sudo chmod 666 /dev/ttyUSB0
```

### 5. RViz 비활성화

RC카에는 디스플레이가 없으므로 RViz를 비활성화합니다.

`scripts/create_slam_map.sh` 수정:

```bash
# 4. RViz (원격 연결용으로 비활성화)
echo "[4/4] RViz disabled (use remote RViz from laptop)"
# echo "[4/4] Starting RViz..."
# rviz2 -d "$PROJECT_DIR/rviz/slam.rviz" &
# RVIZ_PID=$!
```

그리고 cleanup 함수에서도 주석 처리:

```bash
cleanup() {
    echo ""
    echo "Stopping all nodes..."
    # kill $RVIZ_PID 2>/dev/null
    kill $GRID_PID 2>/dev/null
    kill $CARTO_PID 2>/dev/null
    kill $LIDAR_PID 2>/dev/null
    wait 2>/dev/null
    echo "Done."
}
```

---

## 원격 PC 설정

### 1. ROS2 및 Cartographer 설치

```bash
# ROS2 Humble 설치 (Ubuntu 22.04)
sudo apt update
sudo apt install ros-humble-desktop

# Cartographer 설치
sudo apt install ros-humble-cartographer ros-humble-cartographer-ros

# CycloneDDS 설치
sudo apt install ros-humble-rmw-cyclonedds-cpp
```

### 2. CycloneDDS 설정 (원격 PC용)

`~/cyclonedds/cyclonedds_remote_pc.xml` 파일 생성:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CycloneDDS>
  <Domain>
    <Id>0</Id>
    <General>
      <AllowMulticast>false</AllowMulticast>
      <NetworkInterfaceAddress>70.12.246.46</NetworkInterfaceAddress>
    </General>
    <Discovery>
      <ParticipantIndex>auto</ParticipantIndex>
      <MaxAutoParticipantIndex>100</MaxAutoParticipantIndex>
      <Peers>
        <Peer address="70.12.247.62"/>
        <Peer address="localhost"/>
      </Peers>
    </Discovery>
    <Internal>
      <MaxMessageSize>65500</MaxMessageSize>
      <SocketReceiveBufferSize>10MB</SocketReceiveBufferSize>
    </Internal>
    <Tracing>
      <Verbosity>warning</Verbosity>
    </Tracing>
  </Domain>
</CycloneDDS>
```

**주요 설정:**
- `AllowMulticast: false` - 멀티캐스트 비활성화
- `NetworkInterfaceAddress: 70.12.246.46` - 원격 PC IP 명시
- `Peer: 70.12.247.62` - RC카 IP 등록

### 3. 환경 변수 설정

원격 PC의 `~/.bashrc`에 추가:

```bash
# ROS2 환경
source /opt/ros/humble/setup.bash

# CycloneDDS 설정 (원격 PC용)
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
export CYCLONEDDS_URI=file://$HOME/cyclonedds/cyclonedds_remote_pc.xml
export ROS_DOMAIN_ID=0

# 네트워크 설정
export ROS_LOCALHOST_ONLY=0
```

적용:
```bash
source ~/.bashrc
```

### 4. RViz 설정 파일 복사

RC카에서 RViz 설정 파일을 원격 PC로 복사:

```bash
# 원격 PC에서 실행
mkdir -p ~/slam_mapping/rviz
scp seonil@70.12.247.62:/home/seonil/S14P11A401/slam_mapping/rviz/slam.rviz ~/slam_mapping/rviz/
```

### 5. 방화벽 설정 (필요시)

```bash
# 원격 PC에서 포트 허용
sudo ufw allow 8700:8999/udp
sudo ufw allow 8700:8999/tcp

# RC카에서도 동일하게 실행
```

---

## SLAM 실행 및 시각화

### 1. RC카에서 SLAM 실행

**터미널 1: SLAM 실행**
```bash
cd /home/seonil/S14P11A401/slam_mapping
./scripts/create_slam_map.sh /dev/ttyUSB0
```

**터미널 2: RC카 조종 (동시 실행)**
```bash
cd /home/seonil/S14P11A401/slam_mapping
python3 control_car.py
```

**출력 확인:**
```
[INFO] [ydlidar_simple_node]: YDLidar ready on /dev/ttyUSB0
[INFO] [ydlidar_simple_node]: Scans: 100, Points: 1191
[INFO] [cartographer logger]: Added trajectory with ID '0'
[4/4] RViz disabled (use remote RViz from laptop)
```

### 2. 원격 PC에서 토픽 확인

**새 터미널에서:**
```bash
# 환경 변수 확인
echo $RMW_IMPLEMENTATION
echo $CYCLONEDDS_URI

# 토픽 리스트 확인 (RC카의 토픽이 보여야 함)
ros2 topic list

# 스캔 데이터 확인
ros2 topic hz /scan
ros2 topic echo /scan --once

# 노드 리스트 확인
ros2 node list
```

**예상 출력:**
```
/scan
/tf
/tf_static
/map
/trajectory_node_list
/constraint_list
/robot_marker
/tracked_pose
```

### 3. 원격 PC에서 RViz 실행

```bash
rviz2 -d ~/slam_mapping/rviz/slam.rviz
```

**RViz에서 보이는 내용:**
- **LaserScan (밝은 녹색)**: RC카 LiDAR의 실시간 스캔 데이터
- **Map (회색)**: Cartographer가 생성하는 2D 맵
- **TF**: RC카의 좌표계 (map → odom → base_link → laser)
- **Trajectory (빨간색)**: RC카의 이동 경로
- **Robot Marker (파란 원)**: RC카의 위치

### 4. RC카 조종하며 맵 생성

- RC카를 천천히 이동시키며 맵 생성
- 원격 PC의 RViz에서 실시간으로 맵이 업데이트되는 것을 확인
- 같은 영역을 여러 번 지나가면 루프 클로저가 발생하여 맵 정확도 향상

### 5. 맵 저장

맵핑이 완료되면 **RC카에서** 새 터미널을 열고:

```bash
cd /home/seonil/S14P11A401/slam_mapping
./scripts/save_map.sh <맵_이름>
```

예시:
```bash
./scripts/save_map.sh indoor_map_01
```

저장된 맵:
```
maps/indoor_map_01.pgm
maps/indoor_map_01.yaml
```

---

## 네트워크 진단

### 연결 테스트

#### 1. Ping 테스트
```bash
# RC카에서 원격 PC로
ping -c 4 70.12.246.46

# 원격 PC에서 RC카로
ping -c 4 70.12.247.62
```

#### 2. 포트 테스트

**RC카에서:**
```bash
# 네트워크 인터페이스 확인
ip addr show

# 열려있는 포트 확인
sudo netstat -tuln | grep 87
```

#### 3. CycloneDDS 통신 확인

**RC카에서:**
```bash
# DDS 디스커버리 로그 확인
export CYCLONEDDS_VERBOSITY=trace
ros2 topic list
```

**원격 PC에서:**
```bash
# DDS 디스커버리 로그 확인
export CYCLONEDDS_VERBOSITY=trace
ros2 topic list
```

정상이면 peer discovery 로그가 출력됩니다.

---

## 문제 해결

### 1. 원격 PC에서 토픽이 안 보임

**증상:**
```bash
ros2 topic list
# /parameter_events
# /rosout  (RC카 토픽이 안 보임)
```

**원인 및 해결:**

#### 원인 1: CycloneDDS 설정 오류
```bash
# 설정 파일 확인
cat ~/cyclonedds/cyclonedds_remote_pc.xml

# 확인 사항:
# - NetworkInterfaceAddress: 70.12.246.46
# - Peer: 70.12.247.62
# - AllowMulticast: false
```

#### 원인 2: 환경 변수 미설정
```bash
# 환경 변수 확인
env | grep -E "RMW|CYCLONE|ROS_DOMAIN"

# 출력되어야 할 내용:
# RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
# CYCLONEDDS_URI=file:///home/.../cyclonedds_remote_pc.xml
# ROS_DOMAIN_ID=0
# ROS_LOCALHOST_ONLY=0
```

#### 원인 3: 방화벽 차단
```bash
# 방화벽 상태 확인
sudo ufw status

# 포트 허용
sudo ufw allow 8700:8999/udp
sudo ufw allow 8700:8999/tcp

# 또는 방화벽 임시 비활성화 (테스트용)
sudo ufw disable
```

#### 원인 4: 네트워크 문제
```bash
# ping 테스트
ping -c 4 70.12.247.62

# traceroute
traceroute 70.12.247.62
```

### 2. RViz에서 맵이 안 보임

**증상:** RViz는 실행되지만 맵이나 스캔이 표시되지 않음

**해결:**

#### 확인 1: Fixed Frame
RViz 좌측 상단 `Global Options` → `Fixed Frame`을 `map`으로 설정

#### 확인 2: 토픽 구독 상태
RViz 좌측 패널에서 각 Display의 `Topic` 확인:
- LaserScan → `/scan`
- Map → `/map`
- TF → 활성화

#### 확인 3: QoS 설정
일부 토픽은 QoS가 맞지 않으면 수신되지 않습니다.

RViz 설정에서:
- `/scan`: Best Effort
- `/map`: Reliable

### 3. 데이터 전송이 느림

**증상:** RViz에서 맵 업데이트가 느리거나 끊김

**해결:**

#### 해결 1: 네트워크 대역폭 확인
```bash
# iperf3로 대역폭 테스트
# RC카에서
iperf3 -s

# 원격 PC에서
iperf3 -c 70.12.247.62 -t 10
```

#### 해결 2: CycloneDDS 버퍼 크기 증가
`cyclonedds_*.xml` 파일에서:
```xml
<Internal>
  <MaxMessageSize>65500</MaxMessageSize>
  <SocketReceiveBufferSize>10MB</SocketReceiveBufferSize>
  <SocketSendBufferSize>10MB</SocketSendBufferSize>
</Internal>
```

#### 해결 3: 스캔 데이터 다운샘플링
`slam_mapping2/ydlidar_simple_node.py`에서:
```python
# 현재: max_points = 720
max_points = 360  # 절반으로 줄이기
```

### 4. RC카와 원격 PC의 ROS_DOMAIN_ID 불일치

**확인:**
```bash
# RC카에서
echo $ROS_DOMAIN_ID

# 원격 PC에서
echo $ROS_DOMAIN_ID
```

**둘 다 `0`이어야 합니다.**

### 5. 시간 동기화 문제

**증상:** TF 타임스탬프 에러

**해결:**
```bash
# 시간 동기화 (NTP)
sudo apt install ntp
sudo systemctl start ntp
sudo systemctl enable ntp

# 시간 확인
date
```

RC카와 원격 PC의 시스템 시간이 일치해야 합니다.

---

## 최적화 팁

### 1. 네트워크 최적화

- **WiFi 5GHz 사용**: 2.4GHz보다 빠르고 간섭이 적음
- **라우터 QoS 설정**: RC카와 원격 PC에 높은 우선순위 부여
- **유선 연결**: 가능하면 이더넷 케이블 사용

### 2. CycloneDDS 최적화

```xml
<!-- Fast Path 활성화 -->
<General>
  <Transport>
    <Default>udp</Default>
  </Transport>
</General>

<!-- 불필요한 디스커버리 제한 -->
<Discovery>
  <EnableTopicDiscoveryEndpoints>false</EnableTopicDiscoveryEndpoints>
</Discovery>
```

### 3. RViz 최적화

- 불필요한 Display 비활성화
- `Update Interval` 조정 (TF: 0.1초)
- `Queue Size` 감소 (LaserScan: 1~5)

---

## 빠른 시작 체크리스트

### RC카 (Jetson Nano)
- [ ] CycloneDDS 설정 파일 생성 (`cyclonedds_rc_car.xml`)
- [ ] 환경 변수 설정 (`~/.bashrc`)
- [ ] LiDAR 포트 권한 설정
- [ ] `create_slam_map.sh`에서 RViz 비활성화
- [ ] SLAM 실행: `./scripts/create_slam_map.sh /dev/ttyUSB0`
- [ ] RC카 조종: `python3 control_car.py`

### 원격 PC
- [ ] ROS2 Humble + Cartographer 설치
- [ ] CycloneDDS 설정 파일 생성 (`cyclonedds_remote_pc.xml`)
- [ ] 환경 변수 설정 (`~/.bashrc`)
- [ ] RViz 설정 파일 복사
- [ ] 토픽 확인: `ros2 topic list`
- [ ] RViz 실행: `rviz2 -d ~/slam_mapping/rviz/slam.rviz`

---

## 요약

### 핵심 설정

**RC카 (70.12.247.62)**
- CycloneDDS: Peer에 `70.12.246.46` 추가
- RViz: 비활성화
- 실행: SLAM + 차량 조종

**원격 PC (70.12.246.46)**
- CycloneDDS: Peer에 `70.12.247.62` 추가
- RViz: 토픽 구독 및 시각화

**통신**
- 포트: 8700-8999 (UDP/TCP)
- DDS: CycloneDDS (유니캐스트)
- Discovery: Peer-to-Peer

---

**작성일**: 2026-01-28
**버전**: 1.0
**테스트 환경**: RC카 (Jetson Nano) + 원격 PC (Ubuntu 22.04) + ROS2 Humble
