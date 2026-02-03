#!/bin/bash
# ============================================
# SLAM 맵 생성 스크립트 (Headless - RViz 없음)
# RC카 (Jetson Nano) 전용
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
echo "   (Headless Mode - RViz 비활성화)"
echo "   - TF 간소화: base_link -> laser (static)"
echo "   - Cartographer가 odom TF 관리"
echo "   - 해상도: 2.5cm/pixel"
echo "============================================"

# 포트 권한 (dialout 그룹 사용)
if [ -e "$LIDAR_PORT" ]; then
    echo "LiDAR port: $LIDAR_PORT"
    ls -l "$LIDAR_PORT"

    # dialout 그룹으로 접근 가능한지 확인
    if [ ! -r "$LIDAR_PORT" ] || [ ! -w "$LIDAR_PORT" ]; then
        echo "ERROR: No read/write permission for $LIDAR_PORT"
        echo "Please run: sudo chmod 666 $LIDAR_PORT"
        exit 1
    fi
else
    echo "Warning: LiDAR not found at $LIDAR_PORT"
    ls -la /dev/ttyUSB* 2>/dev/null || echo "No ttyUSB devices"
    exit 1
fi

# ROS2 환경
source /opt/ros/humble/setup.bash

# 프로젝트 빌드
echo "Building ROS2 workspace..."
cd "$PROJECT_DIR"
colcon build --symlink-install
if [ $? -ne 0 ]; then
    echo "Error: colcon build failed"
    exit 1
fi

# 빌드된 패키지 소스
if [ -f "$PROJECT_DIR/install/setup.bash" ]; then
    source "$PROJECT_DIR/install/setup.bash"
    echo "ROS2 workspace sourced successfully"
else
    echo "Warning: install/setup.bash not found"
fi

# CycloneDDS 사용 (더 안정적인 메시지 전달)
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp

# Python 경로 (동적으로 설정)
if [ -d "$YDLIDAR_SDK_PATH" ]; then
    export PYTHONPATH="$YDLIDAR_SDK_PATH:$PYTHONPATH"
fi

echo ""
echo "Starting nodes..."
echo ""

# 1. YDLidar Node (ROS2 노드로 실행)
echo "[1/3] Starting YDLidar node..."
ros2 run rccar_nodes ydlidar_node --ros-args -p port:="$LIDAR_PORT" &
LIDAR_PID=$!
sleep 3

# TF 확인 및 스캔 대기
echo "Waiting for LiDAR data..."
ros2 topic echo /scan --once 2>/dev/null && echo "Scan OK" || echo "Waiting..."
ros2 topic echo /tf_static --once 2>/dev/null && echo "Static TF OK" || echo "TF waiting..."
sleep 2

# 2. Cartographer Node
echo "[2/3] Starting Cartographer..."
ros2 run cartographer_ros cartographer_node \
    -configuration_directory "$PROJECT_DIR/config" \
    -configuration_basename ydlidar_2d.lua &
CARTO_PID=$!
sleep 5

# 3. Occupancy Grid Node
echo "[3/3] Starting Occupancy Grid (resolution: 0.05)..."
ros2 run cartographer_ros cartographer_occupancy_grid_node \
    --ros-args -p resolution:=0.05 -p publish_period_sec:=0.3 &
GRID_PID=$!
sleep 1

echo ""
echo "============================================"
echo "  All nodes started! (Headless Mode)"
echo ""
echo "  TF Tree (Cartographer manages):"
echo "    map -> odom -> base_link -> laser"
echo ""
echo "  Map Resolution: 2.5cm per pixel"
echo ""
echo "  원격 PC에서 RViz를 실행하여 시각화하세요"
echo ""
echo "  Move LiDAR slowly for detailed mapping"
echo "  Press Ctrl+C to stop"
echo "============================================"

# 종료 처리
cleanup() {
    echo ""
    echo "Stopping all nodes..."
    kill $GRID_PID 2>/dev/null
    kill $CARTO_PID 2>/dev/null
    kill $LIDAR_PID 2>/dev/null
    wait 2>/dev/null
    echo "Done."
}
trap cleanup EXIT INT TERM

# 메인 프로세스 대기
wait $LIDAR_PID
