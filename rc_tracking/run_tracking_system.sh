#!/bin/bash

# 설정
WORKSPACE_DIR=~/Desktop/S14P11A401/rc_tracking
ROS_DOMAIN_ID=0

echo "========================================="
echo "RC Tracking System (Pure ROS Version)"
echo "========================================="

cleanup() {
    echo "[INFO] Shutting down all nodes..."
    trap - SIGINT SIGTERM  # 추가 시그널 무시
    kill $(jobs -p) 2>/dev/null
    wait
    exit 0
}
trap cleanup SIGINT SIGTERM
 
 
 # 1. 환경 설정
 echo "[0/6] 환경 설정 중..."
 source /opt/ros/humble/setup.bash
 source $WORKSPACE_DIR/install/setup.bash
 export ROS_DOMAIN_ID=$ROS_DOMAIN_ID
 unset CYCLONEDDS_URI
 export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
 # ros2 daemon은 생략 (느려질 수 있음)
 cd "$WORKSPACE_DIR" || exit 1
 
# 2. 프로세스 정리
echo "[1/6] 기존 프로세스 정리 중..."
pkill -9 -f 'webcam_publisher'
pkill -9 -f 'yolo_deepsort'
pkill -9 -f 'distance_lidar'
pkill -9 -f 'tracking_controller'
pkill -9 -f 'ydlidar_ros2_driver'
pkill -9 -f 'static_transform_publisher'   # ✅ [추가] TF 퍼블리셔도 정리
sleep 2

# 3. YDLidar 공식 드라이버 실행 (가장 먼저!)
echo "[2/6] LiDAR Driver 시작 중..."
sudo chmod 777 /dev/ttyUSB*
ros2 launch ydlidar_ros2_driver ydlidar_launch.py 2>/dev/null &
PID_LIDAR=$!
sleep 2

# ✅ [추가] Calibration TF (default_cam -> laser_frame) 자동 실행
ros2 run tf2_ros static_transform_publisher \
  --x -0.14 --y 0 --z 0.1 --yaw 0 --pitch 0 --roll 0 \
  --frame-id default_cam --child-frame-id laser_frame &
PID_TF=$!

sleep 3  # 라이다/TF 안정화 시간

# 4. 나머지 노드 실행
echo "[3/6] 웹캠 노드 시작 중..."
python3 src/rc_detection/rc_detection/webcam_publisher.py &
PID_CAM=$!
sleep 2

echo "[4/6] YOLO + DeepSORT 노드 시작 중..."
python3 src/rc_detection/rc_detection/yolo_deepsort_node.py &
PID_YOLO=$!
sleep 5

echo "[5/6] Distance Processing 노드 시작 중..."
python3 src/rc_detection/rc_detection/distance_lidar_node.py &
PID_DIST=$!
sleep 1

echo "[6/6] Tracking Controller 노드 시작 중..."
sudo chmod 777 /dev/ttyACM*
python3 src/rc_detection/rc_detection/tracking_controller_node.py &
PID_CTRL=$!

echo "========================================="
echo "모든 노드 실행 완료!"
echo "========================================="

wait

