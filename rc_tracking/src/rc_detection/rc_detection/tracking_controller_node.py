#!/usr/bin/env python3
"""
RC Car Tracking Controller Node (No Reverse Version)
- 후진 로직 제거: 목표 거리보다 가까우면 정지(STOP)
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
        self.declare_parameter('target_distance', 1.0)  # 목표 거리 (m)
        self.declare_parameter('kp_speed', 40.0)
        self.declare_parameter('ki_speed', 0.5)
        self.declare_parameter('kd_speed', 10.0)
        self.declare_parameter('max_speed', 100)
        self.declare_parameter('min_speed', 90)

        # 안전 설정
        self.declare_parameter('stop_deadzone', 0.25)
        self.declare_parameter('emergency_stop_dist', 0.7)
        self.declare_parameter('watchdog_timeout', 1.5)

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
        self.get_logger().info('🚗 Tracking Controller Node 시작 (No Reverse)')
        self.get_logger().info(f'   목표 거리: {self.target_dist}m')
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

        if self.locked_target_id is not None:
            for det in self.latest_detections:
                if det.track_id == self.locked_target_id:
                    return det
            self.locked_target_id = None
            self.lock_counter = 0
            self.get_logger().warn('🔓 락온 해제 - 타겟 lost')

        best_det = None
        best_center_dist = float('inf')

        for det in self.latest_detections:
            det_cx = (det.x_min + det.x_max) / 2
            det_cy = (det.y_min + det.y_max) / 2

            if det.x_min <= center_x <= det.x_max and det.y_min <= center_y <= det.y_max:
                dist_to_center = math.sqrt((det_cx - center_x)**2 + (det_cy - center_y)**2)
                if dist_to_center < best_center_dist:
                    best_center_dist = dist_to_center
                    best_det = det

        if best_det:
            self.lock_counter += 1
            if self.lock_counter >= self.lock_threshold:
                self.locked_target_id = best_det.track_id
                self.get_logger().info(f'🔒 락온 완료! Target ID: {self.locked_target_id}')
        else:
            self.lock_counter = max(0, self.lock_counter - 2)

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

        # 양수: 목표보다 멀다 (전진 필요)
        # 음수: 목표보다 가깝다 (정지)
        error_dist = current_distance - self.target_dist

        # [수정] 너무 가까우면 그냥 정지 (후진 안함)
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
        """STM32로 명령 전송 (전진/정지)"""
        if self.ser is None: return

        try:
            # 후진(r) 로직 제거됨
            if speed_z > 0:
                cmd = f"x={int(steer)}\nz={speed_z}\n"
            else:
                cmd = f"x={int(steer)}\nz=0\n" # 정지 시에도 조향은 유지 (선택사항)

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

        # 2. 긴급 정지
        if self.latest_distance is not None and self.latest_distance < self.emergency_stop_dist:
            self.get_logger().warn(f'🚨 긴급 정지! ({self.latest_distance:.2f}m)', throttle_duration_sec=0.5)
            self.emergency_stop()
            self.status_pub.publish(Int32(data=1))
            return

        # 3. 타겟 찾기
        target = self.get_target_detection()
        if target is None:
            self.send_motor_command(0, 0)
            self.get_logger().info(f'👀 탐색 중... ({self.lock_counter})', throttle_duration_sec=1.0)
            self.status_pub.publish(Int32(data=2))
            return

        # 4. 제어 계산
        steer_val = self.calculate_steer(target)
        
        current_dist = self.latest_distance
        if current_dist is None or current_dist <= 0:
            # 거리 없으면 비전 추정값 사용
            bbox_h = target.y_max - target.y_min
            if bbox_h > 10:
                current_dist = (1.7 * self.image_height) / (bbox_h * 2.0)
                current_dist = max(0.5, min(5.0, current_dist))

        # [수정] 속도 계산 (후진 제거됨)
        speed_z = self.calculate_speed_pid(current_dist)

        # 5. 명령 전송
        self.send_motor_command(steer_val, speed_z)

        # 6. 상태 발행
        self.steer_pub.publish(Float32(data=float(steer_val)))
        self.speed_pub.publish(Float32(data=float(speed_z)))
        self.status_pub.publish(Int32(data=3))

        lock_str = 'LOCKED' if self.locked_target_id is not None else 'UNLOCKED'
        dist_str = f'{self.latest_distance:.2f}m' if self.latest_distance else 'N/A'
        
        # 로그 간소화
        self.get_logger().info(
            f'🎯 {lock_str} | Steer:{steer_val:+.0f} | Spd:{speed_z} | Dist:{dist_str}',
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