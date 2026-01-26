#!/usr/bin/env python3
"""
RC Car Tracking Controller Node
- YOLO+DeepSORT 감지 결과 구독
- LiDAR 거리 정보 구독
- PID 제어로 조향 및 속도 제어
- STM32로 모터 명령 전송
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

        # 시리얼 설정
        self.declare_parameter('serial_port', '/dev/ttyACM0')
        self.declare_parameter('baud_rate', 115200)

        # 카메라/이미지 설정
        self.declare_parameter('image_width', 640)
        self.declare_parameter('image_height', 480)

        # 조향 PID
        self.declare_parameter('kp_steer', 0.08)  # 조향 P게인
        self.declare_parameter('max_steer', 30)   # 최대 조향각

        # 속도 PID
        self.declare_parameter('target_distance', 0.8)  # 목표 거리 (m)
        self.declare_parameter('kp_speed', 60.0)        # 속도 P게인
        self.declare_parameter('ki_speed', 0.5)         # 속도 I게인
        self.declare_parameter('kd_speed', 10.0)        # 속도 D게인
        self.declare_parameter('max_speed', 100)         # 최대 속도
        self.declare_parameter('min_speed', 90)         # 최소 구동 속도

        # 안전 설정
        self.declare_parameter('stop_deadzone', 0.15)      # 목표 거리 ± 데드존
        self.declare_parameter('emergency_stop_dist', 0.5)  # 긴급 정지 거리
        self.declare_parameter('watchdog_timeout', 1.5)   # 통신 타임아웃

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

        # ==========================================
        # 상태 변수
        # ==========================================
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
        self.lock_threshold = 45  # 30프레임 유지 시 락온

        # ==========================================
        # 시리얼 초기화
        # ==========================================
        self.ser = self.init_serial()

        # ==========================================
        # ROS2 Subscribers
        # ==========================================
        if DETECTION_MSG_AVAILABLE:
            self.detection_sub = self.create_subscription(
                DetectionArray,
                '/detections',
                self.detection_callback,
                10
            )

        self.closest_id_sub = self.create_subscription(
            Int32,
            '/closest_object_id',
            self.closest_id_callback,
            10
        )

        self.distance_sub = self.create_subscription(
            Float32,
            '/distance',
            self.distance_callback,
            10
        )

        # ==========================================
        # ROS2 Publishers (상태 발행용)
        # ==========================================
        self.steer_pub = self.create_publisher(Float32, '/control/steer', 10)
        self.speed_pub = self.create_publisher(Float32, '/control/speed', 10)
        self.status_pub = self.create_publisher(Int32, '/control/status', 10)

        # ==========================================
        # 제어 타이머 (50Hz)
        # ==========================================
        self.control_timer = self.create_timer(0.02, self.control_loop)

        self.get_logger().info('=' * 50)
        self.get_logger().info('🚗 Tracking Controller Node 시작')
        self.get_logger().info(f'   목표 거리: {self.target_dist}m')
        self.get_logger().info(f'   긴급 정지: {self.emergency_stop_dist}m')
        self.get_logger().info('=' * 50)

    def init_serial(self):
        """STM32 시리얼 연결"""
        try:
            ser = serial.Serial(self.serial_port, self.baud_rate, timeout=0.1)
            time.sleep(2)  # 안정화 대기
            self.get_logger().info(f'✅ STM32 연결 성공 ({self.serial_port})')
            return ser
        except Exception as e:
            self.get_logger().error(f'❌ STM32 연결 실패: {e}')
            return None

    def detection_callback(self, msg):
        """감지 결과 수신"""
        self.latest_detections = msg.detections
        self.last_detection_time = time.time()

    def closest_id_callback(self, msg):
        """가장 가까운 객체 ID 수신"""
        self.closest_object_id = msg.data if msg.data >= 0 else None

    def distance_callback(self, msg):
        """거리 정보 수신"""
        self.latest_distance = msg.data
        self.last_distance_time = time.time()

    def get_target_detection(self):
        """추적 대상 객체 찾기"""
        if not self.latest_detections:
            return None

        center_x = self.image_width // 2
        center_y = self.image_height // 2

        # 락온된 타겟이 있으면 해당 ID 찾기
        if self.locked_target_id is not None:
            for det in self.latest_detections:
                if det.track_id == self.locked_target_id:
                    return det
            # 락온 타겟을 찾지 못함 -> 락온 해제
            self.locked_target_id = None
            self.lock_counter = 0
            self.get_logger().warn('🔓 락온 해제 - 타겟 lost')

        # 락온 없으면 화면 중앙에 있는 객체 찾기
        best_det = None
        best_center_dist = float('inf')

        for det in self.latest_detections:
            det_cx = (det.x_min + det.x_max) / 2
            det_cy = (det.y_min + det.y_max) / 2

            # 바운딩 박스가 화면 중앙점을 포함하는지 확인
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

        # closest_object_id 기반 폴백
        if best_det is None and self.closest_object_id is not None:
            for det in self.latest_detections:
                if det.track_id == self.closest_object_id:
                    return det

        return best_det

    def calculate_steer(self, target_det):
        """조향값 계산 (화면 중앙 기준)"""
        if target_det is None:
            return 0.0

        target_cx = (target_det.x_min + target_det.x_max) / 2
        center_x = self.image_width / 2

        # 에러: 타겟이 오른쪽이면 양수 (우회전), 왼쪽이면 음수 (좌회전)
        error_x = target_cx - center_x

        # P 제어
        steer_val = error_x * self.kp_steer

        # 범위 제한
        steer_val = max(-self.max_steer, min(self.max_steer, steer_val))

        return steer_val

    def calculate_speed_pid(self, current_distance):
        """속도 PID 제어 (목표 거리 유지)"""
        if current_distance is None or current_distance <= 0:
            return 0, 0

        current_time = time.time()
        dt = current_time - self.last_pid_time
        if dt <= 0:
            dt = 0.02
        self.last_pid_time = current_time

        # 거리 에러: 현재 거리 - 목표 거리
        # 양수: 목표보다 멀다 (전진 필요)
        # 음수: 목표보다 가깝다 (후진 필요)
        error_dist = current_distance - self.target_dist

        # 데드존 체크
        if abs(error_dist) < self.stop_deadzone:
            self.integral_dist = 0
            self.prev_error_dist = error_dist
            return 0, 0

        # PID 계산
        # P
        p_term = self.kp_speed * error_dist

        # I (적분 제한)
        self.integral_dist += error_dist * dt
        self.integral_dist = max(-50, min(50, self.integral_dist))
        i_term = self.ki_speed * self.integral_dist

        # D
        d_term = self.kd_speed * (error_dist - self.prev_error_dist) / dt
        self.prev_error_dist = error_dist

        # 전체 출력
        output = p_term + i_term + d_term

        # 전진/후진 분리
        speed_z = 0  # 전진
        speed_r = 0  # 후진

        if output > 0:
            # 전진
            speed_z = int(max(self.min_speed, min(self.max_speed, abs(output))))
        else:
            # 후진 (절반 속도)
            speed_r = int(max(self.min_speed, min(self.max_speed, abs(output) * 0.5)))

        return speed_z, speed_r

    def send_motor_command(self, steer, speed_z, speed_r):
        """STM32로 모터 명령 전송 (중복 명령 필터링 적용)"""
        if self.ser is None:
            return

        try:
            # 1. 명령 문자열 생성
            if speed_z > 0:
                cmd = f"x={int(steer)}\nz={speed_z}\n"
            elif speed_r > 0:
                cmd = f"x={int(steer)}\nr={speed_r}\n"
            else:
                cmd = f"x={int(steer)}\nz=0\n"

            # 2. [최적화] 이전 명령과 동일하면 전송하지 않음 (Skipping)
            if cmd == self.last_cmd:
                return

            # 3. 명령 전송 및 현재 명령 저장
            self.ser.write(cmd.encode())
            self.last_cmd = cmd  # 현재 보낸 명령을 저장해둠

        except Exception as e:
            self.get_logger().error(f'시리얼 전송 에러: {e}')
            # 에러 발생 시 last_cmd를 초기화하여 다음 루프에서 재시도할 수 있게 함
            self.last_cmd = None

    def emergency_stop(self):
        """긴급 정지"""
        if self.ser:
            self.ser.write(b"x=0\nz=0\nr=0\n")
        self.integral_dist = 0

    def control_loop(self):
        """메인 제어 루프"""
        current_time = time.time()

        # ==========================================
        # [1] Watchdog 체크
        # ==========================================
        detection_timeout = (current_time - self.last_detection_time) > self.watchdog_timeout

        if detection_timeout:
            self.get_logger().warn('🚨 감지 데이터 타임아웃 - 정지', throttle_duration_sec=1.0)
            self.emergency_stop()

            # 상태 발행
            status_msg = Int32()
            status_msg.data = 0  # STOPPED
            self.status_pub.publish(status_msg)
            return

        # ==========================================
        # [2] 거리 기반 긴급 정지
        # ==========================================
        if self.latest_distance is not None and self.latest_distance < self.emergency_stop_dist:
            self.get_logger().warn(
                f'🚨 충돌 방지 - 긴급 정지! ({self.latest_distance:.2f}m)',
                throttle_duration_sec=0.5
            )
            self.emergency_stop()

            status_msg = Int32()
            status_msg.data = 1  # EMERGENCY_STOP
            self.status_pub.publish(status_msg)
            return

        # ==========================================
        # [3] 타겟 찾기
        # ==========================================
        target = self.get_target_detection()

        if target is None:
            # 타겟 없음 -> 정지 (조향 유지)
            self.send_motor_command(0, 0, 0)

            self.get_logger().info(
                f'👀 타겟 탐색 중... (락온: {self.lock_counter}/{self.lock_threshold})',
                throttle_duration_sec=1.0
            )

            status_msg = Int32()
            status_msg.data = 2  # SEARCHING
            self.status_pub.publish(status_msg)
            return

        # ==========================================
        # [4] 조향 계산
        # ==========================================
        steer_val = self.calculate_steer(target)

        # ==========================================
        # [5] 속도 PID 계산
        # ==========================================
        # LiDAR 거리 우선, 없으면 비전 기반 추정
        current_dist = self.latest_distance

        if current_dist is None or current_dist <= 0:
            # 비전 기반 거리 추정 (bbox 높이 기준)
            bbox_height = target.y_max - target.y_min
            if bbox_height > 10:
                assumed_height = 1.7  # 사람 평균 키
                current_dist = (assumed_height * self.image_height) / (bbox_height * 2.0)
                current_dist = max(0.5, min(5.0, current_dist))

        speed_z, speed_r = self.calculate_speed_pid(current_dist)

        # ==========================================
        # [6] 명령 전송
        # ==========================================
        self.send_motor_command(steer_val, speed_z, speed_r)

        # ==========================================
        # [7] 상태 발행
        # ==========================================
        steer_msg = Float32()
        steer_msg.data = float(steer_val)
        self.steer_pub.publish(steer_msg)

        speed_msg = Float32()
        speed_msg.data = float(speed_z if speed_z > 0 else -speed_r)
        self.speed_pub.publish(speed_msg)

        status_msg = Int32()
        status_msg.data = 3  # TRACKING
        self.status_pub.publish(status_msg)

        # 로그
        if speed_z > 0:
            direction = "GO"
            speed_val = speed_z
        elif speed_r > 0:
            direction = "BACK"
            speed_val = speed_r
        else:
            direction = "STOP"
            speed_val = 0

        # 락온 상태 표시
        lock_status = f'🔒LOCKED' if self.locked_target_id is not None else f'🔓UNLOCKED({self.lock_counter}/{self.lock_threshold})'

        # 라이다 거리 정보
        lidar_dist_str = f'{self.latest_distance:.2f}m' if self.latest_distance is not None else 'N/A'

        self.get_logger().info(
            f'🎯 ID:{target.track_id} | {lock_status} | Steer:{steer_val:+.1f} | '
            f'{direction}:{speed_val} | Dist:{current_dist:.2f}m | LiDAR:{lidar_dist_str}',
            throttle_duration_sec=0.5
        )

    def cleanup(self):
        """종료 시 정리"""
        self.emergency_stop()
        if self.ser:
            self.ser.close()
        self.get_logger().info('✅ Controller 종료')


def main(args=None):
    rclpy.init(args=args)
    node = None

    try:
        node = TrackingControllerNode()
        rclpy.spin(node)
    except KeyboardInterrupt:
        print('\n🛑 종료 요청')
    except Exception as e:
        print(f'❌ 에러: {e}')
        import traceback
        traceback.print_exc()
    finally:
        if node:
            node.cleanup()
            node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
