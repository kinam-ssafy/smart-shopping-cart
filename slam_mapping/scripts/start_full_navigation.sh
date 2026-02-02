#!/bin/bash
#
# Full Navigation System Startup Script
# YDLidar + Cartographer Pure Localization + Nav2 + Web UI
#
# Usage:
#   ./scripts/start_full_navigation.sh [lidar_port] [map_name] [simulation] [stm32_port]
#
# Examples:
#   ./scripts/start_full_navigation.sh                              # 기본값 사용 (시뮬레이션)
#   ./scripts/start_full_navigation.sh /dev/ttyUSB0                 # LiDAR 포트 지정
#   ./scripts/start_full_navigation.sh /dev/ttyUSB0 s4_map          # 맵 이름 지정
#   ./scripts/start_full_navigation.sh /dev/ttyUSB0 s4_map false    # 실제 모터 사용
#   ./scripts/start_full_navigation.sh /dev/ttyUSB0 s4_map false /dev/ttyACM0  # STM32 포트 지정
#

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 스크립트 위치 기준으로 패키지 경로 설정
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PKG_DIR="$(dirname "$SCRIPT_DIR")"
WEB_DIR="$PKG_DIR/web"
MAPS_DIR="$PKG_DIR/maps"
CONFIG_DIR="$PKG_DIR/config"

# 파라미터
LIDAR_PORT="${1:-/dev/ttyUSB0}"
MAP_NAME="${2:-s4_map}"
SIMULATION="${3:-true}"
STM32_PORT="${4:-/dev/ttyACM0}"

# PID 저장용 배열
declare -a PIDS

# 종료 핸들러
cleanup() {
    echo -e "\n${YELLOW}Shutting down navigation system...${NC}"

    # 모든 백그라운드 프로세스 종료
    for pid in "${PIDS[@]}"; do
        if kill -0 "$pid" 2>/dev/null; then
            kill "$pid" 2>/dev/null || true
        fi
    done

    # ROS2 노드들 정리
    pkill -f "ydlidar_simple_node" 2>/dev/null || true
    pkill -f "cartographer_node" 2>/dev/null || true
    pkill -f "tf_to_web" 2>/dev/null || true
    pkill -f "goal_bridge" 2>/dev/null || true
    pkill -f "cmd_vel_bridge" 2>/dev/null || true
    pkill -f "position_server.py" 2>/dev/null || true
    pkill -f "nav2_controller" 2>/dev/null || true
    pkill -f "nav2_planner" 2>/dev/null || true
    pkill -f "bt_navigator" 2>/dev/null || true
    pkill -f "lifecycle_manager" 2>/dev/null || true

    echo -e "${GREEN}Navigation system stopped.${NC}"
    exit 0
}

trap cleanup SIGINT SIGTERM

# 헤더 출력
echo -e "${BLUE}"
echo "========================================================"
echo "  RC Car Full Navigation System"
echo "========================================================"
echo -e "${NC}"
echo -e "  LiDAR Port:  ${GREEN}$LIDAR_PORT${NC}"
echo -e "  Map:         ${GREEN}$MAP_NAME${NC}"
echo -e "  Simulation:  ${GREEN}$SIMULATION${NC}"
if [ "$SIMULATION" = "false" ]; then
    echo -e "  STM32 Port:  ${GREEN}$STM32_PORT${NC}"
fi
echo ""
echo -e "  Web UI:      ${GREEN}http://localhost:8850${NC}"
echo -e "  Goal Bridge: ${GREEN}http://localhost:8851${NC}"
echo ""
echo -e "${YELLOW}  Press Ctrl+C to stop${NC}"
echo "========================================================"
echo ""

# 맵 파일 확인
MAP_YAML="$MAPS_DIR/${MAP_NAME}.yaml"
MAP_PGM="$MAPS_DIR/${MAP_NAME}.pgm"
MAP_PBSTREAM="$MAPS_DIR/${MAP_NAME}.pbstream"

