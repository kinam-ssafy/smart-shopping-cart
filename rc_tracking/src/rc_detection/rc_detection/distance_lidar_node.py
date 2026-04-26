#!/usr/bin/env python3
"""
================================================================================
📡 Distance LiDAR Node - LiDAR 기반 거리 측정 노드
================================================================================

역할:
    - LiDAR 스캔 데이터와 카메라 Detection 데이터를 융합하여 객체 거리 측정
    - 락온된 타겟이 있으면 해당 타겟의 거리만 측정 (다른 객체 무시)
    - 락온된 타겟이 없으면 가장 가까운 객체의 거리 측정

토픽 구독:
    - /scan (LaserScan): YDLiDAR 스캔 데이터
    - /detections (DetectionArray): YOLO+DeepSORT 감지 결과
    - /locked_target_id (Int32): Controller가 추적 중인 타겟 ID

토픽 발행:
    - /distance (Float32): 타겟까지의 거리 (미터)
    - /closest_object_id (Int32): 가장 가까운 객체의 ID
    - /scan_min_dist (Float32): 전방 안전 거리 (충돌 방지용)

작동 원리:
    1. 카메라 픽셀 좌표 → LiDAR 각도로 변환 (카메라-LiDAR 캘리브레이션 필요)
    2. 해당 각도의 LiDAR 거리 데이터 추출
    3. 노이즈 방지를 위해 인접 각도 평균값 사용
================================================================================
"""

import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data  # LiDAR는 Best Effort QoS 사용
from sensor_msgs.msg import LaserScan
from std_msgs.msg import Int32, Float32
import math
import threading

# ============================================================
# 커스텀 메시지 import (빌드 후 사용 가능)
# ============================================================
try:
    from rc_detection.msg import Detection, DetectionArray
except ImportError:
    DetectionArray = None


