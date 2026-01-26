#!/usr/bin/env python3
"""
Distance LiDAR Node (Pure ROS Version - QoS Fixed)
"""

import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data  # <--- [핵심] 이거 추가됨
from sensor_msgs.msg import LaserScan
from std_msgs.msg import Int32, Float32
import math
import threading

# 커스텀 메시지 확인
try:
    from rc_detection.msg import Detection, DetectionArray
except ImportError:
    DetectionArray = None

class DistanceLidarNode(Node):
    def __init__(self):
        super().__init__('distance_lidar_node')
        
        # 데이터 저장소
        self.latest_scan = None
        self.latest_detections = None
        self.scan_lock = threading.Lock()
        
        # 카메라 파라미터
        self.image_width = 640
        self.camera_fov = 60.0
        
        # [설정] 라이다-카메라 오프셋
        self.declare_parameter('lidar_camera_offset', 179.13)
        self.lidar_offset_deg = self.get_parameter('lidar_camera_offset').value
        
        # ==========================================
        # ROS 2 Subscribers
        # ==========================================
        # 1. 라이다 스캔 데이터 구독 (QoS 수정됨!)
        self.create_subscription(
            LaserScan,
            '/scan',
            self.scan_callback,
            qos_profile_sensor_data  # <--- [핵심] Best Effort 호환 설정
        )

        # 2. YOLO 감지 데이터 구독
        if DetectionArray is not None:
            self.create_subscription(
                DetectionArray,
                '/detections',
                self.detection_callback,
                10
            )
            
        # ==========================================
        # ROS 2 Publishers
        # ==========================================
        self.closest_id_pub = self.create_publisher(Int32, '/closest_object_id', 10)
        self.distance_pub = self.create_publisher(Float32, '/distance', 10)
        self.scan_min_pub = self.create_publisher(Float32, '/scan_min_dist', 10)
        
        # 계산 주기 (20Hz)
        self.create_timer(0.05, self.process_and_publish)
        
        self.get_logger().info('✅ Pure ROS Distance Node Started (QoS Fixed)')
        self.get_logger().info(f'   Offset: {self.lidar_offset_deg} deg')

    def scan_callback(self, msg):
        with self.scan_lock:
            self.latest_scan = msg
        self.publish_front_safety_dist(msg)

    def detection_callback(self, msg):
        self.latest_detections = msg.detections

    def publish_front_safety_dist(self, scan_msg):
        min_dist = float('inf')
        fov_rad = math.radians(20.0) 
        offset_rad = math.radians(self.lidar_offset_deg)

        angle_min = scan_msg.angle_min
        angle_inc = scan_msg.angle_increment
        
        for i, r in enumerate(scan_msg.ranges):
            if r < scan_msg.range_min or r > scan_msg.range_max:
                continue
            
            current_angle = angle_min + (i * angle_inc)
            corrected_angle = current_angle + offset_rad
            
            while corrected_angle > math.pi: corrected_angle -= 2*math.pi
            while corrected_angle <= -math.pi: corrected_angle += 2*math.pi
            
            if abs(corrected_angle) <= fov_rad:
                if r < min_dist:
                    min_dist = r
        
        msg = Float32()
        msg.data = min_dist if min_dist != float('inf') else -1.0
        self.scan_min_pub.publish(msg)

    def get_distance_from_lidar(self, center_x):
        with self.scan_lock:
            if self.latest_scan is None: return None
            scan = self.latest_scan
        
        pixel_offset = center_x - (self.image_width / 2.0)
        angle_offset_deg = pixel_offset * (self.camera_fov / self.image_width)
        
        target_deg = angle_offset_deg + self.lidar_offset_deg
        target_rad = math.radians(target_deg)
        
        while target_rad > math.pi: target_rad -= 2*math.pi
        while target_rad <= -math.pi: target_rad += 2*math.pi
        
        if scan.angle_increment == 0: return None
        target_index = int((target_rad - scan.angle_min) / scan.angle_increment)
        
        window = 3 
        valid_ranges = []
        
        for i in range(target_index - window, target_index + window + 1):
            if 0 <= i < len(scan.ranges):
                r = scan.ranges[i]
                if scan.range_min < r < scan.range_max:
                    valid_ranges.append(r)
        
        if valid_ranges:
            return sum(valid_ranges) / len(valid_ranges)
        return None

    def process_and_publish(self):
        if not self.latest_detections: return

        best_det = None
        min_dist = float('inf')

        for det in self.latest_detections:
            dist = self.get_distance_from_lidar(det.center_x)
            if dist and dist < min_dist:
                min_dist = dist
                best_det = det
        
        if best_det:
            id_msg = Int32()
            id_msg.data = int(best_det.track_id)
            self.closest_id_pub.publish(id_msg)
            
            dist_msg = Float32()
            dist_msg.data = float(min_dist)
            self.distance_pub.publish(dist_msg)

def main(args=None):
    rclpy.init(args=args)
    node = DistanceLidarNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt: pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()