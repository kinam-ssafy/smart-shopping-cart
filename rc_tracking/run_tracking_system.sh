#!/bin/bash

# 설정
WORKSPACE_DIR=~/Desktop/S14P11A401/rc_tracking
ROS_DOMAIN_ID=0

echo "========================================="
echo "RC Tracking System (Pure ROS Version)"
echo "========================================="

# 1. 환경 설정
source /opt/ros/humble/setup.bash
source $WORKSPACE_DIR/install/setup.bash
export ROS_DOMAIN_ID=$ROS_DOMAIN_ID

# 2. 프로세스 정리
echo "[1/6] 기존 프로세스 정리 중..."
pkill -9 -f 'webcam_publisher'
pkill -9 -f 'yolo_deepsort'
pkill -9 -f 'distance_lidar'
pkill -9 -f 'tracking_controller'
pkill -9 -f 'ydlidar_ros2_driver'
sleep 2

# 3. YDLidar 공식 드라이버 실행 (가장 먼저!)
echo "[2/6] LiDAR Driver 시작 중..."
sudo chmod 777 /dev/ttyUSB*
ros2 launch ydlidar_ros2_driver ydlidar_launch.py &
PID_LIDAR=$!
sleep 5  # 라이다 켜지는 시간 대기

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