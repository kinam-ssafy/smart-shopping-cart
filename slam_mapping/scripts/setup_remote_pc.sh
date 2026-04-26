#!/bin/bash
# ============================================
# 원격 PC (노트북) 원격 SLAM 설정 스크립트
# ============================================

set -e

echo "============================================"
echo "  원격 PC 원격 SLAM 설정"
echo "  원격 PC IP: 70.12.246.46"
echo "  RC카 IP: 70.12.247.62"
echo "============================================"
echo ""

# 프로젝트 루트 디렉토리
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# 1. ROS2 및 Cartographer 설치 확인
echo "[1/4] ROS2 및 Cartographer 설치 확인..."
if ! command -v ros2 &> /dev/null; then
    echo "Error: ROS2가 설치되어 있지 않습니다."
    echo "다음 명령으로 설치하세요:"
    echo "  sudo apt update"
    echo "  sudo apt install ros-humble-desktop"
    exit 1
fi

if ! ros2 pkg list | grep -q "cartographer"; then
    echo "Warning: Cartographer가 설치되어 있지 않습니다."
    echo "설치 중..."
    sudo apt update
    sudo apt install -y ros-humble-cartographer ros-humble-cartographer-ros
fi

if ! ros2 pkg list | grep -q "rmw_cyclonedds"; then
    echo "Warning: CycloneDDS가 설치되어 있지 않습니다."
    echo "설치 중..."
    sudo apt install -y ros-humble-rmw-cyclonedds-cpp
fi

echo "모든 패키지가 설치되어 있습니다."

# 2. CycloneDDS 설정 디렉토리 생성
echo "[2/4] CycloneDDS 설정 디렉토리 생성..."
mkdir -p ~/cyclonedds

# 3. CycloneDDS 설정 파일 복사
echo "[3/4] CycloneDDS 설정 파일 복사 (원격 PC용)..."
cp "$PROJECT_DIR/config/cyclonedds_remote_pc.xml" ~/cyclonedds/

# 4. 환경 변수 설정
echo "[4/4] 환경 변수 설정..."

# .bashrc에 이미 설정이 있는지 확인
if ! grep -q "CYCLONEDDS_URI.*cyclonedds_remote_pc.xml" ~/.bashrc; then
    echo "" >> ~/.bashrc
    echo "# ============================================" >> ~/.bashrc
    echo "# 원격 PC SLAM 시각화 설정" >> ~/.bashrc
    echo "# ============================================" >> ~/.bashrc
    echo "" >> ~/.bashrc
    echo "# ROS2 환경" >> ~/.bashrc
    echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc
    echo "" >> ~/.bashrc
    echo "# CycloneDDS 설정 (원격 PC용)" >> ~/.bashrc
    echo "export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp" >> ~/.bashrc
    echo "export CYCLONEDDS_URI=file://\$HOME/cyclonedds/cyclonedds_remote_pc.xml" >> ~/.bashrc
    echo "export ROS_DOMAIN_ID=0" >> ~/.bashrc
    echo "" >> ~/.bashrc
    echo "# 네트워크 설정" >> ~/.bashrc
    echo "export ROS_LOCALHOST_ONLY=0" >> ~/.bashrc
    echo "" >> ~/.bashrc
    echo "환경 변수가 ~/.bashrc에 추가되었습니다."
else
    echo "환경 변수가 이미 설정되어 있습니다."
fi

echo ""
echo "============================================"
echo "  설정 완료!"
echo "============================================"
echo ""
echo "다음 단계:"
echo "  1. 새 터미널을 열거나 다음 명령 실행:"
echo "     source ~/.bashrc"
echo ""
echo "  2. RC카가 SLAM을 실행 중인지 확인"
echo ""
echo "  3. 토픽 확인:"
echo "     ros2 topic list"
echo "     ros2 topic hz /scan"
echo ""
echo "  4. RViz 실행:"
echo "     rviz2 -d $PROJECT_DIR/rviz/slam.rviz"
echo ""
echo "============================================"
