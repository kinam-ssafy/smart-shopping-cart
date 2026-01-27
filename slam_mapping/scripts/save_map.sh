#!/bin/bash
# ============================================
# 맵 저장 스크립트
# ============================================

set -e

# Dynamic path resolution
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
SAVE_DIR="$PROJECT_DIR/maps"

MAP_NAME="${1:-map_$(date +%Y%m%d_%H%M%S)}"

echo "============================================"
echo "   Saving Map: $MAP_NAME"
echo "============================================"

# ROS2 환경
source /opt/ros/humble/setup.bash
if [ -f ~/ros2_ws/install/setup.bash ]; then
    source ~/ros2_ws/install/setup.bash
fi

# 디렉토리 생성
mkdir -p "$SAVE_DIR"

# 맵 저장
echo "Saving to: $SAVE_DIR/$MAP_NAME"
ros2 run nav2_map_server map_saver_cli -f "$SAVE_DIR/$MAP_NAME"

echo ""
echo "============================================"
echo "  Map saved!"
echo "  Files:"
echo "    - $SAVE_DIR/$MAP_NAME.pgm"
echo "    - $SAVE_DIR/$MAP_NAME.yaml"
echo "============================================"

