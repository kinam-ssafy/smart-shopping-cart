#!/bin/bash

# RC Car용 포트 제한 환경 설정 스크립트
# 사용법: source setup_rc_car.sh REMOTE_PC_IP

if [ -z "$1" ]; then
    echo "❌ 오류: 원격 PC의 IP 주소를 입력해주세요."
    echo "사용법: source setup_rc_car.sh REMOTE_PC_IP"
    echo "예시: source setup_rc_car.sh 192.168.0.200"
    return 1
fi

REMOTE_PC_IP=$1
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="$SCRIPT_DIR/cyclonedds_rc_car.xml"

# IP 주소 업데이트
echo "🔧 RC Car 설정 중..."
sed -i "s/REMOTE_PC_IP/$REMOTE_PC_IP/g" "$CONFIG_FILE"

# 환경 변수 설정
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
export ROS_DOMAIN_ID=0
export CYCLONEDDS_URI=file://$CONFIG_FILE

echo "✅ RC Car 설정 완료!"
echo ""
echo "📝 설정 내용:"
echo "  - RMW: $RMW_IMPLEMENTATION"
echo "  - ROS_DOMAIN_ID: $ROS_DOMAIN_ID"
echo "  - CycloneDDS 설정: $CYCLONEDDS_URI"
echo "  - 원격 PC: $REMOTE_PC_IP"
echo "  - 사용 포트: 8765"
echo ""
echo "🚀 이제 SLAM을 시작할 수 있습니다:"
echo "  ./scripts/create_slam_map.sh /dev/ttyUSB0"