if [ ! -f "$MAP_YAML" ]; then
    echo -e "${RED}[ERROR] Map YAML not found: $MAP_YAML${NC}"
    echo "Available maps:"
    ls -1 "$MAPS_DIR"/*.yaml 2>/dev/null || echo "  No maps found"
    exit 1
fi

if [ ! -f "$MAP_PBSTREAM" ]; then
    echo -e "${RED}[ERROR] Map pbstream not found: $MAP_PBSTREAM${NC}"
    echo "Run mapping first and save the map."
    exit 1
fi

echo -e "${GREEN}[OK] Map files found${NC}"

# ROS2 환경 설정
echo -e "${BLUE}[1/7] Setting up ROS2 environment...${NC}"
source /opt/ros/humble/setup.bash

# 워크스페이스 빌드 확인 및 source
WORKSPACE_DIR="$(dirname "$PKG_DIR")"
if [ -f "$WORKSPACE_DIR/install/setup.bash" ]; then
    source "$WORKSPACE_DIR/install/setup.bash"
    echo -e "${GREEN}[OK] Workspace sourced${NC}"
else
    echo -e "${YELLOW}[WARN] Workspace not built. Building now...${NC}"
    cd "$WORKSPACE_DIR"
    colcon build --packages-select slam_mapping2 --symlink-install
    source "$WORKSPACE_DIR/install/setup.bash"
fi

# DDS 설정
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
if [ -f "$CONFIG_DIR/cyclonedds.xml" ]; then
    export CYCLONEDDS_URI="file://$CONFIG_DIR/cyclonedds.xml"
fi

# 1. 웹 서버 시작
echo -e "${BLUE}[2/7] Starting web server...${NC}"
cd "$WEB_DIR"
python3 position_server.py "$MAP_NAME" &
PIDS+=($!)
sleep 1
echo -e "${GREEN}[OK] Web server started on port 8850${NC}"

# 2. YDLidar 노드 시작
echo -e "${BLUE}[3/7] Starting YDLidar node...${NC}"
ros2 run slam_mapping2 ydlidar_node --ros-args \
    -p port:="$LIDAR_PORT" \
    -p baudrate:=128000 \
    -p frame_id:=laser \
    -p range_min:=0.12 \
    -p range_max:=10.0 \
    -p frequency:=6.0 &
PIDS+=($!)
sleep 2
echo -e "${GREEN}[OK] YDLidar node started${NC}"

# 3. Cartographer Pure Localization 시작
echo -e "${BLUE}[4/7] Starting Cartographer Pure Localization...${NC}"
ros2 run cartographer_ros cartographer_node \
    -configuration_directory "$CONFIG_DIR" \
    -configuration_basename ydlidar_2d_localization.lua \
    -load_state_filename "$MAP_PBSTREAM" &
PIDS+=($!)
sleep 2

# Cartographer Occupancy Grid 노드
ros2 run cartographer_ros cartographer_occupancy_grid_node \
    -resolution 0.05 \
    -publish_period_sec 1.0 &
PIDS+=($!)
sleep 1
echo -e "${GREEN}[OK] Cartographer started${NC}"

# 4. TF to Web 노드 시작
echo -e "${BLUE}[5/7] Starting TF to Web bridge...${NC}"
ros2 run slam_mapping2 tf_to_web --ros-args \
    -p web_url:="http://localhost:8850/api/position" \
    -p publish_rate:=5.0 &
PIDS+=($!)
sleep 1
echo -e "${GREEN}[OK] TF to Web bridge started${NC}"

# 5. Nav2 스택 시작
echo -e "${BLUE}[6/7] Starting Nav2 stack...${NC}"

# Map Server
ros2 run nav2_map_server map_server --ros-args \
    -p yaml_filename:="$MAP_YAML" \
    -p use_sim_time:=false &
PIDS+=($!)
sleep 1

# Controller Server
ros2 run nav2_controller controller_server --ros-args \
    --params-file "$CONFIG_DIR/nav2_params.yaml" &
PIDS+=($!)
sleep 1

# Planner Server
ros2 run nav2_planner planner_server --ros-args \
    --params-file "$CONFIG_DIR/nav2_params.yaml" &
PIDS+=($!)
sleep 1

# Behavior Server
ros2 run nav2_behaviors behavior_server --ros-args \
    --params-file "$CONFIG_DIR/nav2_params.yaml" &
PIDS+=($!)
sleep 1

# BT Navigator
ros2 run nav2_bt_navigator bt_navigator --ros-args \
    --params-file "$CONFIG_DIR/nav2_params.yaml" &
PIDS+=($!)
sleep 1

# Velocity Smoother
ros2 run nav2_velocity_smoother velocity_smoother --ros-args \
    --params-file "$CONFIG_DIR/nav2_params.yaml" \
    --remap /cmd_vel:=/cmd_vel_nav \
    --remap /cmd_vel_smoothed:=/cmd_vel &
PIDS+=($!)
sleep 1

# Lifecycle Manager
ros2 run nav2_lifecycle_manager lifecycle_manager --ros-args \
    -p autostart:=true \
    -p bond_timeout:=0.0 \
    -p node_names:="['map_server', 'controller_server', 'planner_server', 'behavior_server', 'bt_navigator', 'velocity_smoother']" &
PIDS+=($!)

echo -e "${YELLOW}[INFO] Waiting for Nav2 nodes to activate...${NC}"
sleep 10

# Nav2 활성화 확인 및 수동 활성화 (필요시)
echo -e "${YELLOW}[INFO] Checking Nav2 lifecycle states...${NC}"
for node in map_server controller_server planner_server behavior_server bt_navigator velocity_smoother; do
    state=$(ros2 lifecycle get /$node 2>/dev/null | grep -oE '(unconfigured|inactive|active)' | head -1)
    if [ "$state" = "unconfigured" ]; then
        echo -e "${YELLOW}  Configuring /$node...${NC}"
        ros2 lifecycle set /$node configure 2>/dev/null || true
        sleep 1
    fi
    state=$(ros2 lifecycle get /$node 2>/dev/null | grep -oE '(unconfigured|inactive|active)' | head -1)
    if [ "$state" = "inactive" ]; then
        echo -e "${YELLOW}  Activating /$node...${NC}"
        ros2 lifecycle set /$node activate 2>/dev/null || true
        sleep 1
    fi
done

echo -e "${GREEN}[OK] Nav2 stack started${NC}"

# 6. Goal Bridge 시작
echo -e "${BLUE}[7/7] Starting Goal Bridge and Cmd Vel Bridge...${NC}"
ros2 run slam_mapping2 goal_bridge --ros-args \
    -p bridge_port:=8851 \
    -p web_server_url:="http://localhost:8850" &
PIDS+=($!)
sleep 1

# Cmd Vel Bridge
ros2 run slam_mapping2 cmd_vel_bridge --ros-args \
    -p simulation:="$SIMULATION" \
    -p serial_port:="$STM32_PORT" \
    -p publish_odom:=true \
    -p publish_tf:=false \
    -p max_steer:=37 \
    -p max_speed:=100 \
    -p min_speed:=30 &
PIDS+=($!)
sleep 1
echo -e "${GREEN}[OK] Goal and Cmd Vel bridges started${NC}"

# 완료 메시지
echo ""
echo -e "${GREEN}========================================================"
echo "  Navigation System Ready!"
echo "========================================================"
echo -e "${NC}"
echo -e "  ${BLUE}Open your browser:${NC} ${GREEN}http://localhost:8850${NC}"
echo ""
echo "  Click on the map to set a navigation goal."
echo ""
if [ "$SIMULATION" = "true" ]; then
    echo -e "  ${YELLOW}Running in SIMULATION mode${NC}"
    echo "  cmd_vel commands will be logged but not sent to motors."
else
    echo -e "  ${RED}Running in REAL mode${NC}"
    echo "  cmd_vel commands will be sent to motor driver."
fi
echo ""
echo -e "${YELLOW}  Press Ctrl+C to stop all processes${NC}"
echo "========================================================"
echo ""

# 로그 모니터링 (선택적)
echo -e "${BLUE}Monitoring system... (Ctrl+C to stop)${NC}"
echo ""

# 무한 대기 (Ctrl+C로 종료)
while true; do
    sleep 1

    # 프로세스 상태 확인
    for i in "${!PIDS[@]}"; do
        if ! kill -0 "${PIDS[$i]}" 2>/dev/null; then
            echo -e "${YELLOW}[WARN] Process ${PIDS[$i]} has stopped${NC}"
            unset 'PIDS[$i]'
        fi
    done
done
