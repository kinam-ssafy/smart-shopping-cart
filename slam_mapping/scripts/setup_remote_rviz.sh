#!/bin/bash

# 원격 RViz 설정 스크립트 (PC 측)
# 사용법: ./setup_remote_rviz.sh <RC카_IP>

if [ -z "$1" ]; then
    echo "사용법: $0 <RC카_IP>"
    echo "예시: $0 192.168.0.100"
    exit 1
fi

RC_CAR_IP=$1

echo "===== 원격 RViz 설정 시작 ====="
echo "RC카 IP: $RC_CAR_IP"

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
        <Peer address="$RC_CAR_IP"/>
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
if [ -f /opt/ros/humble/setup.bash ]; then
    source /opt/ros/humble/setup.bash
    echo "ROS2 Humble 환경 로드 완료"
else
    echo "경고: ROS2 Humble이 설치되어 있지 않습니다."
    echo "설치: sudo apt install ros-humble-rviz2 ros-humble-rmw-cyclonedds-cpp"
fi

echo ""
echo "===== 설정 완료 ====="
echo ""
echo "다음 단계:"
echo "1. RC카에서 SLAM 실행:"
echo "   cd ~/Desktop/seon-il/S14P11A401/slam_mapping"
echo "   ./scripts/create_slam_map.sh /dev/ttyUSB0"
echo ""
echo "2. 현재 터미널에서 토픽 확인:"
echo "   ros2 topic list"
echo "   ros2 topic echo /scan --once"
echo ""
echo "3. RViz 실행:"
echo "   rviz2"
echo ""
echo "문제 발생 시:"
echo "- 방화벽에서 포트 8000-8999 허용 확인"
echo "- RC카와 PC가 같은 네트워크인지 확인"
echo "- ping $RC_CAR_IP 로 연결 테스트"
echo ""
