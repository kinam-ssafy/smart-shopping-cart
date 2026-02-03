#!/bin/bash
# ============================================
# SLAM 직접 실행 (빌드 없이)
# TF 동기화 문제 해결 버전
# ============================================

set -e

# Dynamic path resolution
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

LIDAR_PORT="${1:-/dev/ttyUSB0}"

echo "============================================"
echo "   YDLidar Cartographer SLAM (Direct Run)"
echo "============================================"

# 포트 권한
if [ -e "$LIDAR_PORT" ]; then
    sudo chmod 666 "$LIDAR_PORT"
    echo "LiDAR port: $LIDAR_PORT"
else
    echo "Warning: LiDAR not found at $LIDAR_PORT"
    echo "Checking available ports..."
    ls -la /dev/ttyUSB* 2>/dev/null || echo "No ttyUSB devices"
fi

# ROS2 환경
source /opt/ros/humble/setup.bash

echo ""
echo "Starting nodes in order..."
echo ""

# 1. YDLidar Node (ROS2 노드로 실행)
echo "[1/4] Starting YDLidar node..."
ros2 run rccar_nodes ydlidar_node --ros-args -p port:="$LIDAR_PORT" &
LIDAR_PID=$!
sleep 3

# TF 확인
echo "Checking TF..."
ros2 topic echo /tf --once 2>/dev/null && echo "TF OK" || echo "TF not yet"

# 2. Cartographer Node
echo "[2/4] Starting Cartographer..."
ros2 run cartographer_ros cartographer_node \
    -configuration_directory "$PROJECT_DIR/config" \
    -configuration_basename ydlidar_2d.lua &
CARTO_PID=$!
sleep 3

# 3. Occupancy Grid Node
echo "[3/4] Starting Occupancy Grid..."
ros2 run cartographer_ros cartographer_occupancy_grid_node \
    --ros-args -p resolution:=0.05 -p publish_period_sec:=1.0 &
GRID_PID=$!
sleep 1

# 4. RViz
echo "[4/4] Starting RViz..."
rviz2 -d "$PROJECT_DIR/rviz/slam.rviz" &
RVIZ_PID=$!

echo ""
echo "============================================"
echo "  All nodes started!"
echo ""
echo "  TF Tree: odom -> base_footprint -> base_link -> laser"
echo ""
echo "  Move LiDAR around to build map"
echo "  Press Ctrl+C to stop"
echo "============================================"

# 종료 처리
cleanup() {
    echo ""
    echo "Stopping all nodes..."
    kill $RVIZ_PID 2>/dev/null
    kill $GRID_PID 2>/dev/null
    kill $CARTO_PID 2>/dev/null
    kill $LIDAR_PID 2>/dev/null
    wait 2>/dev/null
    echo "Done."
}
trap cleanup EXIT INT TERM

# 메인 프로세스 대기
wait $LIDAR_PID

