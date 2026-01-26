#!/bin/bash
# ============================================
# SLAM 맵 생성 스크립트
# YDLidar + Cartographer를 사용한 실시간 맵핑
# ============================================

set -e

# Dynamic path resolution
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
YDLIDAR_SDK_PATH="$HOME/YDLidar-SDK/build/python"

LIDAR_PORT="${1:-/dev/ttyUSB0}"

echo "============================================"
echo "   YDLidar Cartographer SLAM - 맵 생성"
echo "   - TF 간소화: base_link -> laser (static)"
echo "   - Cartographer가 odom TF 관리"
echo "   - 해상도: 2.5cm/pixel"
echo "============================================"

# 포트 권한
if [ -e "$LIDAR_PORT" ]; then
    sudo chmod 666 "$LIDAR_PORT"
    echo "LiDAR port: $LIDAR_PORT"
else
    echo "Warning: LiDAR not found at $LIDAR_PORT"
    ls -la /dev/ttyUSB* 2>/dev/null || echo "No ttyUSB devices"
fi

# ROS2 환경
source /opt/ros/humble/setup.bash

# CycloneDDS 사용 (더 안정적인 메시지 전달)
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp

# Python 경로 (동적으로 설정)
if [ -d "$YDLIDAR_SDK_PATH" ]; then
    export PYTHONPATH="$YDLIDAR_SDK_PATH:$PYTHONPATH"
fi

echo ""
echo "Starting nodes..."
echo ""

# 1. YDLidar Simple Node (Static TF만 퍼블리시)
echo "[1/4] Starting YDLidar Simple node..."
python3 "$PROJECT_DIR/slam_mapping2/ydlidar_simple_node.py" --port "$LIDAR_PORT" &
LIDAR_PID=$!
sleep 3

# TF 확인 및 스캔 대기
echo "Waiting for LiDAR data..."
ros2 topic echo /scan --once 2>/dev/null && echo "Scan OK" || echo "Waiting..."
ros2 topic echo /tf_static --once 2>/dev/null && echo "Static TF OK" || echo "TF waiting..."
sleep 2

# 2. Cartographer Node
echo "[2/4] Starting Cartographer..."
ros2 run cartographer_ros cartographer_node \
    -configuration_directory "$PROJECT_DIR/config" \
    -configuration_basename ydlidar_2d.lua &
CARTO_PID=$!
sleep 5

# 3. Occupancy Grid Node
echo "[3/4] Starting Occupancy Grid (resolution: 0.05)..."
ros2 run cartographer_ros cartographer_occupancy_grid_node \
    --ros-args -p resolution:=0.05 -p publish_period_sec:=0.3 &
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
echo "  TF Tree (Cartographer manages):"
echo "    map -> odom -> base_link -> laser"
echo ""
echo "  Map Resolution: 2.5cm per pixel"
echo ""
echo "  Move LiDAR slowly for detailed mapping"
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

