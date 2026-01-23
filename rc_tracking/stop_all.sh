#!/bin/bash
# RC Tracking System 종료 스크립트

echo "RC Tracking System 종료 중..."

pkill -9 -f "webcam_publisher" 2>/dev/null
pkill -9 -f "yolo_deepsort" 2>/dev/null
pkill -9 -f "distance_lidar" 2>/dev/null
pkill -9 -f "tracking_controller" 2>/dev/null

sleep 1

echo "모든 프로세스 종료 완료"
