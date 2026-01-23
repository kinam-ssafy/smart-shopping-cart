#!/bin/bash
# RC Tracking System - 전체 실행 스크립트
# 웹캠 + YOLO + DeepSORT + Distance Test 통합 실행

echo "========================================="
echo "🚀 RC Tracking System 시작"
echo "========================================="
echo ""

# 이전 프로세스 종료
echo "🛑 기존 프로세스 정리 중..."
pkill -9 -f "webcam_publisher|yolo_deepsort|distance_lidar" 2>/dev/null
sleep 2

# 작업 디렉토리 이동
cd /home/seonil/rc_tracking
source install/setup.bash

# 웹캠 노드 시작
echo "📷 웹캠 노드 시작 중..."
python3 /home/seonil/rc_tracking/src/rc_detection/rc_detection/webcam_publisher.py > /tmp/webcam.log 2>&1 &
WEBCAM_PID=$!
sleep 3

# YOLO + DeepSORT 노드 시작
echo "🤖 YOLO + DeepSORT 노드 시작 중..."
python3 /home/seonil/rc_tracking/src/rc_detection/rc_detection/yolo_deepsort_node.py \
    --model_path=/home/seonil/rc_tracking/yolo26s.pt \
    --show_preview=true > /tmp/yolo.log 2>&1 &
YOLO_PID=$!
sleep 5

# Distance LiDAR 노드 시작 (Python SDK 사용)
echo "📏 Distance LiDAR 노드 시작 중..."
python3 /home/seonil/rc_tracking/src/rc_detection/rc_detection/distance_lidar_node.py > /tmp/distance.log 2>&1 &
DISTANCE_PID=$!

echo ""
echo "========================================="
echo "✅ 모든 노드 실행 완료!"
echo "========================================="
echo ""
echo "📊 실행 중인 프로세스:"
echo "  📷 웹캠: PID $WEBCAM_PID"
echo "  🤖 YOLO: PID $YOLO_PID"
echo "  📏 Distance: PID $DISTANCE_PID"
echo ""
echo "🎯 기능:"
echo "  • 실시간 객체 감지 및 추적 (YOLO + DeepSORT)"
echo "  • 가장 가까운 객체를 🔴 빨간색 박스로 표시"
echo "  • 기타 객체는 🟢 초록색 박스로 표시"
echo "  • 터미널에 거리 데이터 출력 (가장 가까운 객체만)"
echo ""
echo "📺 OpenCV 창 확인:"
echo "  • 창 이름: 'YOLO + DeepSORT Tracking'"
echo "  • Alt+Tab으로 전환하여 확인"
echo ""
echo "📋 로그 파일:"
echo "  • 웹캠: /tmp/webcam.log"
echo "  • YOLO: /tmp/yolo.log"
echo "  • Distance: /tmp/distance.log"
echo ""
echo "📈 실시간 모니터링 명령어:"
echo "  • 거리 출력 보기: tail -f /tmp/distance.log | grep -E 'CLOSEST|Track'"
echo "  • YOLO 상태: tail -f /tmp/yolo.log | grep 'Total tracks'"
echo "  • 토픽 확인: ros2 topic list | grep -E 'detections|closest'"
echo ""
echo "🛑 종료 방법:"
echo "  ./stop_all.sh"
echo "  또는: pkill -9 -f 'webcam_publisher|yolo_deepsort|distance_test'"
echo ""
echo "========================================="
echo "🎬 시스템 준비 완료 - 카메라를 보세요!"
echo "========================================="
