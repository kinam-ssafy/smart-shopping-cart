#!/bin/bash
# ============================================
# 맵 저장 스크립트
# 저장 파일:
#   - .pgm, .yaml (맵 이미지 + 메타데이터)
#   - .pbstream (Cartographer 상태 - Localization용)
# ============================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
SAVE_DIR="$PROJECT_DIR/maps"

MAP_NAME="${1:-map_$(date +%Y%m%d_%H%M%S)}"

echo "============================================"
echo "   Saving Map: $MAP_NAME"
echo "============================================"

# ROS2 환경
source /opt/ros/humble/setup.bash
if [ -f "$PROJECT_DIR/install/setup.bash" ]; then
    source "$PROJECT_DIR/install/setup.bash"
fi

# CycloneDDS 설정
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
if [ -f "$HOME/cyclonedds/config.xml" ]; then
    export CYCLONEDDS_URI=file://$HOME/cyclonedds/config.xml
fi

# 디렉토리 생성
mkdir -p "$SAVE_DIR"

# 1. Cartographer 상태 저장 (.pbstream)
echo ""
echo "[1/3] Saving Cartographer state (.pbstream)..."
PBSTREAM_PATH="$SAVE_DIR/${MAP_NAME}.pbstream"

# Trajectory 완료
ros2 service call /finish_trajectory cartographer_ros_msgs/srv/FinishTrajectory "{trajectory_id: 0}" 2>/dev/null || true
sleep 1

# 상태 저장
ros2 service call /write_state cartographer_ros_msgs/srv/WriteState "{filename: '$PBSTREAM_PATH'}" 2>/dev/null
if [ -f "$PBSTREAM_PATH" ]; then
    echo "  Saved: $PBSTREAM_PATH"
else
    echo "  Warning: pbstream 저장 실패 (Cartographer 실행 중인지 확인)"
fi

# 2. 맵 이미지 저장 (.pgm, .yaml)
echo ""
echo "[2/3] Saving map image (.pgm, .yaml)..."
ros2 run nav2_map_server map_saver_cli -f "$SAVE_DIR/$MAP_NAME"

# 3. 현재 로봇 위치를 YAML에 추가
echo ""
echo "[3/3] Saving initial pose to yaml..."

MAP_YAML="$SAVE_DIR/${MAP_NAME}.yaml"

python3 << EOF
import rclpy
from rclpy.node import Node
from tf2_ros import Buffer, TransformListener
import math
import yaml
import sys

class PoseSaver(Node):
    def __init__(self):
        super().__init__('pose_saver')
        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)

    def get_pose(self):
        try:
            self.tf_buffer.can_transform('map', 'base_link', rclpy.time.Time(),
                                         timeout=rclpy.duration.Duration(seconds=2.0))
            transform = self.tf_buffer.lookup_transform('map', 'base_link', rclpy.time.Time())

            x = transform.transform.translation.x
            y = transform.transform.translation.y

            q = transform.transform.rotation
            siny_cosp = 2.0 * (q.w * q.z + q.x * q.y)
            cosy_cosp = 1.0 - 2.0 * (q.y * q.y + q.z * q.z)
            yaw = math.atan2(siny_cosp, cosy_cosp)

            return {'x': round(x, 4), 'y': round(y, 4), 'yaw': round(yaw, 4)}
        except Exception as e:
            print(f"  Warning: Could not get pose from TF: {e}")
            return None

def main():
    rclpy.init()
    node = PoseSaver()

    for _ in range(20):
        rclpy.spin_once(node, timeout_sec=0.1)

    pose = node.get_pose()

    # 기존 YAML 파일 읽기
    yaml_path = "$MAP_YAML"
    try:
        with open(yaml_path, 'r') as f:
            data = yaml.safe_load(f)
    except:
        data = {}

    # 초기 위치 추가
    if pose:
        data['initial_pose'] = {
            'x': pose['x'],
            'y': pose['y'],
            'yaw': pose['yaw']
        }
        print(f"  Initial pose: x={pose['x']:.3f}, y={pose['y']:.3f}, yaw={pose['yaw']:.3f}")
    else:
        data['initial_pose'] = {
            'x': 0.0,
            'y': 0.0,
            'yaw': 0.0
        }
        print("  Using default pose (0, 0, 0)")

    # YAML 파일 저장
    with open(yaml_path, 'w') as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)

    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
EOF

echo ""
echo "============================================"
echo "  Map saved!"
echo ""
echo "  Files:"
echo "    - $SAVE_DIR/$MAP_NAME.pgm      (맵 이미지)"
echo "    - $SAVE_DIR/$MAP_NAME.yaml     (맵 + 초기 위치)"
echo "    - $SAVE_DIR/$MAP_NAME.pbstream (Cartographer 상태)"
echo ""
echo "  Navigation 시:"
echo "    ./scripts/start_navigation.sh /dev/ttyUSB0 $MAP_NAME"
echo "============================================"
