#!/bin/bash
# ============================================
# 패키지 빌드 스크립트
# ============================================

set -e

# Dynamic path resolution
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "============================================"
echo "   Building slam_mapping2 package"
echo "============================================"

# ROS2 환경
source /opt/ros/humble/setup.bash

# 패키지를 워크스페이스로 복사
mkdir -p ~/ros2_ws/src
if [ ! -L ~/ros2_ws/src/slam_mapping2 ]; then
    ln -sf "$PROJECT_DIR" ~/ros2_ws/src/slam_mapping2
    echo "Created symlink to package"
fi

# 빌드
cd ~/ros2_ws
colcon build --packages-select slam_mapping2 --symlink-install

echo ""
echo "============================================"
echo "  Build complete!"
echo "  Run: source ~/ros2_ws/install/setup.bash"
echo "============================================"

