# 원격 RViz 가이드 (윈도우 노트북에서 RC카 SLAM 보기)

RC카(우분투)에서 실행 중인 SLAM을 윈도우 노트북의 RViz로 실시간 확인하는 방법입니다.

---

## 🎯 방법 1: WSL2 + RViz (권장) ⭐

### 1. RC카(우분투) 설정

```bash
# 1-1. RC카 IP 확인
hostname -I
# 예: 192.168.0.100 (메모해두기)

# 1-2. CycloneDDS 설정 (포트 8000-8999 사용)
mkdir -p ~/cyclonedds
cat > ~/cyclonedds/config.xml << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<CycloneDDS>
  <Domain>
    <General>
      <NetworkInterfaceAddress>auto</NetworkInterfaceAddress>
      <AllowMulticast>false</AllowMulticast>
    </General>
    <Discovery>
      <ParticipantIndex>auto</ParticipantIndex>
      <Peers>
        <Peer address="노트북_IP_주소"/>
      </Peers>
      <Ports>
        <Base>8000</Base>
        <DomainGain>100</DomainGain>
        <ParticipantGain>10</ParticipantGain>
      </Ports>
    </Discovery>
  </Domain>
</CycloneDDS>
EOF

# 노트북 IP를 실제 값으로 변경 (WSL2의 경우 Windows IP 사용)
# 노트북에서 PowerShell로 ipconfig 실행하여 확인
LAPTOP_IP="192.168.0.200"  # 노트북 IP로 변경
sed -i "s/노트북_IP_주소/$LAPTOP_IP/g" ~/cyclonedds/config.xml

# 환경 변수 설정
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
export ROS_DOMAIN_ID=0
export CYCLONEDDS_URI=file://$HOME/cyclonedds/config.xml

# 1-3. SLAM 실행 (RViz 비활성화 상태)
cd ~/Desktop/seon-il/S14P11A401/slam_mapping
./scripts/create_slam_map.sh /dev/ttyUSB0

# 1-4. 토픽 확인
# 다른 터미널에서
ros2 topic list
# /scan, /map, /tf, /tf_static 등이 보여야 함
```

### 2. 윈도우 노트북 설정

#### 2-1. WSL2 Ubuntu 설치 (처음 한 번만)

PowerShell을 **관리자 권한**으로 실행:

```powershell
# WSL 설치 (Windows 10 버전 2004 이상 또는 Windows 11)
wsl --install -d Ubuntu-22.04

# 재부팅 후 Ubuntu 실행
# 사용자명/비밀번호 설정
```

#### 2-2. WSL2에서 ROS2 설치 (처음 한 번만)

WSL2 Ubuntu 터미널에서:

```bash
# 시스템 업데이트
sudo apt update && sudo apt upgrade -y

# ROS2 Humble 설치
sudo apt install software-properties-common
sudo add-apt-repository universe
sudo apt update

sudo apt install curl -y
sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key -o /usr/share/keyrings/ros-archive-keyring.gpg

echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu $(. /etc/os-release && echo $UBUNTU_CODENAME) main" | sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null

sudo apt update
sudo apt install -y ros-humble-rviz2 ros-humble-rmw-cyclonedds-cpp

# X11 디스플레이 확인 (Windows 11은 WSLg 내장)
echo $DISPLAY  # :0 또는 :0.0 이 나와야 함
```

