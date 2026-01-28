#!/bin/bash
# ============================================
# RC카 (Jetson Nano) 원격 SLAM 설정 스크립트
# ============================================

set -e

echo "============================================"
echo "  RC카 원격 SLAM 설정"
echo "  RC카 IP: 70.12.247.62"
echo "  원격 PC IP: 70.12.246.46"
echo "============================================"
echo ""

# 프로젝트 루트 디렉토리
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# 1. CycloneDDS 설정 디렉토리 생성
echo "[1/5] CycloneDDS 설정 디렉토리 생성..."
mkdir -p ~/cyclonedds

# 2. CycloneDDS 설정 파일 복사
echo "[2/5] CycloneDDS 설정 파일 복사 (RC카용)..."
cp "$PROJECT_DIR/config/cyclonedds_rc_car.xml" ~/cyclonedds/

# 3. 환경 변수 설정
echo "[3/5] 환경 변수 설정..."

# .bashrc에 이미 설정이 있는지 확인
if ! grep -q "CYCLONEDDS_URI.*cyclonedds_rc_car.xml" ~/.bashrc; then
    echo "" >> ~/.bashrc
    echo "# ============================================" >> ~/.bashrc
    echo "# RC카 원격 SLAM 설정" >> ~/.bashrc
    echo "# ============================================" >> ~/.bashrc
    echo "" >> ~/.bashrc
    echo "# ROS2 환경" >> ~/.bashrc
    echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc
    echo "" >> ~/.bashrc
    echo "# CycloneDDS 설정 (RC카용)" >> ~/.bashrc
    echo "export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp" >> ~/.bashrc
    echo "export CYCLONEDDS_URI=file://\$HOME/cyclonedds/cyclonedds_rc_car.xml" >> ~/.bashrc
    echo "export ROS_DOMAIN_ID=0" >> ~/.bashrc
    echo "" >> ~/.bashrc
    echo "# 네트워크 설정" >> ~/.bashrc
    echo "export ROS_LOCALHOST_ONLY=0" >> ~/.bashrc
    echo "" >> ~/.bashrc
    echo "환경 변수가 ~/.bashrc에 추가되었습니다."
else
    echo "환경 변수가 이미 설정되어 있습니다."
fi

# 4. LiDAR udev 규칙 설정
echo "[4/5] LiDAR udev 규칙 설정..."
echo 'KERNEL=="ttyUSB*", ATTRS{idVendor}=="10c4", ATTRS{idProduct}=="ea60", MODE="0666", GROUP="dialout"' | sudo tee /etc/udev/rules.d/99-ydlidar.rules

sudo udevadm control --reload-rules
sudo udevadm trigger

echo "udev 규칙이 설정되었습니다."

# 5. 임시 포트 권한 설정
echo "[5/5] LiDAR 포트 권한 설정..."
if [ -e /dev/ttyUSB0 ]; then
    sudo chmod 666 /dev/ttyUSB0
    echo "포트 권한 설정 완료: /dev/ttyUSB0"
else
    echo "Warning: /dev/ttyUSB0 포트를 찾을 수 없습니다."
    echo "LiDAR를 연결한 후 다음 명령을 실행하세요:"
    echo "  sudo chmod 666 /dev/ttyUSB0"
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
echo "  2. SLAM 실행:"
echo "     cd $PROJECT_DIR"
echo "     ./scripts/create_slam_map_headless.sh /dev/ttyUSB0"
echo ""
echo "  3. 별도 터미널에서 RC카 조종:"
echo "     python3 control_car.py"
echo ""
echo "  4. 원격 PC에서 RViz 실행하여 시각화"
echo ""
echo "============================================"
