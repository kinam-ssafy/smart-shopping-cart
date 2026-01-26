#!/usr/bin/env python3
"""
Distance LiDAR Node
- LiDAR로 객체 거리 계산 및 발행 (/distance)
- 전방 안전 거리 감지 (/scan_min_dist)
"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import Int32, Float32
import math
import threading
import time
import sys

try:
    import ydlidar
    YDLIDAR_AVAILABLE = True
except ImportError:
    print("❌ ydlidar 모듈 없음")
    YDLIDAR_AVAILABLE = False
    sys.exit(1)

try:
    from rc_detection.msg import Detection, DetectionArray
except ImportError:
    DetectionArray = None


class DistanceLidarNode(Node):
    def __init__(self):
        super().__init__('distance_lidar_node')
        
        # 데이터 저장
        self.latest_scan = None
        self.latest_detections = None
        self.scan_lock = threading.Lock()
        
        # 카메라 파라미터
        self.image_width = 640
        self.camera_fov = 60.0
        
        # [수정] 오프셋 파라미터
        self.declare_parameter('lidar_camera_offset', 179.17)
        self.lidar_offset_deg = self.get_parameter('lidar_camera_offset').value

        # LiDAR 초기화
        self.laser = None
        self.lidar_thread = None
        self.running = False
        if not self.init_lidar():
            raise RuntimeError('LiDAR initialization failed')
        
        # Subscribers
        if DetectionArray is not None:
            self.create_subscription(DetectionArray, '/detections', self.detection_callback, 10)
        
        # [핵심] Publishers 추가
        self.closest_id_pub = self.create_publisher(Int32, '/closest_object_id', 10)
        self.distance_pub = self.create_publisher(Float32, '/distance', 10)       # 타겟 거리
        self.scan_min_pub = self.create_publisher(Float32, '/scan_min_dist', 10)  # 전방 장애물 거리
        
        # Timer
        self.create_timer(0.1, self.process_and_publish) # 10Hz로 변경 (반응 속도 향상)
        
        self.get_logger().info(f'✅ Distance Node 시작 (오프셋: {self.lidar_offset_deg}도)')

    def init_lidar(self):
        try:
            ydlidar.os_init()
            self.laser = ydlidar.CYdLidar()
            port = "/dev/ttyUSB0"  # 라이다 포트 확인 필요
            self.laser.setlidaropt(ydlidar.LidarPropSerialPort, port)
            self.laser.setlidaropt(ydlidar.LidarPropSerialBaudrate, 128000)
            self.laser.setlidaropt(ydlidar.LidarPropLidarType, ydlidar.TYPE_TRIANGLE)
            self.laser.setlidaropt(ydlidar.LidarPropDeviceType, ydlidar.YDLIDAR_TYPE_SERIAL)
            self.laser.setlidaropt(ydlidar.LidarPropScanFrequency, 8.0) # 주파수 상향
            self.laser.setlidaropt(ydlidar.LidarPropSampleRate, 4)
            self.laser.setlidaropt(ydlidar.LidarPropSingleChannel, True)
            
            if self.laser.initialize() and self.laser.turnOn():
                self.running = True
                self.lidar_thread = threading.Thread(target=self.lidar_scan_loop, daemon=True)
                self.lidar_thread.start()
                return True
            return False
        except Exception as e:
            self.get_logger().error(f'LiDAR Init Fail: {e}')
            return False

    def lidar_scan_loop(self):
        scan = ydlidar.LaserScan()
        while self.running and ydlidar.os_isOk():
            if self.laser.doProcessSimple(scan):
                with self.scan_lock:
                    self.latest_scan = {
                        'ranges': [p.range for p in scan.points],
                        'angles': [p.angle for p in scan.points]
                    }
                
                # [추가] 전방 부채꼴(±20도) 안전 거리 즉시 계산 및 발행
                self.publish_front_safety_dist(scan)
            else:
                time.sleep(0.001)

    def publish_front_safety_dist(self, scan):
        """전방 ±20도 내 가장 가까운 장애물 거리 발행 (안전장치용)"""
        min_dist = float('inf')
        FOV_HALF = 20.0
        
        for p in scan.points:
            r = p.range
            if r < 0.1: continue # 노이즈
            
            # 각도 변환 및 오프셋 적용
            deg = math.degrees(p.angle) + self.lidar_offset_deg
            # 정규화
            while deg > 180: deg -= 360
            while deg <= -180: deg += 360
            
            if abs(deg) <= FOV_HALF:
                if r < min_dist:
                    min_dist = r
        
        msg = Float32()
        msg.data = min_dist if min_dist != float('inf') else -1.0
        self.scan_min_pub.publish(msg)

    def detection_callback(self, msg):
        self.latest_detections = msg.detections

    def get_distance_from_lidar(self, center_x):
        """특정 픽셀(center_x) 방향의 LiDAR 거리 계산"""
        with self.scan_lock:
            if self.latest_scan is None: return None
            ranges = self.latest_scan['ranges']
            angles = self.latest_scan['angles']
        
        # 픽셀 -> 각도 변환
        pixel_offset = center_x - (self.image_width / 2.0)
        angle_offset = pixel_offset * (self.camera_fov / self.image_width)
        target_deg = angle_offset + self.lidar_offset_deg
        
        # 정규화
        while target_deg > 180: target_deg -= 360
        while target_deg <= -180: target_deg += 360
        
        target_rad = math.radians(target_deg)
        window_rad = math.radians(3.0) # ±3도 오차 허용
        
        valid_ranges = []
        for i, a in enumerate(angles):
            # 각도 차이 (Wrap-around 처리)
            diff = abs(a - target_rad)
            if diff > math.pi: diff = 2*math.pi - diff
            
            if diff < window_rad:
                r = ranges[i]
                if 0.1 < r < 10.0: valid_ranges.append(r)
        
        if valid_ranges:
            return sum(valid_ranges) / len(valid_ranges)
        return None

    def process_and_publish(self):
        """가장 가까운 객체 거리 계산 및 발행"""
        if not self.latest_detections: return

        best_det = None
        min_dist = float('inf')

        # 감지된 모든 객체 중 가장 가까운 놈 찾기
        for det in self.latest_detections:
            dist = self.get_distance_from_lidar(det.center_x)
            if dist and dist < min_dist:
                min_dist = dist
                best_det = det
        
        if best_det:
            # 1. ID 발행
            id_msg = Int32()
            id_msg.data = int(best_det.track_id)
            self.closest_id_pub.publish(id_msg)
            
            # 2. [핵심] 거리 발행 (/distance) -> 이게 없어서 N/A 였음
            dist_msg = Float32()
            dist_msg.data = float(min_dist)
            self.distance_pub.publish(dist_msg)

    def cleanup(self):
        self.running = False
        if self.laser:
            self.laser.turnOff()
            self.laser.disconnecting()

def main(args=None):
    rclpy.init(args=args)
    node = DistanceLidarNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.cleanup()
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()