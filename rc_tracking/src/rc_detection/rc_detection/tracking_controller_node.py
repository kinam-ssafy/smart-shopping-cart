#!/usr/bin/env python3
"""
================================================================================
🚗 RC Car Tracking Controller Node (KKN Version - Active Brake)
================================================================================

기존 버전과의 차이점:
    ✅ r값 기반 능동 브레이크 시스템 추가
    ✅ 락온 ID를 LiDAR 노드에 동기화

STM32 프로토콜:
    - x = 조향각 (-30 ~ +30)
    - z = 전진 속도 (0 ~ 100)
    - r = 후진 속도 (0 ~ 100)

능동 브레이크 작동 원리:
    1. 거리 < emergency_stop_dist 감지 → 브레이크 시작
    2. BRAKE_DURATION 동안 r=BRAKE_POWER 전송 (후진 펄스)
    3. 시간 종료 후 → z=0, r=0 (완전 정지)
    
    기존 문제: z=0만 보내면 모터 힘만 풀려서 관성으로 밀림
    해결책: 짧은 시간 역방향(r값) 펄스로 능동 제동
================================================================================
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
TARGET_REAL_HEIGHT = 0.20


class TrackingControllerNodeKKN(Node):
    """
    능동 브레이크 + 락온 ID 동기화가 포함된 스마트 추적 컨트롤러
    """
    
    def __init__(self):
        super().__init__('tracking_controller_node_kkn')

        # ============================================================
        # ⚙️ ROS 파라미터 선언
        # ============================================================
        self.declare_parameter('serial_port', '/dev/ttyACM0')
        self.declare_parameter('baud_rate', 115200)
        self.declare_parameter('image_width', 640)
        self.declare_parameter('image_height', 480)
        self.declare_parameter('kp_steer', 0.18)  # 높이면 빠르게 조향
        self.declare_parameter('kd_steer', 0.02)  # ✅ PD 제어용 D항 / 높이면 더 부드럽게
        self.declare_parameter('max_steer', 30)
        self.declare_parameter('target_distance', 0.7)
        self.declare_parameter('kp_speed', 50.0)
        self.declare_parameter('ki_speed', 0.2)
        self.declare_parameter('kd_speed', 0.5)
        self.declare_parameter('max_speed', 80)
        self.declare_parameter('min_speed', 40)
        self.declare_parameter('stop_deadzone', 0.15)
        self.declare_parameter('emergency_stop_dist', 0.7)
        self.declare_parameter('safety_stop_dist', 0.4)  # ✅ 전방 장애물 안전 거리
        self.declare_parameter('watchdog_timeout', 1.5)
        self.declare_parameter('target_real_height', TARGET_REAL_HEIGHT)

        # 파라미터 로드
        self.serial_port = self.get_parameter('serial_port').value
        self.baud_rate = self.get_parameter('baud_rate').value
        self.image_width = self.get_parameter('image_width').value
        self.image_height = self.get_parameter('image_height').value
        self.kp_steer = self.get_parameter('kp_steer').value
        self.kd_steer = self.get_parameter('kd_steer').value  # ✅ PD 제어용
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

        # ============================================================
        # 📊 상태 변수
        # ============================================================
        self.latest_detections = None      # YOLO 감지 결과
        self.closest_object_id = None      # LiDAR가 보낸 가장 가까운 ID
        self.latest_distance = None        # LiDAR 거리
        self.last_cmd = None               # 마지막 시리얼 명령 (중복 방지)
        self.last_detection_time = time.time()
        self.last_distance_time = time.time()
        
        # ✅ [핵심] 유예 기간 중 속도 유지용
        self.last_speed_z = 0              # 마지막으로 발행한 속도
        self.last_steer_val = 0            # 마지막으로 발행한 조향각
        # ✅ Distance Jump Filter (급격한 거리 변화 방지)
        self.prev_distance = None
        self.DISTANCE_JUMP_THRESHOLD = 0.5  # 50% 이상 변화 무시
        
        # ✅ 전방 안전 거리 (장애물 충돌 방지)
        self.forward_min_dist = None
        self.safety_stop_dist = self.get_parameter('safety_stop_dist').value

        # ============================================================
        #  PID/PD 상태
        # ============================================================
        self.prev_error_dist = 0.0
        self.integral_dist = 0.0
        self.last_pid_time = time.time()
        self.prev_error_x = 0.0  # ✅ 조향 PD 제어용

        # ============================================================
        # 🎯 락온 상태
        # ============================================================
        self.locked_target_id = None   # 락온된 타겟 ID
        self.lock_counter = 0          # 중앙 체류 카운터
        self.lock_threshold = 45       # 락온까지 필요한 프레임 수
        
        # ✅ [핵심] 락온 유예 기간 - Detection 플리커링 방지
        # YOLO가 8Hz인데 Controller가 50Hz라서 Detection이 끊길 수 있음
        # 바로 락온 해제하지 않고 유예 기간 동안 대기
        self.lock_lost_counter = 8     # 연속 Detection 놓친 횟수
        self.LOCK_LOST_GRACE = 2      

        # ============================================================
        # 📏 Vision 거리 추정용 캘리브레이션
        # ============================================================
        self.ref_lidar_dist = None
        self.ref_bbox_height = None
        self.is_calibrated = False

        # ============================================================
        # 🔍 수색 모드 변수
        # ============================================================
        self.last_known_error_x = 0.0  # 마지막 타겟 X 오차 (픽셀)
        self.is_searching = False      # 수색 모드 여부
        self.search_end_time = 0.0     # 수색 종료 시간
        self.SEARCH_DURATION = 2.0     # 수색 지속 시간 (초)
        self.SEARCH_DEADZONE = 200      # 중앙 소실 판정 범위 (픽셀)

        # ============================================================
        # 🛑 [핵심] 능동 브레이크 시스템 (r값 사용)
        # ============================================================
        # 기존 문제: z=0은 모터 힘을 "풀어버리는" 것 → 관성으로 밀림
        # 해결책: 짧은 시간 동안 r값(후진)을 줘서 능동적으로 제동
        #
        # STM32 프로토콜:
        #   z = 전진 속도 (0~100)
        #   r = 후진 속도 (0~100)
        #
        # 작동 흐름:
        # 1. 긴급 정지 거리 감지 → is_braking = True
        # 2. BRAKE_DURATION 동안 r=BRAKE_POWER 전송
        # 3. 시간 종료 후 → r=0, z=0 (완전 정지)
        # ============================================================
        self.is_braking = False        # 브레이크 작동 중 여부
        self.brake_start_time = 0.0    # 브레이크 시작 시간
        self.BRAKE_DURATION = 0.15     # 후진 지속 시간 (초) - 조절 가능
        self.BRAKE_POWER = 40          # 후진 파워 (r값, 0~100) - 조절 가능
        # 
        # 🔧 튜닝 가이드:
        # - 차가 앞으로 밀림 → BRAKE_DURATION ↑ 또는 BRAKE_POWER ↑
        # - 차가 뒤로 감 → BRAKE_DURATION ↓ 또는 BRAKE_POWER ↓
        # ============================================================

        # ============================================================
        # 🔌 시리얼 초기화 (락온 후 연결)
        # ============================================================
        # ✅ 락온 전에는 STM32 연결 안 함 (락온 시 연결)
        self.ser = None


        # ============================================================
        # 📡 ROS Subscribers
        # ============================================================
        if DETECTION_MSG_AVAILABLE:
            self.detection_sub = self.create_subscription(
                DetectionArray, '/detections', self.detection_callback, 10)
        
        self.closest_id_sub = self.create_subscription(
            Int32, '/closest_object_id', self.closest_id_callback, 10)
        
        self.distance_sub = self.create_subscription(
            Float32, '/distance', self.distance_callback, 10)
        
        # ✅ 전방 안전 거리 구독 (충돌 방지)
        self.forward_dist_sub = self.create_subscription(
            Float32, '/scan_min_dist', self.forward_dist_callback, 10)

        # ============================================================
        # 📡 ROS Publishers
        # ============================================================
        self.steer_pub = self.create_publisher(Float32, '/control/steer', 10)
        self.speed_pub = self.create_publisher(Float32, '/control/speed', 10)
        self.status_pub = self.create_publisher(Int32, '/control/status', 10)
        
        # ✅ [핵심] 락온 타겟 ID를 LiDAR 노드에 전달
        # LiDAR 노드는 이 ID의 객체 거리만 측정 → 다른 객체 무시
        self.locked_target_pub = self.create_publisher(Int32, '/locked_target_id', 10)

        # 메인 제어 루프 (50Hz)
        self.control_timer = self.create_timer(0.02, self.control_loop)

        self.get_logger().info('🚗 KKN Controller Started (Active Brake + Lock ID Sync)')
        self.get_logger().info(f'   🛑 Brake: r={self.BRAKE_POWER} × {self.BRAKE_DURATION}s')

    # ================================================================
    # 🔌 시리얼 초기화
    # ================================================================
    def init_serial(self):
        """STM32와 시리얼 통신 연결"""
        try:
            ser = serial.Serial(self.serial_port, self.baud_rate, timeout=0.1)
            time.sleep(2)
            self.ser = ser
            self.get_logger().info(f'✅ STM32 연결 성공 ({self.serial_port})')
            # self.emergency_stop()
            return ser
        except Exception as e:
            self.get_logger().error(f'❌ STM32 연결 실패: {e}')
            return None

    # ================================================================
    # 📥 콜백 함수들
    # ================================================================
    def detection_callback(self, msg):
        self.latest_detections = msg.detections
        self.last_detection_time = time.time()

    def closest_id_callback(self, msg):
        self.closest_object_id = msg.data if msg.data >= 0 else None

    def distance_callback(self, msg):
        """LiDAR 거리 콜백 - 급변 필터 적용"""
        new_dist = msg.data
        
        # ✅ 거리 급변 필터: 이전 값 대비 50% 이상 변화하면 무시
        if self.prev_distance is not None and self.prev_distance > 0:
            ratio = new_dist / self.prev_distance
            # 0.5 ~ 2.0 범위 밖이면 급변으로 판단 → 무시
            if ratio < self.DISTANCE_JUMP_THRESHOLD or ratio > (1 / self.DISTANCE_JUMP_THRESHOLD):
                # 급변 무시, 이전 값 유지
                return
        
        # 유효한 거리 업데이트
        self.latest_distance = new_dist
        self.prev_distance = new_dist
        self.last_distance_time = time.time()

    def forward_dist_callback(self, msg):
        """전방 최소 거리 콜백 (장애물 충돌 방지용)"""
        self.forward_min_dist = msg.data

    # ================================================================
    # 🎯 타겟 선택 로직
    # ================================================================
    def get_target_detection(self):
        """추적할 타겟 Detection 선택"""
        if not self.latest_detections:
            return None

        center_x = self.image_width // 2
        center_y = self.image_height // 2

        # 1. 락온된 타겟 찾기
        if self.locked_target_id is not None:
            for det in self.latest_detections:
                if det.track_id == self.locked_target_id:
                    det_cx = (det.x_min + det.x_max) / 2
                    self.last_known_error_x = det_cx - center_x
                    self.lock_lost_counter = 0  # ✅ 찾았으면 카운터 리셋
                    return det
            
            # 락온 타겟 못 찾음 → 유예 기간 체크
            self.lock_lost_counter += 1
            
            if self.lock_lost_counter < self.LOCK_LOST_GRACE:
                # ✅ 아직 유예 기간 → 락온 유지하고 이전 정보로 계속 주행
                # (Detection 플리커링 방지)
                return "GRACE_PERIOD"  # 특수 플래그 반환
            
            # 유예 기간 초과 → 진짜로 락온 해제
            self.get_logger().warn(f'👋 타겟 소실! 마지막 오차: {self.last_known_error_x:.1f}')
            self.is_searching = True
            self.search_end_time = time.time() + self.SEARCH_DURATION
            self.locked_target_id = None
            self.lock_counter = 0
            self.lock_lost_counter = 0
            self.latest_distance = None # 락온 풀리면 거리 정보도 초기화
            self.is_calibrated = False
            return None

        # 2. 새로운 타겟 탐색 (화면 중앙의 객체)
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
                self.get_logger().info(f'🎯 락온 완료! ID: {self.locked_target_id}')
                
                # ✅ [핵심] 락온 완료 시 STM32 연결
                if self.ser is None:
                    self.ser = self.init_serial()
                    if self.ser:
                        self.get_logger().info('🔌 락온 후 STM32 연결 완료!')
        else:
            self.lock_counter = max(0, self.lock_counter - 2)

        # 3. 백업: LiDAR가 보낸 가장 가까운 객체
        if best_det is None and self.closest_object_id is not None:
            for det in self.latest_detections:
                if det.track_id == self.closest_object_id:
                    return det

        return best_det

    # ================================================================
    # 🎮 조향 계산 (PD 제어)
    # ================================================================
    def calculate_steer(self, target_det):
        """PD 제어기로 조향각 계산 (부드럽고 오버슈트 적음)"""
        if target_det is None: 
            return 0.0
        
        target_cx = (target_det.x_min + target_det.x_max) / 2
        center_x = self.image_width / 2
        error_x = target_cx - center_x
        
        # P항: 현재 오차에 비례
        p_term = self.kp_steer * error_x
        
        # D항: 오차 변화율에 비례 (급격한 조향 억제)
        d_term = self.kd_steer * (error_x - self.prev_error_x)
        self.prev_error_x = error_x
        
        steer_val = p_term + d_term
        steer_val = max(-self.max_steer, min(self.max_steer, steer_val))
        return steer_val

    # ================================================================
    # 🏎️ 속도 계산 (PID)
    # ================================================================
    def calculate_speed_pid(self, current_distance):
        """PID 제어기로 속도 계산 (min_speed 베이스 + PID)"""
        if current_distance is None or current_distance <= 0: 
            return 0
        
        current_time = time.time()
        dt = current_time - self.last_pid_time
        if dt <= 0: 
            dt = 0.02
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
        
        # ✅ 변경: min_speed를 베이스로, PID 결과를 더함
        # 항상 최소 속도(min_speed)에서 시작, 거리가 멀수록 증가
        speed_z = 0
        if output > 0:
            speed_z = int(self.min_speed + output)
            speed_z = min(speed_z, self.max_speed)  # max_speed 제한
        return speed_z

    # ================================================================
    # 📤 모터 명령 전송 함수들
    # ================================================================
    def send_motor_command(self, steer, speed_z):
        """
        [전진 명령] x=조향, z=전진속도 (r값 생략!)
        
        일반 주행에 사용 - 기존 방식 복원
        """
        if self.ser is None: 
            return
        try:
            # ✅ 기존 방식: r=0 생략, \n 사용
            cmd = f"x={int(steer)}\nz={int(speed_z)}\n"
            if cmd == self.last_cmd:
                return
            self.ser.write(cmd.encode())
            self.ser.flush()
            self.last_cmd = cmd
        except Exception as e:
            self.get_logger().error(f'시리얼 에러: {e}')
            self.last_cmd = None

    def send_brake_command(self, steer, brake_power):
        """
        [능동 브레이크 명령] 
        - 첫 번째: x=조향, z=0, r=후진 (전진 정지 후 후진)
        - 이후: x=조향, r=후진 (r만 전송)
        """
        if self.ser is None: 
            return
        try:
            if not getattr(self, 'brake_z_sent', False):
                # ✅ 첫 브레이크: z=0으로 전진 정지 + r값으로 후진
                cmd = f"x={int(steer)}\nz=0\nr={int(brake_power)}\n"
                self.brake_z_sent = True
            else:
                # ✅ 이후: r값만 전송
                cmd = f"x={int(steer)}\nr={int(brake_power)}\n"
            self.ser.write(cmd.encode())
            self.ser.flush()
            self.last_cmd = None  # 브레이크 후에는 새 명령 허용
        except Exception as e:
            self.get_logger().error(f'시리얼 에러: {e}')

    def stop_brake(self):
        """
        [브레이크 해제] r=0으로 후진 정지
        
        능동 브레이크 완료 후 호출
        """
        if self.ser is None: 
            return
        try:
            self.ser.write(b"r=0\n")
            self.ser.flush()
            self.brake_z_sent = False  # ✅ 다음 브레이크 시 z=0 다시 보내도록 리셋
        except Exception as e:
            self.get_logger().error(f'시리얼 에러: {e}')

    def emergency_stop(self):
        """
        [비상 정지] 모든 모터 즉시 정지
        
        Watchdog 타임아웃 등 비상 상황에서 호출
        """
        if self.ser:
            self.ser.write(b"x=0\r\nz=0\r\nr=0\r\n")
            self.ser.flush()
        self.integral_dist = 0
        self.is_braking = False
        self.last_cmd = None

    # ================================================================
    # 🔄 메인 제어 루프 (50Hz)
    # ================================================================
    def control_loop(self):
        """
        메인 제어 루프 - 0.02초(50Hz)마다 실행
        
        전체 흐름:
        1. 락온 ID를 LiDAR 노드에 발행
        2. Watchdog 체크
        3. 타겟 감지 및 거리 획득
        4. 조향/속도 계산
        5. 능동 브레이크 상태 머신
        6. 모터 명령 전송
        """
        current_time = time.time()

        # ============================================================
        # [0단계] 락온 타겟 ID를 LiDAR 노드에 발행
        # ============================================================
        # LiDAR 노드는 이 ID를 받아서 해당 객체의 거리만 측정
        lock_msg = Int32()
        lock_msg.data = self.locked_target_id if self.locked_target_id is not None else -1
        self.locked_target_pub.publish(lock_msg)

        # ============================================================
        # [1단계] Watchdog - 통신 끊김 감지
        # ============================================================
        if (current_time - self.last_detection_time) > self.watchdog_timeout:
            self.emergency_stop()
            self.status_pub.publish(Int32(data=0))
            return

        # ============================================================
        # [1.5단계] 🛡️ 전방 안전 브레이크 - 장애물 충돌 방지
        # ============================================================
        if self.forward_min_dist is not None and self.forward_min_dist > 0:
            if self.forward_min_dist < self.safety_stop_dist:
                # 전방에 뭔가 너무 가깝다! → 무조건 브레이크
                if not self.is_braking:
                    self.is_braking = True
                    self.brake_start_time = current_time
                    self.send_brake_command(0, self.BRAKE_POWER)
                    self.get_logger().warn(f'🛡️ 전방 장애물! 안전 브레이크 (거리: {self.forward_min_dist:.2f}m)')
                else:
                    elapsed = current_time - self.brake_start_time
                    if elapsed < self.BRAKE_DURATION:
                        self.send_brake_command(0, self.BRAKE_POWER)
                    else:
                        self.stop_brake()
                        self.send_motor_command(0, 0)
                return  # 안전 브레이크 중에는 다른 로직 무시

        # ============================================================
        # [2단계] 타겟 감지 및 거리 획득
        # ============================================================
        target = self.get_target_detection()
        final_dist = 0.0
        dist_source = "NONE"

        # ====================================================
        # 🟡 CASE 0: 유예 기간 → 이전 속도 유지
        # ====================================================
        if target == "GRACE_PERIOD":
            # 락온은 유지 중이지만 Detection이 일시적으로 끊김
            # 이전 속도와 조향을 그대로 유지!
            self.send_motor_command(self.last_steer_val, self.last_speed_z)
            self.steer_pub.publish(Float32(data=float(self.last_steer_val)))
            self.speed_pub.publish(Float32(data=float(self.last_speed_z)))
            self.get_logger().info(
                f'⏳ 유예({self.lock_lost_counter}/{self.LOCK_LOST_GRACE}) | St:{self.last_steer_val:.0f} | Sp:{self.last_speed_z}',
                throttle_duration_sec=0.5
            )
            return

        # ====================================================
        # 🟢 CASE 1: 타겟 발견 → 주행
        # ====================================================
        if target:
            # ✅ 수색 중 타겟 재발견 시 → 즉시 브레이크!
            was_searching = self.is_searching
            self.is_searching = False
            
            if was_searching:
                # 수색 중이었다면 급정지 후 재추적
                self.get_logger().info('🎯 수색 중 타겟 재발견! 브레이크 후 재추적')
                self.is_braking = True
                self.brake_start_time = current_time
                steer_val = self.calculate_steer(target)
                self.send_brake_command(steer_val, self.BRAKE_POWER)
                return  # 이번 사이클은 브레이크만
            
            # 거리 정보 획득 (LiDAR 우선, Vision 백업)
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

            # 조향 계산
            steer_val = self.calculate_steer(target)
            
            # ============================================================
            # [3단계] 속도 제어 + 능동 브레이크 상태 머신
            # ============================================================
            
            if self.locked_target_id is None:
                # 🔒 락온 대기 중 → 정지 상태 유지
                speed_z = 0
                dist_source = "LOCKING..."
                self.is_braking = False
                self.send_motor_command(steer_val, speed_z)
                
            elif final_dist > 0 and final_dist < self.emergency_stop_dist:
                # ============================================================
                # 🛑 긴급 정지 거리! → 능동 브레이크 작동
                # ============================================================
                
                if not self.is_braking:
                    # [브레이크 시작] r값으로 후진 펄스
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
                # 🚗 정상 주행 → PID 속도 제어
                if self.is_braking:
                    self.stop_brake()  # 후진 해제
                    self.is_braking = False
                speed_z = self.calculate_speed_pid(final_dist)
                self.send_motor_command(steer_val, speed_z)

            # ✅ 유예 기간용 마지막 값 저장
            self.last_speed_z = speed_z
            self.last_steer_val = steer_val

            # 상태 발행
            self.steer_pub.publish(Float32(data=float(steer_val)))
            self.speed_pub.publish(Float32(data=float(speed_z)))

            # 로그 출력
            lock_str = 'LOCKED' if self.locked_target_id else f'WAIT({self.lock_counter})'
            brake_str = ' [BRAKE]' if self.is_braking else ''
            self.get_logger().info(
                f'🎯 {lock_str}{brake_str} | St:{steer_val:.0f} | Sp:{speed_z} | D:{final_dist:.2f}m ({dist_source})',
                throttle_duration_sec=0.5
            )

        # ====================================================
        # 🔴 CASE 2: 타겟 소실 → 수색 or 대기
        # ====================================================
        else:
            # 브레이크 상태 리셋
            if self.is_braking:
                self.stop_brake()
                self.is_braking = False
            
            if self.is_searching and current_time < self.search_end_time:
                # 마지막 오차로 "가려짐" vs "도망감" 판단
                if abs(self.last_known_error_x) < self.SEARCH_DEADZONE:
                    # 🛡️ 중앙에서 사라짐 → 가려진 것으로 판단 → 제자리 대기
                    self.send_motor_command(0, 0)
                    self.get_logger().info('🛡️ 중앙 소실(가려짐?) → 대기 중...', throttle_duration_sec=0.5)
                else:
                    # 🔍 측면에서 사라짐 → 도망간 것으로 판단 → 회전 수색
                    search_dir = 1 if self.last_known_error_x > 0 else -1
                    steer_val = self.max_steer * search_dir
                    speed_z = self.min_speed
                    self.send_motor_command(steer_val, speed_z)
                    
                    direction_str = "RIGHT" if search_dir > 0 else "LEFT"
                    remaining = self.search_end_time - current_time
                    self.get_logger().info(f'🔍 {direction_str} 수색 중... ({remaining:.1f}s)', throttle_duration_sec=0.5)

            else:
                # 수색 시간 종료 → 새 타겟 대기
                self.is_searching = False
                self.send_motor_command(0, 0)
                self.status_pub.publish(Int32(data=2))
                self.get_logger().info(f'👀 탐색 중... ({self.lock_counter})', throttle_duration_sec=1.0)

    # ================================================================
    # 🧹 정리 함수
    # ================================================================
    def cleanup(self):
        """노드 종료 시 정리"""
        self.emergency_stop()
        if self.ser: 
            self.ser.close()
        self.get_logger().info('✅ Controller 종료')


# ================================================================
# 🚀 메인 함수
# ================================================================
def main(args=None):
    rclpy.init(args=args)
    node = TrackingControllerNodeKKN()
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

