#!/bin/bash
# ===========================================
# RC Car Tracking System - 통합 실행 스크립트
# 웹캠 + YOLO + DeepSORT + LiDAR + PID 제어
# ===========================================

echo "========================================="
echo "RC Tracking System (With Controller)"
echo "========================================="
echo ""

# 이전 프로세스 종료
echo "[1/5] 기존 프로세스 정리 중..."
pkill -9 -f "webcam_publisher|yolo_deepsort|distance_lidar|tracking_controller" 2>/dev/null
sleep 2

# Conda 환경 및 ROS2 환경 설정
source ~/miniforge3/etc/profile.d/conda.sh
conda activate rc_car
source /opt/ros/humble/setup.bash

# 작업 디렉토리 이동 및 워크스페이스 설정
cd /home/ssafy/Desktop/S14P11A401/rc_tracking
source install/setup.bash

# GUI 없이 실행 (headless 모드)
export QT_QPA_PLATFORM=offscreen
export DISPLAY=:0

# 웹캠 노드 시작
echo "[2/5] 웹캠 노드 시작 중..."
python3 /home/ssafy/Desktop/S14P11A401/rc_tracking/src/rc_detection/rc_detection/webcam_publisher.py > /tmp/webcam.log 2>&1 &
WEBCAM_PID=$!
sleep 3

# YOLO + DeepSORT 노드 시작
echo "[3/5] YOLO + DeepSORT 노드 시작 중..."
python3 /home/ssafy/Desktop/S14P11A401/rc_tracking/src/rc_detection/rc_detection/yolo_deepsort_node.py \
    --ros-args \
    -p model_path:=/home/ssafy/Desktop/S14P11A401/rc_tracking/yolo26m.engine \
    -p show_preview:=false \
    -p publish_debug_image:=true > /tmp/yolo.log 2>&1 &
YOLO_PID=$!
sleep 5

# Distance LiDAR 노드 시작
echo "[4/5] Distance LiDAR 노드 시작 중..."
python3 /home/ssafy/Desktop/S14P11A401/rc_tracking/src/rc_detection/rc_detection/distance_lidar_node.py > /tmp/distance.log 2>&1 &
DISTANCE_PID=$!
sleep 2

# Tracking Controller 노드 시작
echo "[5/5] Tracking Controller 노드 시작 중..."
python3 /home/ssafy/Desktop/S14P11A401/rc_tracking/src/rc_detection/rc_detection/tracking_controller_node.py > /tmp/controller.log 2>&1 &
CONTROLLER_PID=$!

echo ""
echo "========================================="
echo "모든 노드 실행 완료!"
echo "========================================="
echo ""
echo "실행 중인 프로세스:"
echo "  [1] Webcam:    PID $WEBCAM_PID"
echo "  [2] YOLO:      PID $YOLO_PID"
echo "  [3] Distance:  PID $DISTANCE_PID"
echo "  [4] Controller: PID $CONTROLLER_PID"
echo ""
echo "기능:"
echo "  - 실시간 객체 감지 및 추적 (YOLO + DeepSORT)"
echo "  - LiDAR 기반 거리 측정"
echo "  - PID 제어로 목표 거리(0.8m) 유지"
echo "  - 화면 중앙 기준 자동 조향"
echo "  - 35cm 이내 긴급 정지"
echo ""
echo "로그 파일:"
echo "  - Webcam:    tail -f /tmp/webcam.log"
echo "  - YOLO:      tail -f /tmp/yolo.log"
echo "  - Distance:  tail -f /tmp/distance.log"
echo "  - Controller: tail -f /tmp/controller.log"
echo ""
echo "ROS2 토픽:"
echo "  - /detections        : 객체 감지 결과"
echo "  - /yolo_debug_image  : YOLO 시각화 이미지 (노트북에서 보기용)"
echo "  - /closest_object_id : 가장 가까운 객체 ID"
echo "  - /control/steer     : 조향값"
echo "  - /control/speed     : 속도"
echo "  - /control/status    : 상태 (0:STOP, 1:EMERGENCY, 2:SEARCH, 3:TRACKING)"
echo ""
echo "노트북에서 영상 보기:"
echo "  ros2 run rqt_image_view rqt_image_view"
echo "  (토픽 선택: /yolo_debug_image)"
echo ""
echo "종료:"
echo "  ./stop_all.sh"
echo "  또는: pkill -9 -f 'webcam_publisher|yolo_deepsort|distance_lidar|tracking_controller'"
echo ""
echo "========================================="
echo "시스템 준비 완료!"
echo "========================================="
