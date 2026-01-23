#!/usr/bin/env python3
"""
ROS2 Control Node - LiDAR Distance + Motor Control
기존 control_sub.py를 ROS2로 변환 (로직 95% 동일)
"""

import serial
import time
import sys
import threading
import math

import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32, Bool

# YDLidar SDK 임포트
try:
    import ydlidar
except ImportError:
    print("🚨 [에러] ydlidar 라이브러리가 없습니다. 설치 후 실행하세요.")
    sys.exit(1)

# ==========================================
# ⚙️ 설정 파라미터
# ==========================================

# 하드웨어
SERIAL_PORT = "/dev/ttyACM0"  # STM32
LIDAR_PORT = "/dev/ttyUSB0"   # LiDAR
BAUD_RATE = 115200

# 조향
KP_STEER = 0.15
MAX_STEER = 30

# 속도
TARGET_DIST = 0.5
KP_SPEED = 60.0
MAX_SPEED = 60
MIN_SPEED = 20

# 안전
STOP_DEADZONE = 0.1
WATCHDOG_TIME = 1.0
LIDAR_STOP_DIST = 0.35
LIDAR_FOV_DEG = 20

# ==========================================
# LiDAR 스레드 (기존 로직 그대로)
# ==========================================

class LidarReader(threading.Thread):
    def __init__(self, logger):
        super().__init__(daemon=True)
        self.lock = threading.Lock()
        self.latest_front_min = None
        self.latest_stamp = None
        self._stop = False
        self.laser = None
        self.logger = logger

    def stop(self):
        self._stop = True

    def get_latest(self):
        with self.lock:
            return self.latest_front_min

    def _init_lidar(self):
        ydlidar.os_init()
        laser = ydlidar.CYdLidar()

        # LiDAR 설정
        laser.setlidaropt(ydlidar.LidarPropSerialPort, LIDAR_PORT)
        laser.setlidaropt(ydlidar.LidarPropSerialBaudrate, 128000)
        laser.setlidaropt(ydlidar.LidarPropLidarType, ydlidar.TYPE_TRIANGLE)
        laser.setlidaropt(ydlidar.LidarPropDeviceType, ydlidar.YDLIDAR_TYPE_SERIAL)
        laser.setlidaropt(ydlidar.LidarPropScanFrequency, 8.0)
        laser.setlidaropt(ydlidar.LidarPropSampleRate, 5)
        laser.setlidaropt(ydlidar.LidarPropSingleChannel, True)

        if not laser.initialize():
            raise RuntimeError("라이다 초기화 실패")
        if not laser.turnOn():
            raise RuntimeError("라이다 켜기 실패")

        self.laser = laser
        self.logger.info(f'✅ 라이다 연결 성공! ({LIDAR_PORT})')
        return laser

    def run(self):
        try:
            laser = self._init_lidar()
            scan = ydlidar.LaserScan()

            while (not self._stop) and ydlidar.os_isOk():
                ok = laser.doProcessSimple(scan)
                if not ok:
                    continue

                # 전방 데이터 필터링
                front_ranges = []
                for p in scan.points:
                    r = p.range
                    if r <= 0:
                        continue

                    ang_deg = p.angle * 180.0 / math.pi

                    if -LIDAR_FOV_DEG <= ang_deg <= LIDAR_FOV_DEG:
                        if 0.1 < r < 10.0:
                            front_ranges.append(r)

                front_min = min(front_ranges) if front_ranges else None

                with self.lock:
                    self.latest_front_min = front_min
                    self.latest_stamp = scan.stamp

        except Exception as e:
            self.logger.error(f'🚨 라이다 스레드 에러: {e}')
        finally:
            if self.laser:
                self.laser.turnOff()
                self.laser.disconnecting()
            self.logger.info('✅ 라이다 스레드 종료')

# ==========================================
# ROS2 제어 노드
# ==========================================

