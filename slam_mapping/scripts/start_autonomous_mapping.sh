#!/bin/bash
# Autonomous Exploration Mapping Script
# RC카가 자율적으로 탐색하며 맵을 생성합니다

set -e

# 매개변수
LIDAR_PORT=${1:-/dev/ttyUSB0}
EXPLORATION_TIME=${2:-300}  # 탐색 시간 (초, 기본 5분)
STM32_PORT=${3:-/dev/ttyACM0}
SIMULATION=${4:-false}

echo "========================================================"
echo "  Autonomous Exploration Mapping System"
echo "========================================================"
echo ""
echo "  LiDAR Port:      $LIDAR_PORT"
echo "  Exploration:     ${EXPLORATION_TIME}s ($(($EXPLORATION_TIME/60)) minutes)"
echo "  STM32 Port:      $STM32_PORT"
echo "  Simulation:      $SIMULATION"
echo ""
echo "  Press Ctrl+C to stop and save map"
echo "========================================================"
echo ""

# 작업 디렉토리
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_DIR="$(dirname "$SCRIPT_DIR")"
cd "$WORKSPACE_DIR"

# 환경 변수 설정
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
export CYCLONEDDS_URI=file://$HOME/cyclonedds/config.xml

# ROS2 환경 소싱
if [ -f "/opt/ros/humble/setup.bash" ]; then
    source /opt/ros/humble/setup.bash
fi

if [ -f "$WORKSPACE_DIR/install/setup.bash" ]; then
    source "$WORKSPACE_DIR/install/setup.bash
fi

# 정리 함수
cleanup() {
    echo ""
    echo "[CLEANUP] Stopping all nodes..."

    # 맵 자동 저장
    MAP_NAME="auto_map_$(date +%Y%m%d_%H%M%S)"
    echo "[SAVE] Saving map as: $MAP_NAME"

    ros2 service call /cartographer/finish_trajectory \
        cartographer_ros_msgs/srv/FinishTrajectory "{trajectory_id: 0}" 2>/dev/null || true

    sleep 2

    ros2 service call /cartographer/write_state \
        cartographer_ros_msgs/srv/WriteState \
        "{filename: '$WORKSPACE_DIR/maps/${MAP_NAME}.pbstream'}" 2>/dev/null || true

    sleep 1

    ros2 run nav2_map_server map_saver_cli \
        -f "$WORKSPACE_DIR/maps/$MAP_NAME" --ros-args -p save_map_timeout:=10000 2>/dev/null || true

    echo "[SAVE] Map saved to: maps/${MAP_NAME}.pgm/.yaml/.pbstream"

    # 모든 프로세스 종료
    pkill -P $$ 2>/dev/null || true

    exit 0
}

trap cleanup SIGINT SIGTERM

echo "[1/8] Starting YDLidar node..."
ros2 run slam_mapping2 ydlidar_node \
    --ros-args -p port:=$LIDAR_PORT &
YDLIDAR_PID=$!
sleep 3
echo "[OK] YDLidar started (PID: $YDLIDAR_PID)"

echo "[2/8] Starting Cartographer SLAM..."
ros2 launch slam_mapping2 cartographer.launch.py \
    use_sim_time:=false \
    configuration_directory:=$WORKSPACE_DIR/config \
    configuration_basename:=ydlidar_2d.lua &
CARTO_PID=$!
sleep 3
echo "[OK] Cartographer started (PID: $CARTO_PID)"

echo "[3/8] Starting TF to Web bridge (optional)..."
ros2 run slam_mapping2 tf_to_web \
    --ros-args -p enable_logging:=false &
TF_WEB_PID=$!
sleep 1
echo "[OK] TF bridge started (PID: $TF_WEB_PID)"

echo "[4/8] Starting Nav2 controller and planner..."
ros2 run nav2_controller controller_server \
    --ros-args \
    --params-file $WORKSPACE_DIR/config/nav2_explore_params.yaml &
CONTROLLER_PID=$!
sleep 2

ros2 run nav2_planner planner_server \
    --ros-args \
    --params-file $WORKSPACE_DIR/config/nav2_explore_params.yaml &
PLANNER_PID=$!
sleep 2

echo "[5/8] Starting Nav2 bt_navigator..."
ros2 run nav2_bt_navigator bt_navigator \
    --ros-args \
    --params-file $WORKSPACE_DIR/config/nav2_explore_params.yaml &
BT_NAV_PID=$!
sleep 2

echo "[6/8] Starting cmd_vel bridge..."
if [ "$SIMULATION" = "true" ]; then
    ros2 run slam_mapping2 cmd_vel_bridge \
        --ros-args -p simulation:=true &
else
    ros2 run slam_mapping2 cmd_vel_bridge \
        --ros-args \
        -p simulation:=false \
        -p serial_port:=$STM32_PORT &
fi
CMD_VEL_PID=$!
sleep 2
echo "[OK] cmd_vel bridge started (PID: $CMD_VEL_PID)"

echo "[7/8] Activating Nav2 lifecycle nodes..."
sleep 3

# Configure and activate controller_server
ros2 lifecycle set /controller_server configure 2>/dev/null || true
sleep 1
ros2 lifecycle set /controller_server activate 2>/dev/null || true
sleep 1

# Configure and activate planner_server
ros2 lifecycle set /planner_server configure 2>/dev/null || true
sleep 1
ros2 lifecycle set /planner_server activate 2>/dev/null || true
sleep 1

# Configure and activate bt_navigator
ros2 lifecycle set /bt_navigator configure 2>/dev/null || true
sleep 1
ros2 lifecycle set /bt_navigator activate 2>/dev/null || true
sleep 1

echo "[OK] Nav2 nodes activated"

echo "[8/8] Starting autonomous exploration..."
ros2 run explore_lite explore \
    --ros-args \
    --params-file $WORKSPACE_DIR/config/explore_params.yaml &
EXPLORE_PID=$!
sleep 2
echo "[OK] Exploration started (PID: $EXPLORE_PID)"

echo ""
echo "========================================================"
echo "  🤖 Autonomous Exploration Active!"
echo "========================================================"
echo "  The robot will explore for $EXPLORATION_TIME seconds"
echo "  Watch progress: http://localhost:8850"
echo "  Press Ctrl+C to stop and save map"
echo "========================================================"
echo ""

# 탐색 시간 제한
if [ "$EXPLORATION_TIME" -gt 0 ]; then
    echo "[INFO] Exploration will stop automatically after $EXPLORATION_TIME seconds"
    sleep $EXPLORATION_TIME
    echo "[INFO] Exploration time completed!"
    cleanup
fi

# 계속 실행 (수동 중단 대기)
wait
