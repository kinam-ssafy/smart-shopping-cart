#!/bin/bash
#
# 웹 내비게이션 실행 스크립트 (Cartographer Pure Localization)
# 저장된 맵(.pbstream)을 로드하여 현재 위치를 정확하게 추정
#
# 사용법: ./scripts/start_navigation.sh /dev/ttyUSB0 [맵파일명]
# 예시:   ./scripts/start_navigation.sh /dev/ttyUSB0 seoul_room4
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
WEB_DIR="$PROJECT_DIR/web"
MAPS_DIR="$PROJECT_DIR/maps"
CONFIG_DIR="$PROJECT_DIR/config"
YDLIDAR_SDK_PATH="$HOME/YDLidar-SDK/build/python"

# 인자 확인
if [ -z "$1" ]; then
    echo "=============================================="
    echo "  RC Car Web Navigation (Pure Localization)"
    echo "=============================================="
    echo ""
    echo "사용법: $0 <포트> [맵파일명]"
    echo "예시: $0 /dev/ttyUSB0 seoul_room4"
    echo ""
    echo "사용 가능한 맵 파일:"
    if ls "$MAPS_DIR"/*.pbstream 1> /dev/null 2>&1; then
        ls -1 "$MAPS_DIR"/*.pbstream | while read f; do
            name=$(basename "$f" .pbstream)
            if [ -f "$MAPS_DIR/${name}.pgm" ]; then
                echo "  - $name (pbstream + pgm)"
            fi
        done
    else
        echo "  (pbstream 파일 없음)"
        echo ""
        echo "  맵 생성 방법:"
        echo "    1. ./scripts/create_slam_map.sh /dev/ttyUSB0"
        echo "    2. (별도 터미널) ./scripts/save_map.sh my_map"
    fi
    echo ""
    exit 1
fi

LIDAR_PORT="$1"
MAP_NAME="${2:-}"

# 맵 파일 찾기
if [ -z "$MAP_NAME" ]; then
    # 가장 최근 pbstream 파일 사용
    PBSTREAM=$(ls -t "$MAPS_DIR"/*.pbstream 2>/dev/null | head -1)
    if [ -z "$PBSTREAM" ]; then
        echo "[ERROR] maps/ 디렉토리에 .pbstream 파일이 없습니다."
        echo ""
        echo "[INFO] Pure Localization을 위해서는 .pbstream 파일이 필요합니다."
        echo "       맵을 다시 생성하고 저장하세요:"
        echo "       1. ./scripts/create_slam_map.sh $LIDAR_PORT"
        echo "       2. (별도 터미널) ./scripts/save_map.sh my_map"
        exit 1
    fi
    MAP_NAME=$(basename "$PBSTREAM" .pbstream)
else
    PBSTREAM="$MAPS_DIR/${MAP_NAME}.pbstream"
    if [ ! -f "$PBSTREAM" ]; then
        echo "[ERROR] pbstream 파일을 찾을 수 없습니다: $PBSTREAM"
        echo ""
        echo "[INFO] .pgm/.yaml만 있고 .pbstream이 없다면 맵을 다시 생성해야 합니다."
        exit 1
    fi
fi

MAP_PGM="$MAPS_DIR/${MAP_NAME}.pgm"
MAP_YAML="$MAPS_DIR/${MAP_NAME}.yaml"

# 초기 위치 읽기
INIT_X=0.0
INIT_Y=0.0
INIT_YAW=0.0
if [ -f "$MAP_YAML" ] && grep -q "initial_pose:" "$MAP_YAML" 2>/dev/null; then
    INIT_X=$(grep -A3 "initial_pose:" "$MAP_YAML" | grep "x:" | awk '{print $2}' | head -1)
    INIT_Y=$(grep -A3 "initial_pose:" "$MAP_YAML" | grep "y:" | awk '{print $2}' | head -1)
    INIT_YAW=$(grep -A3 "initial_pose:" "$MAP_YAML" | grep "yaw:" | awk '{print $2}' | head -1)
    # 빈 값 처리
    INIT_X=${INIT_X:-0.0}
    INIT_Y=${INIT_Y:-0.0}
    INIT_YAW=${INIT_YAW:-0.0}
fi

echo "=============================================="
echo "  RC Car Web Navigation (Pure Localization)"
echo "=============================================="
echo ""
echo "  LiDAR Port:     $LIDAR_PORT"
echo "  Map:            $MAP_NAME"
echo "  Pbstream:       $(basename $PBSTREAM)"
echo "  Initial Pose:   x=$INIT_X, y=$INIT_Y, yaw=$INIT_YAW"
echo "  Web URL:        http://localhost:8850"
echo ""
echo "  Pure Localization: 저장된 맵에서 위치 추정"
echo "=============================================="

# 포트 권한 확인
if [ -e "$LIDAR_PORT" ]; then
    if [ ! -r "$LIDAR_PORT" ] || [ ! -w "$LIDAR_PORT" ]; then
        echo "[ERROR] $LIDAR_PORT 권한이 없습니다."
        echo "        sudo chmod 666 $LIDAR_PORT"
        exit 1
    fi
else
    echo "[ERROR] LiDAR를 찾을 수 없습니다: $LIDAR_PORT"
    exit 1
fi

# ROS2 환경 설정
source /opt/ros/humble/setup.bash

# 워크스페이스 빌드
echo ""
echo "[INFO] Building workspace..."
cd "$PROJECT_DIR"
colcon build --symlink-install
source install/setup.bash

# CycloneDDS 설정
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
if [ -f "$HOME/cyclonedds/config.xml" ]; then
    export CYCLONEDDS_URI=file://$HOME/cyclonedds/config.xml
fi

# Python 경로
if [ -d "$YDLIDAR_SDK_PATH" ]; then
    export PYTHONPATH="$YDLIDAR_SDK_PATH:$PYTHONPATH"
fi

echo ""
echo "[INFO] Starting Pure Localization navigation..."
echo ""

# 1. 웹 서버 (맵 이름 전달)
echo "[1/4] Starting Web Server (port 8850)..."
echo "       Map: $MAP_NAME"
cd "$WEB_DIR"
python3 position_server.py "$MAP_NAME" &
WEB_PID=$!
sleep 2
cd "$PROJECT_DIR"

# 2. YDLidar 노드 (Static TF: base_link -> laser)
echo "[2/4] Starting YDLidar node..."
/usr/bin/python3.10 "$PROJECT_DIR/slam_mapping2/ydlidar_simple_node.py" --port "$LIDAR_PORT" &
LIDAR_PID=$!
sleep 3

# 스캔 대기
ros2 topic echo /scan --once 2>/dev/null && echo "  /scan OK" || echo "  Waiting for scan..."
sleep 1

# 3. Cartographer (Pure Localization 모드 - 저장된 맵 로드)
echo "[3/4] Starting Cartographer with saved map..."
echo "       Loading: $(basename $PBSTREAM)"
echo "       Config: ydlidar_2d_localization.lua"

ros2 run cartographer_ros cartographer_node \
    -configuration_directory "$CONFIG_DIR" \
    -configuration_basename ydlidar_2d_localization.lua \
    -load_state_filename "$PBSTREAM" &
CARTO_PID=$!
sleep 5

# Occupancy Grid (맵 발행)
ros2 run cartographer_ros cartographer_occupancy_grid_node \
    --ros-args -p resolution:=0.05 -p publish_period_sec:=0.3 &
GRID_PID=$!
sleep 1

# 4. TF to Web 노드
echo "[4/4] Starting TF to Web node..."
ros2 run slam_mapping2 tf_to_web &
TF_WEB_PID=$!
sleep 1

echo ""
echo "=============================================="
echo "  Pure Localization Started!"
echo "=============================================="
echo ""
echo "  웹 브라우저: http://localhost:8850"
echo ""
echo "  맵: $MAP_NAME"
echo "  초기 위치: x=$INIT_X, y=$INIT_Y, yaw=$INIT_YAW"
echo ""
echo "  TF Tree: map -> odom -> base_link -> laser"
echo ""
echo "  Cartographer가 저장된 맵을 기반으로"
echo "  현재 위치를 추정합니다."
echo ""
echo "  종료: Ctrl+C"
echo "=============================================="

# 종료 처리
cleanup() {
    echo ""
    echo "[INFO] Stopping all processes..."
    kill $TF_WEB_PID 2>/dev/null
    kill $GRID_PID 2>/dev/null
    kill $CARTO_PID 2>/dev/null
    kill $LIDAR_PID 2>/dev/null
    kill $WEB_PID 2>/dev/null
    wait 2>/dev/null
    echo "[INFO] Done."
}
trap cleanup EXIT INT TERM

# 메인 프로세스 대기
wait $LIDAR_PID