class ControlNode(Node):
    def __init__(self):
        super().__init__('kinam_control_node')

        # ROS2 구독자
        self.sub_steer = self.create_subscription(
            Float32, '/kinam/steer', self.steer_callback, 10)
        self.sub_locked = self.create_subscription(
            Bool, '/kinam/locked', self.locked_callback, 10)

        # ROS2 퍼블리셔 (디버깅용)
        self.pub_min_distance = self.create_publisher(Float32, '/kinam/min_distance', 10)

        self.get_logger().info('📡 ROS2 제어 노드 시작!')

        # 변수 초기화
        self.steer_val = 0.0
        self.is_locked = False
        self.last_recv_time = time.time()

        # 시리얼 초기화
        self.ser = self._init_serial()

        # LiDAR 시작
        self.lidar_thread = LidarReader(self.get_logger())
        self.lidar_thread.start()
        time.sleep(1)  # 안정화 대기

        # 타이머 (제어 루프)
        self.timer = self.create_timer(0.01, self.control_loop)  # 100Hz

    def _init_serial(self):
        """시리얼 초기화"""
        try:
            ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=0.1)
            time.sleep(2)
            self.get_logger().info(f'✅ STM32 연결 성공! ({SERIAL_PORT})')
            return ser
        except Exception as e:
            self.get_logger().error(f'🚨 STM32 연결 실패: {e}')
            return None

    def steer_callback(self, msg):
        """조향값 수신 콜백"""
        self.steer_val = msg.data
        self.last_recv_time = time.time()

    def locked_callback(self, msg):
        """락온 상태 수신 콜백"""
        self.is_locked = msg.data
        self.last_recv_time = time.time()

    def control_loop(self):
        """메인 제어 루프 (기존 로직 거의 그대로)"""
        # --- [A] 센서 데이터 수집 ---
        lidar_dist = self.lidar_thread.get_latest()

        # LiDAR 거리 발행 (디버깅용)
        if lidar_dist is not None:
            msg_dist = Float32()
            msg_dist.data = float(lidar_dist)
            self.pub_min_distance.publish(msg_dist)

        # --- [B] 안전장치 (Emergency Stop) ---
        if lidar_dist is not None and lidar_dist < LIDAR_STOP_DIST:
            self.get_logger().warn(f'🚨 [충돌 방지] 장애물 감지! ({lidar_dist:.2f}m)', throttle_duration_sec=1.0)
            if self.ser:
                self.ser.write(b"x=0\nz=0\nr=0\n")
            return

        # --- [C] 주행 로직 ---
        if self.is_locked:
            # 1. 조향 (Vision 사용)
            error_x = self.steer_val - 0  # steer_val은 이미 정규화된 값
            steer_cmd = error_x * KP_STEER
            steer_cmd = max(-MAX_STEER, min(MAX_STEER, steer_cmd))

            # 2. 속도 (LiDAR 사용)
            current_dist = lidar_dist if lidar_dist is not None else 0.0

            if current_dist == 0.0:
                error_dist = 0
            else:
                error_dist = current_dist - TARGET_DIST

            speed_z = 0
            speed_r = 0

            # PID 제어
            if abs(error_dist) < STOP_DEADZONE:
                speed_z = 0
                speed_r = 0
            elif error_dist > 0:  # 멀다 -> 전진
                raw_speed = error_dist * KP_SPEED
                final_speed = min(MAX_SPEED, max(MIN_SPEED, raw_speed))
                speed_z = int(final_speed)
            else:  # 가깝다 -> 후진
                raw_speed = abs(error_dist) * (KP_SPEED * 0.5)
                final_speed = min(MAX_SPEED, max(MIN_SPEED, raw_speed))
                speed_r = int(final_speed)

            # 명령 전송
            if self.ser:
                cmd = ""
                if speed_z > 0:
                    cmd = f"x={int(steer_cmd)}\nz={speed_z}\n"
                    self.get_logger().info(f'🚀 GO   | Lidar:{current_dist:.2f}m | Spd:{speed_z}', throttle_duration_sec=1.0)
                elif speed_r > 0:
                    cmd = f"x={int(steer_cmd)}\nr={speed_r}\n"
                    self.get_logger().info(f'🔙 BACK | Lidar:{current_dist:.2f}m | Spd:{speed_r}', throttle_duration_sec=1.0)
                else:
                    cmd = f"x={int(steer_cmd)}\nz=0\n"
                    self.get_logger().info(f'🛑 STOP | Lidar:{current_dist:.2f}m', throttle_duration_sec=1.0)

                self.ser.write(cmd.encode())

        else:
            # 타겟 없음 -> 정지
            if self.ser:
                self.ser.write(b"x=0\nz=0\nr=0\n")

        # --- [D] 통신 Watchdog ---
        if time.time() - self.last_recv_time > WATCHDOG_TIME:
            self.get_logger().warn('🚨 [비상 정지] 비전 통신 두절!', throttle_duration_sec=1.0)
            if self.ser:
                self.ser.write(b"z=0\nr=0\n")
            self.last_recv_time = time.time()

    def cleanup(self):
        """종료 처리"""
        self.lidar_thread.stop()
        if self.ser:
            self.ser.write(b"x=0\nz=0\nr=0\n")
            self.ser.close()
        self.get_logger().info('✅ 제어 노드 종료')


def main(args=None):
    rclpy.init(args=args)
    node = ControlNode()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info('🛑 종료 요청')
    finally:
        node.cleanup()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
