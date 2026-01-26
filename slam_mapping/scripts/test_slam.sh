#!/bin/bash
# ============================================
# SLAM 매핑 테스트 (노트북 + YDLidar X4-Pro)
# ============================================
#
# 사용법:
#   1. YDLidar를 노트북 USB에 연결
#   2. ./scripts/test_slam.sh 실행
#   3. RViz에서 맵 생성 확인
#   4. LiDAR를 손에 들고 방 안을 돌아다님
#   5. 맵이 완성되면 다른 터미널에서:
#      ./scripts/save_map.sh
#
# ============================================

set -e

# Dynamic path resolution
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "============================================"
echo "   YDLidar Cartographer SLAM Test"
echo "============================================"

# LiDAR 포트 확인
LIDAR_PORT="/dev/ttyUSB0"
if [ ! -e "$LIDAR_PORT" ]; then
    echo "Checking USB devices..."
    ls -la /dev/ttyUSB* 2>/dev/null || echo "No ttyUSB devices"
    echo ""
    read -p "LiDAR port (default: /dev/ttyUSB0): " USER_PORT
    LIDAR_PORT="${USER_PORT:-/dev/ttyUSB0}"
fi

# 권한 설정
if [ -e "$LIDAR_PORT" ]; then
    sudo chmod 666 "$LIDAR_PORT"
    echo "LiDAR port: $LIDAR_PORT"
else
    echo "Error: LiDAR not found"
    exit 1
fi

echo ""
echo "Starting SLAM..."
echo "  - YDLidar Driver"
echo "  - Cartographer SLAM"
echo "  - RViz Visualization"
echo ""
echo "============================================"
echo "  Move LiDAR around to build the map!"
echo "  Save map: ./scripts/save_map.sh"
echo "============================================"
echo ""

# ROS2 환경
source /opt/ros/humble/setup.bash

# 패키지 빌드 확인
if [ -f ~/ros2_ws/install/setup.bash ]; then
    source ~/ros2_ws/install/setup.bash
    echo "Using built package"
else
    echo "Package not built. Building now..."
    cd ~/ros2_ws
    colcon build --packages-select slam_mapping2
    source install/setup.bash
fi

# Launch
ros2 launch slam_mapping2 slam_mapping.launch.py port:="$LIDAR_PORT"