class DistanceLidarNode(Node):
    """
    LiDAR 기반 거리 측정 노드
    
    핵심 기능:
    1. 락온 타겟 거리 우선 측정 (Controller와 동기화)
    2. 카메라 픽셀 → LiDAR 각도 변환
    3. 전방 안전 거리 모니터링
    """
    
    def __init__(self):
        super().__init__('distance_lidar_node')
        
        # ============================================================
        # 📦 데이터 저장소
        # ============================================================
        self.latest_scan = None          # 최신 LiDAR 스캔 데이터
        self.latest_detections = None    # 최신 Detection 목록
        self.scan_lock = threading.Lock() # 멀티스레드 안전을 위한 락
        
        # ============================================================
        # 📷 카메라 파라미터 (체커보드 캘리브레이션 결과 기반)
        # ============================================================
        # fx = 610.26 에서 FOV 계산: 2 * atan(640 / (2 * 610.26)) = 55.3°
        self.image_width = 640    # 카메라 해상도 가로
        self.camera_fov = 55.3    # 카메라 시야각 (캘리브레이션 기반)
        
        # ============================================================
        # 🔧 LiDAR-카메라 캘리브레이션 오프셋
        # ============================================================
        # LiDAR 0도와 카메라 중앙 사이의 각도 차이 (도)
        # 이 값은 캘리브레이션으로 측정해야 함
        self.declare_parameter('lidar_camera_offset', 179.13)
        self.lidar_offset_deg = self.get_parameter('lidar_camera_offset').value
        
        # ============================================================
        # 🔗 락온 타겟 ID (Controller와 동기화)
        # ============================================================
        # Controller가 /locked_target_id로 알려주면 여기에 저장
        # None이면 락온된 타겟 없음 → 가장 가까운 객체 거리 측정
        self.locked_target_id = None
        
        # ============================================================
        # 📡 ROS 2 Subscribers
        # ============================================================
        
        # 1. LiDAR 스캔 데이터 구독
        # - QoS: qos_profile_sensor_data (Best Effort, 센서 데이터용)
        # - YDLiDAR는 Best Effort로 발행하므로 이 설정 필수!
        self.create_subscription(
            LaserScan,
            '/scan',
            self.scan_callback,
            qos_profile_sensor_data
        )

        # 2. YOLO+DeepSORT 감지 결과 구독
        if DetectionArray is not None:
            self.create_subscription(
                DetectionArray,
                '/detections',
                self.detection_callback,
                10
            )

        # 3. 락온 타겟 ID 구독 (Controller → LiDAR)
        # - Controller가 "ID 5번 추적 중"이라고 알려주면 저장
        self.create_subscription(
            Int32,
            '/locked_target_id',
            self.locked_target_id_callback,
            10
        )
            
        # ============================================================
        # 📡 ROS 2 Publishers
        # ============================================================
        
        # 타겟 객체 ID 발행 (Controller가 참고)
        self.closest_id_pub = self.create_publisher(Int32, '/closest_object_id', 10)
        
        # 타겟까지의 거리 발행 (Controller가 속도 제어에 사용)
        self.distance_pub = self.create_publisher(Float32, '/distance', 10)
        
        # 전방 안전 거리 발행 (충돌 방지 모니터링용)
        self.scan_min_pub = self.create_publisher(Float32, '/scan_min_dist', 10)
        
        # ============================================================
        # ⏰ 메인 처리 타이머 (20Hz)
        # ============================================================
        self.create_timer(0.02, self.process_and_publish)
        
        # 시작 로그
        self.get_logger().info('✅ Distance LiDAR Node Started')
        self.get_logger().info(f'   📐 LiDAR-Camera Offset: {self.lidar_offset_deg}°')

    # ================================================================
    # 📥 콜백 함수들
    # ================================================================
    
    def scan_callback(self, msg):
        """
        LiDAR 스캔 데이터 수신 콜백
        
        - 스레드 안전을 위해 Lock 사용
        - 전방 안전 거리도 함께 계산하여 발행
        """
        with self.scan_lock:
            self.latest_scan = msg
        self.publish_front_safety_dist(msg)

    def detection_callback(self, msg):
        """
        YOLO+DeepSORT 감지 결과 수신 콜백
        
        - DetectionArray 메시지에서 detections 리스트 추출
        """
        self.latest_detections = msg.detections

    def locked_target_id_callback(self, msg):
        """
        락온 타겟 ID 수신 콜백 (Controller → LiDAR)
        
        - msg.data >= 0: 유효한 타겟 ID → 저장
        - msg.data < 0 (예: -1): 락온 해제 → None으로 설정
        
        이 값이 설정되면 process_and_publish()에서 해당 ID의 거리만 측정
        """
        self.locked_target_id = msg.data if msg.data >= 0 else None

    # ================================================================
    # 🛡️ 전방 안전 거리 계산
    # ================================================================
    
    def publish_front_safety_dist(self, scan_msg):
        """
        전방 ±20도 범위 내 최소 거리 계산 및 발행
        
        용도: 충돌 방지 모니터링 (객체 추적과 별개)
        """
        min_dist = float('inf')
        fov_rad = math.radians(20.0)  # 전방 ±20도
        offset_rad = math.radians(self.lidar_offset_deg)

        angle_min = scan_msg.angle_min
        angle_inc = scan_msg.angle_increment
        
        for i, r in enumerate(scan_msg.ranges):
            # 유효 범위 체크
            if r < scan_msg.range_min or r > scan_msg.range_max:
                continue
            
            # 현재 각도 계산 (오프셋 적용)
            current_angle = angle_min + (i * angle_inc)
            corrected_angle = current_angle + offset_rad
            
            # 각도를 -π ~ π 범위로 정규화
            while corrected_angle > math.pi: corrected_angle -= 2*math.pi
            while corrected_angle <= -math.pi: corrected_angle += 2*math.pi
            
            # 전방 범위 내인지 확인
            if abs(corrected_angle) <= fov_rad:
                if r < min_dist:
                    min_dist = r
        
        # 발행 (유효한 값이 없으면 -1)
        msg = Float32()
        msg.data = min_dist if min_dist != float('inf') else -1.0
        self.scan_min_pub.publish(msg)

    # ================================================================
    # 📏 픽셀 좌표 → LiDAR 거리 변환 (개선됨)
    # ================================================================
    
    def get_distance_from_lidar(self, center_x):
        """
        카메라 픽셀 X좌표를 LiDAR 각도로 변환하여 거리 측정
        (개선: 최소 거리 필터링 + 중앙값 사용)
        """
        with self.scan_lock:
            if self.latest_scan is None: 
                return None
            scan = self.latest_scan
        
        # [1단계] 픽셀 오프셋 계산
        pixel_offset = center_x - (self.image_width / 2.0)
        
        # [2단계] 각도 오프셋 계산 (도)
        angle_offset_deg = pixel_offset * (self.camera_fov / self.image_width)
        
        # [3단계] 최종 LiDAR 각도 계산
        target_deg = angle_offset_deg + self.lidar_offset_deg
        target_rad = math.radians(target_deg)
        
        # 각도를 -π ~ π 범위로 정규화
        while target_rad > math.pi: target_rad -= 2*math.pi
        while target_rad <= -math.pi: target_rad += 2*math.pi
        
        # [4단계] LiDAR 인덱스 계산
        if scan.angle_increment == 0: 
            return None
        target_index = int((target_rad - scan.angle_min) / scan.angle_increment)
        
        # [5단계] 거리 추출 (개선된 로직)
        window = 3  # ±3 인덱스 범위
        valid_ranges = []
        
        # ✅ [설정] 물리적 최소 거리 (이보다 가까우면 차체/노이즈로 간주하고 무시)
        PHYSICAL_MIN_DIST = 0.30  # 30cm 이하는 무시 (0.24m 노이즈 차단)
        
        for i in range(target_index - window, target_index + window + 1):
            # 인덱스 순환 처리 (LiDAR는 360도이므로 인덱스가 이어짐)
            idx = i % len(scan.ranges)
            
            r = scan.ranges[idx]
            # ✅ 최소/최대 거리 필터링 강화
            if r > PHYSICAL_MIN_DIST and r < scan.range_max:
                valid_ranges.append(r)
        
        if valid_ranges:
            # ✅ 평균(Mean) 대신 중앙값(Median) 사용 -> 튄 값 무시 효과 탁월
            valid_ranges.sort()
            return valid_ranges[len(valid_ranges) // 2]
            
        return None

    # ================================================================
    # 🎯 메인 처리 함수 (20Hz)
    # ================================================================
    
    def process_and_publish(self):
        """
        메인 처리 함수 - Detection과 LiDAR 데이터 융합
        
        동작 방식:
        1. 락온된 타겟이 있으면 → 그 타겟의 거리만 측정 후 즉시 종료
        2. 락온된 타겟이 없으면 → 모든 Detection 중 가장 가까운 객체 선택
        
        이 로직 덕분에:
        - 추적 중인 타겟 앞에 다른 사람이 지나가도 거리가 튀지 않음
        - 락온 전에는 가장 가까운 객체를 자연스럽게 추적
        """
        # Detection 데이터가 없으면 처리 불가
        if not self.latest_detections: 
            return

        # ============================================================
        # [1단계] 락온 타겟 우선 처리
        # ============================================================
        # Controller가 /locked_target_id로 "ID 5번 추적 중"이라고 알려주면
        # 다른 객체가 아무리 가까워도 무시하고 ID 5번의 거리만 측정
        if self.locked_target_id is not None:
            for det in self.latest_detections:
                # 락온된 타겟 ID와 일치하는 Detection 찾기
                if det.track_id == self.locked_target_id:
                    # 해당 객체의 화면 중심 X좌표로 LiDAR 거리 계산
                    dist = self.get_distance_from_lidar(det.center_x)
                    if dist:
                        # 거리 발행: /distance
                        self.distance_pub.publish(Float32(data=float(dist)))
                        # 객체 ID 발행: /closest_object_id
                        self.closest_id_pub.publish(Int32(data=int(det.track_id)))
                    # ✅ 락온 타겟을 처리했으면 즉시 함수 종료!
                    # 아래의 "가장 가까운 객체 찾기" 로직은 실행 안 함
                    return
            
            # ✅ [핵심 수정] 락온 상태인데 Detection에서 타겟 못 찾음
            # → 아무것도 발행하지 않고 종료! (이전 거리값 유지)
            # → 다른 객체의 거리를 잘못 발행하는 것 방지!
            return

        # ============================================================
        # [2단계] 락온 전 상태: 화면 중앙에 가장 가까운 객체 찾기
        # ============================================================
        # Controller는 중앙의 객체를 락온하므로, 락온 전에도 중앙 객체의 거리를 제공
        # (기존: LiDAR 거리가 가장 가까운 객체 → 변경: 화면 중앙에 가장 가까운 객체)
        
        best_det = None
        min_center_dist = float('inf')
        image_center_x = self.image_width / 2.0

        for det in self.latest_detections:
            # 화면 중앙과의 거리 계산
            det_cx = det.center_x
            center_distance = abs(det_cx - image_center_x)
            
            if center_distance < min_center_dist:
                min_center_dist = center_distance
                best_det = det
        
        # 중앙에 가장 가까운 객체 발행
        if best_det:
            lidar_dist = self.get_distance_from_lidar(best_det.center_x)
            if lidar_dist:
                id_msg = Int32()
                id_msg.data = int(best_det.track_id)
                self.closest_id_pub.publish(id_msg)
                
                dist_msg = Float32()
                dist_msg.data = float(lidar_dist)
                self.distance_pub.publish(dist_msg)


# ================================================================
# 🚀 메인 함수
# ================================================================

def main(args=None):
    rclpy.init(args=args)
    node = DistanceLidarNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt: 
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()