**Windows 10 사용자**: X11 서버 필요 ([VcXsrv](https://sourceforge.net/projects/vcxsrv/) 설치)

#### 2-3. CycloneDDS 설정 (네트워크 통신용 - 포트 8000-8999 사용)

WSL2 Ubuntu에서:

```bash
# 설정 디렉토리 생성
mkdir -p ~/cyclonedds

# 설정 파일 생성 (포트 8000-8999 범위 사용, 8080 제외)
cat > ~/cyclonedds/config.xml << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<CycloneDDS>
  <Domain>
    <General>
      <NetworkInterfaceAddress>auto</NetworkInterfaceAddress>
      <AllowMulticast>false</AllowMulticast>
    </General>
    <Discovery>
      <ParticipantIndex>auto</ParticipantIndex>
      <Peers>
        <Peer address="RC카_IP_주소"/>
      </Peers>
      <Ports>
        <Base>8000</Base>
        <DomainGain>100</DomainGain>
        <ParticipantGain>10</ParticipantGain>
      </Ports>
    </Discovery>
  </Domain>
</CycloneDDS>
EOF

# RC카 IP 주소를 실제 값으로 변경 (예: 192.168.0.100)
RC_CAR_IP="192.168.0.100"  # RC카 IP로 변경
sed -i "s/RC카_IP_주소/$RC_CAR_IP/g" ~/cyclonedds/config.xml

# 환경 변수 설정
echo 'source /opt/ros/humble/setup.bash' >> ~/.bashrc
echo 'export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp' >> ~/.bashrc
echo 'export ROS_DOMAIN_ID=0' >> ~/.bashrc
echo 'export CYCLONEDDS_URI=file://$HOME/cyclonedds/config.xml' >> ~/.bashrc

# 적용
source ~/.bashrc
```

### 3. RViz 실행 및 SLAM 확인

#### 3-1. 토픽 확인 (먼저 테스트)

WSL2 Ubuntu에서:

```bash
# 토픽 리스트 확인
ros2 topic list

# /scan, /map, /tf, /tf_static 등이 보이면 성공!
# 안 보이면 아래 "문제 해결" 참고

# 스캔 데이터 확인
ros2 topic echo /scan --once

# 맵 데이터 확인
ros2 topic echo /map --once
```

#### 3-2. RViz 설정 파일 다운로드

```bash
# RC카에서 설정 파일 복사 (RC카 IP를 192.168.0.100으로 가정)
scp ssafy@192.168.0.100:~/Desktop/seon-il/S14P11A401/slam_mapping/rviz/slam.rviz ~/slam.rviz
```

#### 3-3. RViz 실행

```bash
# 설정 파일과 함께 실행
rviz2 -d ~/slam.rviz
```

**RViz에서 확인할 수 있는 것들**:
- 🟢 **LaserScan**: 현재 LiDAR 스캔 데이터 (녹색 점들)
- 🗺️ **Map**: 생성 중인 맵 (흑백 그리드)
- 📍 **TF**: 로봇의 위치와 좌표계
- 🔴 **Trajectory**: 로봇이 이동한 경로 (빨간 선)

---

## 🎯 방법 2: rosbridge + 웹 Visualizer (포트 8765 사용)

네트워크가 복잡하거나 WSL2가 안 될 때 사용합니다.

### 1. RC카에서 rosbridge 설치 및 실행

```bash
# rosbridge 설치 (처음 한 번만)
sudo apt install ros-humble-rosbridge-suite

# SLAM 실행 (터미널 1)
cd ~/Desktop/seon-il/S14P11A401/slam_mapping
./scripts/create_slam_map.sh /dev/ttyUSB0

# rosbridge 실행 (터미널 2)
source /opt/ros/humble/setup.bash
ros2 launch rosbridge_server rosbridge_websocket_launch.xml port:=8765

# "Rosbridge WebSocket server started on port 8765" 메시지 확인
```

### 2. 포트 포워딩 또는 직접 연결

**옵션 A: 같은 네트워크인 경우 (RC카 IP 직접 접근 가능)**

```bash
# RC카 IP 확인
hostname -I  # 예: 192.168.0.100

# 노트북에서 http://192.168.0.100:8765 로 직접 연결
```

**옵션 B: SSH 터널링 사용**

PowerShell에서:

```powershell
# RC카로 SSH 연결 + 포트 포워딩 (RC카 IP: 192.168.0.100)
ssh -L 8765:localhost:8765 ssafy@192.168.0.100

# 연결 상태 유지 (종료하지 말 것)
```

### 3. Foxglove Studio 사용

1. [Foxglove Studio 다운로드](https://foxglove.dev/download) (무료)
2. 설치 후 실행
3. "Open connection" → "Rosbridge (ROS 1 & 2)"
4. WebSocket URL: `ws://localhost:8765`
5. "Open" 클릭

**Foxglove에서 패널 추가**:
- "Add panel" → "3D" → `/scan`, `/map` 토픽 추가
- "Add panel" → "Image" → 카메라 있으면 추가
- "Add panel" → "Plot" → 데이터 시각화

---

## 🔧 문제 해결

### ❌ `ros2 topic list`에서 토픽이 안 보임

**원인**: RC카와 노트북이 서로 ROS2 메시지를 주고받지 못함

**해결**:

```bash
# WSL2 Ubuntu에서

# 1. 방화벽 확인 (Windows)
# Windows Defender 방화벽에서 포트 8000-8999 UDP/TCP 허용
# 제어판 → Windows Defender 방화벽 → 고급 설정 → 인바운드 규칙 → 새 규칙
# 포트 → TCP, UDP → 특정 로컬 포트: 8000-8999 → 연결 허용

# 2. 같은 네트워크 확인
ping <RC카_IP>  # RC카 IP로 변경 (예: 192.168.0.100)

# 3. ROS_DOMAIN_ID 확인
echo $ROS_DOMAIN_ID  # RC카와 동일해야 함 (기본값: 0)

# 4. CycloneDDS 설정 확인
cat ~/cyclonedds/config.xml
# Peer address가 RC카 IP로 올바르게 설정되어 있는지 확인

# 5. CycloneDDS 환경 변수 재설정
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
export ROS_DOMAIN_ID=0
export CYCLONEDDS_URI=file://$HOME/cyclonedds/config.xml

# 6. 포트 사용 확인
netstat -an | grep 800  # 8000번대 포트가 열려 있는지 확인
```

### ❌ RViz가 실행되지 않음 (WSL2)

**원인**: X11 디스플레이 문제

**해결**:

```bash
# DISPLAY 환경변수 확인
echo $DISPLAY  # :0 또는 :0.0 이어야 함

# Windows 10: VcXsrv 실행 필요
# 1. VcXsrv 다운로드: https://sourceforge.net/projects/vcxsrv/
# 2. 설치 후 XLaunch 실행
# 3. "Multiple windows" → "Start no client" → "Disable access control" 체크
# 4. WSL2에서:
export DISPLAY=$(cat /etc/resolv.conf | grep nameserver | awk '{print $2}'):0

# Windows 11: WSLg 기본 지원
# 업데이트 확인
wsl --update
wsl --shutdown
# WSL 재시작
```

### ❌ RViz에서 TF 에러

**원인**: 시간 동기화 문제

**해결**:

```bash
# RC카와 노트북의 시간 동기화
# RC카에서
sudo timedatectl set-ntp true
date

# WSL2에서
sudo apt install ntpdate
sudo ntpdate ntp.ubuntu.com
date
```

### ❌ 맵이 보이지 않음

**원인**: RC카를 움직이지 않아서 맵이 생성되지 않음

**해결**:
- RC카를 **천천히** 움직이세요
- 최소 10초 이상 이동해야 맵이 생성되기 시작합니다
- RViz에서 `/scan` 토픽 데이터가 업데이트되는지 확인

---

## 📊 성능 체크리스트

### RC카 확인

```bash
# 토픽 발행 확인
ros2 topic hz /scan
# average rate: ~10.000 (10Hz 정도면 정상)

ros2 topic hz /map
# average rate: ~3.000 (3Hz 정도면 정상)

# CPU 사용률
top
# cartographer_node: 50-80% 정상
```

### WSL2 노트북 확인

```bash
# 토픽 수신 확인
ros2 topic hz /scan
# RC카와 동일한 Hz가 나와야 함

# 네트워크 지연
ros2 topic echo /scan --field header.stamp
# 시간이 최신이어야 함 (1-2초 이상 지연되면 문제)
```

---

## 💡 팁

### 네트워크 최적화

1. **같은 WiFi 사용**: 5GHz WiFi 권장 (2.4GHz보다 빠름)
2. **라우터 가까이**: WiFi 신호 강도 -50dBm 이상 유지
3. **유선 연결**: 가능하면 RC카를 이더넷으로 연결 (가장 안정적)

### RViz 사용 팁

1. **Fixed Frame**: `map`으로 설정
2. **LaserScan Decay Time**: 0 (최신 데이터만 표시)
3. **Map Alpha**: 0.8 (투명도 조절로 LaserScan과 함께 보기)
4. **Grid 크기**: Cell Size 1m로 설정

### 저장 및 공유

```bash
# RC카에서 맵 저장
cd ~/Desktop/seon-il/S14P11A401/slam_mapping
./scripts/save_map.sh my_first_map

# 노트북으로 맵 파일 다운로드
scp ssafy@192.168.0.100:~/Desktop/seon-il/S14P11A401/slam_mapping/maps/my_first_map.* ./
```

---

## 📞 추가 도움

- ROS2 DDS 문제: https://docs.ros.org/en/humble/Concepts/About-Different-Middleware-Vendors.html
- WSL2 GUI: https://learn.microsoft.com/en-us/windows/wsl/tutorials/gui-apps
- Foxglove 사용법: https://foxglove.dev/docs

---

**버전**: 1.0.0  
**최종 업데이트**: 2026-01-27  
**테스트 환경**: Windows 11 + WSL2 Ubuntu 22.04 + ROS2 Humble
