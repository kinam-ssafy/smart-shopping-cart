#!/bin/bash

# 원격 RViz 설정 스크립트 (RC카 측)
# 사용법: ./setup_rc_car_for_remote.sh <노트북_IP>

if [ -z "$1" ]; then
    echo "사용법: $0 <노트북_IP>"
    echo "예시: $0 192.168.0.200"
    echo ""
    echo "노트북 IP 확인 방법:"
    echo "  - Linux/WSL2: hostname -I"
    echo "  - Windows PowerShell: ipconfig (WSL2의 경우 Windows 호스트 IP 사용)"
    exit 1
fi

LAPTOP_IP=$1

echo "===== RC카 원격 통신 설정 시작 ====="
echo "노트북 IP: $LAPTOP_IP"

# CycloneDDS 설정 디렉토리 생성
mkdir -p ~/cyclonedds

# CycloneDDS 설정 파일 생성
echo "CycloneDDS 설정 파일 생성 중..."
cat > ~/cyclonedds/config.xml << EOF
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
        <Peer address="$LAPTOP_IP"/>
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

echo "CycloneDDS 설정 완료: ~/cyclonedds/config.xml"

# 환경 변수 설정
echo "환경 변수 설정 중..."
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
export ROS_DOMAIN_ID=0
export CYCLONEDDS_URI=file://$HOME/cyclonedds/config.xml

# .bashrc에 추가 (이미 있는지 확인)
if ! grep -q "export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp" ~/.bashrc; then
    echo "" >> ~/.bashrc
    echo "# ROS2 원격 통신 설정" >> ~/.bashrc
    echo "export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp" >> ~/.bashrc
    echo "export ROS_DOMAIN_ID=0" >> ~/.bashrc
    echo "export CYCLONEDDS_URI=file://\$HOME/cyclonedds/config.xml" >> ~/.bashrc
    echo ".bashrc에 환경 변수 추가 완료"
fi

# ROS2 환경 소스
source /opt/ros/humble/setup.bash

echo ""
echo "===== 설정 완료 ====="
echo ""
echo "RC카 IP 주소: $(hostname -I | awk '{print $1}')"
echo ""
echo "다음 단계:"
echo "1. SLAM 실행:"
echo "   cd ~/Desktop/seon-il/S14P11A401/slam_mapping"
echo "   ./scripts/create_slam_map.sh /dev/ttyUSB0"
echo ""
echo "2. 다른 터미널에서 토픽 확인:"
echo "   ros2 topic list"
echo ""
echo "3. 노트북에서 토픽이 보이는지 확인"
echo ""
echo "문제 발생 시:"
echo "- 방화벽에서 포트 8000-8999 허용 확인"
echo "- 노트북과 RC카가 같은 네트워크인지 확인"
echo "- 노트북에서 ping $(hostname -I | awk '{print $1}') 로 연결 테스트"
echo ""
