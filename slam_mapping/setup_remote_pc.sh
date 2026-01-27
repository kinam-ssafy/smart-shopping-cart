#!/bin/bash

# 원격 PC용 포트 제한 환경 설정 스크립트
# 사용법: source setup_remote_pc.sh RC_CAR_IP

if [ -z "$1" ]; then
    echo "❌ 오류: RC 카의 IP 주소를 입력해주세요."
    echo "사용법: source setup_remote_pc.sh RC_CAR_IP"
    echo "예시: source setup_remote_pc.sh 192.168.0.100"
    return 1
fi

RC_CAR_IP=$1
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="$SCRIPT_DIR/cyclonedds_remote_pc.xml"

# IP 주소 업데이트
echo "🔧 원격 PC 설정 중..."
sed -i "s/RC_CAR_IP/$RC_CAR_IP/g" "$CONFIG_FILE"

# 환경 변수 설정
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
export ROS_DOMAIN_ID=0
export CYCLONEDDS_URI=file://$CONFIG_FILE

echo "✅ 원격 PC 설정 완료!"
echo ""
echo "📝 설정 내용:"
echo "  - RMW: $RMW_IMPLEMENTATION"
echo "  - ROS_DOMAIN_ID: $ROS_DOMAIN_ID"
echo "  - CycloneDDS 설정: $CYCLONEDDS_URI"
echo "  - RC Car: $RC_CAR_IP"
echo "  - 사용 포트: 8765"
echo ""
echo "🔍 토픽 확인:"
echo "  ros2 topic list"
echo ""
echo "🎨 RViz 실행:"
echo "  rviz2 -d $SCRIPT_DIR/rviz/slam.rviz"
