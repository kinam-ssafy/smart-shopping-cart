#!/usr/bin/env python3
"""
RC Car Tracking Controller Node (Smart Search & Recovery)
- 락온(Lock-on) 확정 전 대기
- 측면 소실 시 -> 회전 수색
- 중앙 소실 시 -> 제자리 대기 (가려짐 대비)
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
# 📏 [사용자 설정] 타겟 설정
# ==========================================
TARGET_REAL_HEIGHT = 0.15

class TrackingControllerNode(Node):
    def __init__(self):
        super().__init__('tracking_controller_node')

        # ... (파라미터 설정) ...
        self.declare_parameter('serial_port', '/dev/ttyACM0')
        self.declare_parameter('baud_rate', 115200)
        self.declare_parameter('image_width', 640)
        self.declare_parameter('image_height', 480)
        self.declare_parameter('kp_steer', 0.20)
        self.declare_parameter('max_steer', 30)
        self.declare_parameter('target_distance', 0.6)
        self.declare_parameter('kp_speed', 60.0)
        self.declare_parameter('ki_speed', 0.5)
        self.declare_parameter('kd_speed', 5.0)
        self.declare_parameter('max_speed', 100)
        self.declare_parameter('min_speed', 40)
        self.declare_parameter('stop_deadzone', 0.2)
        self.declare_parameter('emergency_stop_dist', 0.5)
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

        # 거리 추정용 기준값
        self.ref_lidar_dist = None
        self.ref_bbox_height = None
        self.is_calibrated = False

        # ✅ [수색 모드 변수]
        self.last_known_error_x = 0.0  # 마지막 타겟 위치 오차
        self.is_searching = False      # 수색 중 여부
        self.search_end_time = 0.0     # 수색 종료 시간
        self.SEARCH_DURATION = 2.0     # 수색 지속 시간 (초)
        self.SEARCH_DEADZONE = 50      # 픽셀 단위 (이 범위 안에서 사라지면 정지)

        # ============================================================
        # 🛑 [능동 브레이크 시스템] - r값 사용 (후진 속도)
        # ============================================================
        # 기존 문제: z=0 명령은 모터 힘을 "풀어버리는" 것 → 관성으로 밀림
        # 해결책: 짧은 시간 동안 r값(후진)을 줘서 능동적으로 제동
        # 
        # STM32 프로토콜:
        #   z = 전진 속도 (0~100)
        #   r = 후진 속도 (0~100)
        #   x = 조향각
        # ============================================================
        self.is_braking = False       # 현재 브레이크 작동 중인지 여부
        self.brake_start_time = 0.0   # 브레이크 시작 시간 기록
        self.BRAKE_DURATION = 0.15    # 후진 지속 시간 (0.25초 = 250ms)
        self.BRAKE_POWER = 30         # 후진 파워 (r값, 0~100)
        # 튜닝 가이드:
        # - 차가 너무 밀리면 → BRAKE_DURATION 늘리기 (0.3~0.4)
        # - 차가 뒤로 가면 → BRAKE_DURATION 줄이기 (0.15~0.2)
        # - 제동력 부족 시 → BRAKE_POWER 키우기 (60, 70)

        

        # 시리얼 초기화
        self.ser = self.init_serial()

        # ============================================================
        # 📡 ROS Subscribers (외부 데이터 수신)
        # ============================================================
        if DETECTION_MSG_AVAILABLE:
            # YOLO 노드로부터 감지된 객체 목록 수신
            self.detection_sub = self.create_subscription(
                DetectionArray, '/detections', self.detection_callback, 10)
        
        # LiDAR 노드로부터 가장 가까운 객체 ID 수신
        self.closest_id_sub = self.create_subscription(
            Int32, '/closest_object_id', self.closest_id_callback, 10)
        
        # LiDAR 노드로부터 거리 정보 수신 (락온된 타겟의 거리)
        self.distance_sub = self.create_subscription(
            Float32, '/distance', self.distance_callback, 10)

        # ============================================================
        # 📡 ROS Publishers (데이터 발행)
        # ============================================================
        self.steer_pub = self.create_publisher(Float32, '/control/steer', 10)
        self.speed_pub = self.create_publisher(Float32, '/control/speed', 10)
        self.status_pub = self.create_publisher(Int32, '/control/status', 10)
        
        # ✅ [핵심] 락온 타겟 ID를 LiDAR 노드에게 알려주는 Publisher
        # - LiDAR 노드는 이 ID를 받아서, 해당 객체의 거리만 측정함
        # - 덕분에 다른 가까운 객체가 있어도 락온 타겟 거리만 정확히 받음
        self.locked_target_pub = self.create_publisher(Int32, '/locked_target_id', 10)

        # 메인 제어 루프 (50Hz = 0.02초마다 실행)
        self.control_timer = self.create_timer(0.02, self.control_loop)

        self.get_logger().info('🚗 Smart Controller Started (Active Brake + Lock ID Sync)')

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

        # 1. 락온된 타겟 찾기
        if self.locked_target_id is not None:
            found = False
            for det in self.latest_detections:
                if det.track_id == self.locked_target_id:
                    # ✅ 마지막 위치 오차 업데이트
                    det_cx = (det.x_min + det.x_max) / 2
                    self.last_known_error_x = det_cx - center_x
                    return det
            
            # 2. 락온 타겟 놓침 -> 수색 모드 진입
            if not found:
                self.get_logger().warn(f'👋 타겟 소실! 마지막 오차: {self.last_known_error_x:.1f}')
                self.is_searching = True
                self.search_end_time = time.time() + self.SEARCH_DURATION
                
                self.locked_target_id = None
                self.lock_counter = 0
                self.is_calibrated = False
                return None

        # 3. 새로운 타겟 탐색
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
                self.is_searching = False
        else:
            self.lock_counter = max(0, self.lock_counter - 2)

        if best_det is None and self.closest_object_id is not None:
            for det in self.latest_detections:
                if det.track_id == self.closest_object_id:
                    return det

        return best_det

    def calculate_steer(self, target_det):
        if target_det is None: return 0.0
        
        target_cx = (target_det.x_min + target_det.x_max) / 2
        center_x = self.image_width / 2
        error_x = target_cx - center_x
        steer_val = error_x * self.kp_steer
        steer_val = max(-self.max_steer, min(self.max_steer, steer_val))
        return steer_val

    def calculate_speed_pid(self, current_distance):
        if current_distance is None or current_distance <= 0: return 0
        current_time = time.time()
        dt = current_time - self.last_pid_time
        if dt <= 0: dt = 0.02
        self.last_pid_time = current_time

        error_dist = current_distance - self.target_dist
        if error_dist < self.stop_deadzone:
            self.integral_dist = 0
            self.prev_error_dist = error_dist
            return 0

        p_term = self.kp_speed * error_dist
        self.integral_dist += error_dist * dt
        self.integral_dist = max(-50, min(50, self.integral_dist))
        i_term = self.ki_speed * self.integral_dist
        d_term = self.kd_speed * (error_dist - self.prev_error_dist) / dt
        self.prev_error_dist = error_dist
        output = p_term + i_term + d_term
        
        speed_z = 0
        if output > 0:
            speed_z = int(max(self.min_speed, min(self.max_speed, abs(output))))
        return speed_z

    def send_motor_command(self, steer, speed_z):
        """[전진 명령] x=조향, z=전진속도"""
        if self.ser is None: return
        try:
            cmd = f"x={int(steer)}\nz={speed_z}\n" if speed_z > 0 else f"x={int(steer)}\nz=0\n"
            if cmd == self.last_cmd: return
            self.ser.write(cmd.encode())
            self.last_cmd = cmd
        except Exception as e:
            self.get_logger().error(f'시리얼 에러: {e}')
            self.last_cmd = None

    def send_brake_command(self, steer, brake_power):
        """
        [능동 브레이크 명령] r값을 사용한 후진
        
        STM32에 z=0 + r=brake_power 전송
        - z=0: 전진 정지
        - r=brake_power: 후진 속도 (0~100)
        """
        if self.ser is None: return
        try:
            # z=0으로 전진 정지 + r값으로 후진
            cmd = f"x={int(steer)}\nz=0\nr={int(brake_power)}\n"
            self.ser.write(cmd.encode())
            self.last_cmd = None  # 브레이크 후에는 새 명령 허용
        except Exception as e:
            self.get_logger().error(f'시리얼 에러: {e}')

    def stop_brake(self):
        """[브레이크 해제] r=0으로 후진 정지"""
        if self.ser is None: return
        try:
            self.ser.write(b"r=0\n")
        except Exception as e:
            self.get_logger().error(f'시리얼 에러: {e}')

    def emergency_stop(self):
        """비상 정지 - 모든 모터 정지"""
        if self.ser: self.ser.write(b"x=0\nz=0\nr=0\n")
        self.integral_dist = 0
        self.is_braking = False

    def control_loop(self):
        current_time = time.time()

        # 1. Watchdog
        if (current_time - self.last_detection_time) > self.watchdog_timeout:
            self.emergency_stop()
            self.status_pub.publish(Int32(data=0))
            return

        # 2. 타겟 감지
        target = self.get_target_detection()
        final_dist = 0.0
        dist_source = "NONE"

        # ====================================================
        # 🟢 CASE 1: 타겟 발견 (주행)
        # ====================================================
        if target:
            self.is_searching = False
            
            bbox_h = target.y_max - target.y_min
            if self.latest_distance is not None and self.latest_distance > 0:
                final_dist = self.latest_distance
                dist_source = "LiDAR"
                if self.locked_target_id is not None and not self.is_calibrated and 0.2 < final_dist < 2.0:
                    self.ref_lidar_dist = final_dist
                    self.ref_bbox_height = bbox_h
                    self.is_calibrated = True
            else:
                if self.is_calibrated and bbox_h > 0:
                    final_dist = self.ref_lidar_dist * (self.ref_bbox_height / bbox_h)
                    dist_source = "Vision(Ref)"
                else:
                    if bbox_h > 10:
                        final_dist = (self.target_height_m * self.image_height) / (bbox_h * 2.0)
                        final_dist = max(0.2, min(5.0, final_dist))
                        dist_source = "Vision(Basic)"

            steer_val = self.calculate_steer(target)
            
            # ============================================================
            # 🛑 속도 제어 + 능동 브레이크 (r값 사용)
            # ============================================================
            if self.locked_target_id is None:
                # 락온 대기 중 → 정지
                speed_z = 0
                dist_source = "LOCKING..."
                self.is_braking = False
                self.send_motor_command(steer_val, speed_z)
                
            elif final_dist > 0 and final_dist < self.emergency_stop_dist:
                # ⚠️ 긴급 정지 거리! → 능동 브레이크
                if not self.is_braking:
                    # [브레이크 시작] r값으로 후진
                    self.is_braking = True
                    self.brake_start_time = current_time
                    self.send_brake_command(steer_val, self.BRAKE_POWER)
                    self.get_logger().warn(f'⛔ 급제동! r={self.BRAKE_POWER} (거리: {final_dist:.2f}m)')
                else:
                    # [브레이크 진행 중]
                    elapsed = current_time - self.brake_start_time
                    if elapsed < self.BRAKE_DURATION:
                        # 아직 후진 시간 → 계속 후진
                        self.send_brake_command(steer_val, self.BRAKE_POWER)
                    else:
                        # 후진 시간 끝 → 완전 정지
                        self.stop_brake()
                        self.send_motor_command(steer_val, 0)
                
                speed_z = 0  # 로그용
                
            else:
                # 정상 주행 → PID 속도 제어
                if self.is_braking:
                    self.stop_brake()  # 후진 해제
                    self.is_braking = False
                speed_z = self.calculate_speed_pid(final_dist)
                self.send_motor_command(steer_val, speed_z)

            self.steer_pub.publish(Float32(data=float(steer_val)))
            self.speed_pub.publish(Float32(data=float(speed_z)))

            lock_str = 'LOCKED' if self.locked_target_id else f'WAIT({self.lock_counter})'
            brake_str = ' [BRAKE]' if self.is_braking else ''
            self.get_logger().info(f'🎯 {lock_str}{brake_str} | St:{steer_val:.0f} | Sp:{speed_z} | D:{final_dist:.2f}m ({dist_source})', throttle_duration_sec=0.5)

        # ====================================================
        # 🔴 CASE 2: 타겟 소실 (수색 or 대기)
        # ====================================================
        else:
            # 타겟 소실 시 브레이크 상태 리셋
            if self.is_braking:
                self.stop_brake()
                self.is_braking = False
            
            if self.is_searching and current_time < self.search_end_time:
                
                # [핵심 로직] 중앙 근처에서 사라졌는지 판단
                if abs(self.last_known_error_x) < self.SEARCH_DEADZONE:
                    # 1. 중앙 소실 (가려짐/사람 끼어듦) -> 정지하고 대기
                    self.send_motor_command(0, 0)
                    self.get_logger().info(f'🛡️ 중앙 소실(가려짐?) -> 대기 중...', throttle_duration_sec=0.5)
                
                else:
                    # 2. 측면 소실 (도망감) -> 회전 수색
                    search_dir = 1 if self.last_known_error_x > 0 else -1
                    steer_val = self.max_steer * search_dir
                    speed_z = self.min_speed

                    self.send_motor_command(steer_val, speed_z)
                    
                    direction_str = "RIGHT" if search_dir > 0 else "LEFT"
                    self.get_logger().info(f'🔍 {direction_str} 수색 중... ({self.search_end_time - current_time:.1f}s)', throttle_duration_sec=0.5)

            else:
                # 수색 시간 종료
                self.is_searching = False
                self.send_motor_command(0, 0)
                self.status_pub.publish(Int32(data=2))
                self.get_logger().info(f'👀 탐색 중... ({self.lock_counter})', throttle_duration_sec=1.0)

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
