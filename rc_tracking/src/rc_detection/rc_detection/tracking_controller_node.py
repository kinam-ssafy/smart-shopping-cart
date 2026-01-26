#!/usr/bin/env python3
"""
RC Car Tracking Controller Node (One-Shot Calibration)
- 기준값(Calibration) 로직 개선:
  최초 락온 시점의 안정적인 데이터만 '딱 한 번' 학습하고,
  주행 중 튀는 값(이상치)으로 오염되지 않도록 업데이트를 막습니다.
"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import Int32, Float32
import serial
import time
import math

try:
    from rc_detection.msg import Detection, DetectionArray
    DETECTION_MSG_AVAILABLE = True
except ImportError:
    print("❌ Detection 메시지 import 실패")
    DETECTION_MSG_AVAILABLE = False

# ==========================================
# 📏 [사용자 설정] 타겟의 실제 키 (단위: m)
# ==========================================
# 실제 사람: 1.7
# A4용지 프린트: 0.2 ~ 0.3 (자로 재보세요!)
TARGET_REAL_HEIGHT = 0.15


class TrackingControllerNode(Node):
    def __init__(self):
        super().__init__('tracking_controller_node')

        # ==========================================
        # ⚙️ 파라미터 설정
        # ==========================================

        self.declare_parameter('serial_port', '/dev/ttyACM0')
        self.declare_parameter('baud_rate', 115200)

        self.declare_parameter('image_width', 640)
        self.declare_parameter('image_height', 480)

        # 조향 PID
        self.declare_parameter('kp_steer', 0.08)
        self.declare_parameter('max_steer', 30)

        # 속도 PID
        self.declare_parameter('target_distance', 0.8)
        self.declare_parameter('kp_speed', 40.0)
        self.declare_parameter('ki_speed', 0.5)
        self.declare_parameter('kd_speed', 10.0)
        self.declare_parameter('max_speed', 100)
        self.declare_parameter('min_speed', 90)

        # 안전 설정
        self.declare_parameter('stop_deadzone', 0.25)
        self.declare_parameter('emergency_stop_dist', 0.6)
        self.declare_parameter('watchdog_timeout', 1.5)
        self.declare_parameter('target_real_height', TARGET_REAL_HEIGHT)

        # 파라미터 로드
        self.serial_port = self.get_parameter('serial_port').value
        self.baud_rate = self.get_parameter('baud_rate').value
        self.image_width = self.get_parameter('image_width').value
        self.image_height = self.get_parameter('image_height').value

        self.kp_steer = self.get_parameter('kp_steer').value
        self.max_steer = self.get_parameter('max_steer').value

        self.target_dist = self.get_parameter('target_distance').value
        self.kp_speed = self.get_parameter('kp_speed').value
        self.ki_speed = self.get_parameter('ki_speed').value
        self.kd_speed = self.get_parameter('kd_speed').value
        self.max_speed = self.get_parameter('max_speed').value
        self.min_speed = self.get_parameter('min_speed').value

        self.stop_deadzone = self.get_parameter('stop_deadzone').value
        self.emergency_stop_dist = self.get_parameter('emergency_stop_dist').value
        self.watchdog_timeout = self.get_parameter('watchdog_timeout').value
        self.target_height_m = self.get_parameter('target_real_height').value

        # 상태 변수
        self.latest_detections = None
        self.closest_object_id = None
        self.latest_distance = None
        self.last_cmd = None

        self.last_detection_time = time.time()
        self.last_distance_time = time.time()

        # PID 상태
        self.prev_error_dist = 0.0
        self.integral_dist = 0.0
        self.last_pid_time = time.time()

        # 락온 상태
        self.locked_target_id = None
        self.lock_counter = 0
        self.lock_threshold = 45

        # [NEW] 거리 추정용 기준값 & 플래그
        self.ref_lidar_dist = None    # 기준 라이다 거리
        self.ref_bbox_height = None   # 기준 바운딩 박스 높이
        self.is_calibrated = False    # 학습 완료 여부 (True면 더 이상 업데이트 안 함)

        # 시리얼 초기화
        self.ser = self.init_serial()

        # Subscribers
        if DETECTION_MSG_AVAILABLE:
            self.detection_sub = self.create_subscription(
                DetectionArray, '/detections', self.detection_callback, 10)

        self.closest_id_sub = self.create_subscription(
            Int32, '/closest_object_id', self.closest_id_callback, 10)

        self.distance_sub = self.create_subscription(
            Float32, '/distance', self.distance_callback, 10)

        # Publishers
        self.steer_pub = self.create_publisher(Float32, '/control/steer', 10)
        self.speed_pub = self.create_publisher(Float32, '/control/speed', 10)
        self.status_pub = self.create_publisher(Int32, '/control/status', 10)

        # Timer
        self.control_timer = self.create_timer(0.02, self.control_loop)

        self.get_logger().info('=' * 50)
        self.get_logger().info('🚗 Smart Tracking Controller (One-Shot Calib)')
        self.get_logger().info(f'👉 타겟 키: {self.target_height_m}m')
        self.get_logger().info('=' * 50)

    def init_serial(self):
        try:
            ser = serial.Serial(self.serial_port, self.baud_rate, timeout=0.1)
            time.sleep(2)
            self.get_logger().info(f'✅ STM32 연결 성공 ({self.serial_port})')
            return ser
        except Exception as e:
            self.get_logger().error(f'❌ STM32 연결 실패: {e}')
            return None

    def detection_callback(self, msg):
        self.latest_detections = msg.detections
        self.last_detection_time = time.time()

    def closest_id_callback(self, msg):
        self.closest_object_id = msg.data if msg.data >= 0 else None

    def distance_callback(self, msg):
        self.latest_distance = msg.data
        self.last_distance_time = time.time()

    def get_target_detection(self):
        if not self.latest_detections:
            return None

        center_x = self.image_width // 2
        center_y = self.image_height // 2

        # 락온 유지 체크
        if self.locked_target_id is not None:
            for det in self.latest_detections:
                if det.track_id == self.locked_target_id:
                    return det
            
            # 타겟을 놓침 -> 락온 해제 및 학습 데이터 초기화
            self.locked_target_id = None
            self.lock_counter = 0
            self.is_calibrated = False  # [중요] 타겟 놓치면 학습도 초기화 (새로운 사람일 수 있으니)
            self.get_logger().warn('🔓 락온 해제 (Target Lost) -> 학습 초기화')

        best_det = None
        best_center_dist = float('inf')

        # 화면 중앙에 가까운 객체 탐색
        for det in self.latest_detections:
            det_cx = (det.x_min + det.x_max) / 2
            det_cy = (det.y_min + det.y_max) / 2

            if det.x_min <= center_x <= det.x_max and det.y_min <= center_y <= det.y_max:
                dist_to_center = math.sqrt((det_cx - center_x)**2 + (det_cy - center_y)**2)
                if dist_to_center < best_center_dist:
                    best_center_dist = dist_to_center
                    best_det = det

        # 락온 카운터 관리
        if best_det:
            self.lock_counter += 1
            if self.lock_counter >= self.lock_threshold:
                self.locked_target_id = best_det.track_id
        else:
            self.lock_counter = max(0, self.lock_counter - 2)

        # fallback: closest_id
        if best_det is None and self.closest_object_id is not None:
            for det in self.latest_detections:
                if det.track_id == self.closest_object_id:
                    return det

        return best_det

    def calculate_steer(self, target_det):
        if target_det is None:
            return 0.0
        
        target_cx = (target_det.x_min + target_det.x_max) / 2
        center_x = self.image_width / 2
        error_x = target_cx - center_x
        steer_val = error_x * self.kp_steer
        steer_val = max(-self.max_steer, min(self.max_steer, steer_val))
        return steer_val

    def calculate_speed_pid(self, current_distance):
        """속도 PID 제어 (후진 없음)"""
        if current_distance is None or current_distance <= 0:
            return 0

        current_time = time.time()
        dt = current_time - self.last_pid_time
        if dt <= 0: dt = 0.02
        self.last_pid_time = current_time

        error_dist = current_distance - self.target_dist

        # [수정] 너무 가까우면 정지
        if error_dist < self.stop_deadzone:
            self.integral_dist = 0
            self.prev_error_dist = error_dist
            return 0

        # PID 계산
        p_term = self.kp_speed * error_dist
        self.integral_dist += error_dist * dt
        self.integral_dist = max(-50, min(50, self.integral_dist))
        i_term = self.ki_speed * self.integral_dist
        d_term = self.kd_speed * (error_dist - self.prev_error_dist) / dt
        self.prev_error_dist = error_dist

        output = p_term + i_term + d_term

        # [수정] 전진만 허용
        speed_z = 0
        if output > 0:
            speed_z = int(max(self.min_speed, min(self.max_speed, abs(output))))
        
        return speed_z

    def send_motor_command(self, steer, speed_z):
        """STM32로 명령 전송"""
        if self.ser is None: return

        try:
            if speed_z > 0:
                cmd = f"x={int(steer)}\nz={speed_z}\n"
            else:
                cmd = f"x={int(steer)}\nz=0\n"

            if cmd == self.last_cmd: return

            self.ser.write(cmd.encode())
            self.last_cmd = cmd

        except Exception as e:
            self.get_logger().error(f'시리얼 전송 에러: {e}')
            self.last_cmd = None

    def emergency_stop(self):
        if self.ser:
            self.ser.write(b"x=0\nz=0\nr=0\n")
        self.integral_dist = 0

    def control_loop(self):
        current_time = time.time()

        # 1. Watchdog
        if (current_time - self.last_detection_time) > self.watchdog_timeout:
            self.get_logger().warn('🚨 감지 타임아웃', throttle_duration_sec=1.0)
            self.emergency_stop()
            self.status_pub.publish(Int32(data=0))
            return

        # 2. [핵심] 거리 추정 로직 (One-Shot Calibration)
        target = self.get_target_detection()
        final_dist = 0.0
        dist_source = "NONE"

        if target:
            bbox_h = target.y_max - target.y_min
            
            # (A) 라이다 데이터가 건강한 경우
            if self.latest_distance is not None and self.latest_distance > 0:
                final_dist = self.latest_distance
                dist_source = "LiDAR"
                
                # [수정됨] 매번 업데이트하지 않고, '아직 학습 안 됐을 때'만 저장 (One-shot)
                # 락온 상태이고, 거리가 2m 이내로 안정적일 때만 학습
                if self.locked_target_id is not None and not self.is_calibrated and 0.2 < final_dist < 2.0:
                     self.ref_lidar_dist = final_dist
                     self.ref_bbox_height = bbox_h
                     self.is_calibrated = True
                     self.get_logger().info(f"✅ 거리 비율 학습 완료: {final_dist:.2f}m / {bbox_h}px")
                
            # (B) 라이다가 죽었거나 이상한 경우 (비전 추정)
            else:
                if self.is_calibrated and bbox_h > 0:
                    # [핵심] 학습된 비율(고정값)을 사용하여 거리 추정
                    final_dist = self.ref_lidar_dist * (self.ref_bbox_height / bbox_h)
                    dist_source = "Vision(Ref)"
                else:
                    # 학습 전이면 설정된 키 기반 추정
                    if bbox_h > 10:
                        final_dist = (self.target_height_m * self.image_height) / (bbox_h * 2.0)
                        final_dist = max(0.2, min(5.0, final_dist))
                        dist_source = "Vision(Basic)"

        # 3. 긴급 정지
        if final_dist > 0 and final_dist < self.emergency_stop_dist:
            self.get_logger().warn(f'🚨 긴급 정지! ({final_dist:.2f}m via {dist_source})', throttle_duration_sec=0.5)
            self.emergency_stop()
            self.status_pub.publish(Int32(data=1))
            return

        # 4. 타겟 없음 처리
        if target is None:
            self.send_motor_command(0, 0)
            self.get_logger().info(f'👀 탐색 중... ({self.lock_counter})', throttle_duration_sec=1.0)
            self.status_pub.publish(Int32(data=2))
            return

        # 5. 제어 계산 및 전송
        steer_val = self.calculate_steer(target)
        speed_z = self.calculate_speed_pid(final_dist)
        self.send_motor_command(steer_val, speed_z)

        # 6. 상태 발행 및 로그
        self.steer_pub.publish(Float32(data=float(steer_val)))
        self.speed_pub.publish(Float32(data=float(speed_z)))
        self.status_pub.publish(Int32(data=3))

        lock_str = 'LOCKED' if self.locked_target_id is not None else 'UNLOCKED'
        
        self.get_logger().info(
            f'🎯 {lock_str} | Steer:{steer_val:+.0f} | Spd:{speed_z} | '
            f'Dist:{final_dist:.2f}m ({dist_source})',
            throttle_duration_sec=0.5
        )

    def cleanup(self):
        self.emergency_stop()
        if self.ser: self.ser.close()
        self.get_logger().info('✅ Controller 종료')


def main(args=None):
    rclpy.init(args=args)
    node = TrackingControllerNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        print('\n🛑 종료 요청')
    finally:
        node.cleanup()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()