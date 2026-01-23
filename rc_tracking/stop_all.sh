#!/bin/bash
# RC Tracking System 종료 스크립트

echo "RC Tracking System 종료 중..."

# 먼저 모터 정지 명령 전송
echo "모터 정지 명령 전송..."
echo -e "x=0\nz=0\nr=0\n" > /dev/ttyACM0 2>/dev/null

sleep 0.5

# 프로세스 종료
pkill -9 -f "webcam_publisher" 2>/dev/null
pkill -9 -f "yolo_deepsort" 2>/dev/null
pkill -9 -f "distance_lidar" 2>/dev/null
pkill -9 -f "tracking_controller" 2>/dev/null

sleep 1

# 한번 더 정지 명령
echo -e "x=0\nz=0\nr=0\n" > /dev/ttyACM0 2>/dev/null

echo "모든 프로세스 종료 완료"
