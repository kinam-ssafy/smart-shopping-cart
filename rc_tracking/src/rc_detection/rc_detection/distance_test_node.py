#!/usr/bin/env python3
"""
Distance Test Node
실시간으로 가장 큰 바운딩 박스 객체까지의 LiDAR 거리를 터미널에 표시
"""

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
from std_msgs.msg import Int32
import math

try:
    from rc_detection.msg import Detection, DetectionArray
    print("✅ Distance Test: Detection 메시지 import 성공")
except ImportError as e:
    print(f"❌ Distance Test: Detection 메시지 import 실패: {e}")
    DetectionArray = None


class DistanceTestNode(Node):
    def __init__(self):
        super().__init__('distance_test_node')
        
        # 최신 데이터 저장
        self.latest_scan = None
        self.latest_detections = None
        
        # 카메라 파라미터 (근사치)
        self.image_width = 640
        self.image_height = 480
        self.camera_fov = 60.0  # degrees (대략적인 웹캠 FOV)
        
        # Subscribers
        self.scan_sub = self.create_subscription(
            LaserScan,
            '/scan',
            self.scan_callback,
            10
        )
        
        if DetectionArray is not None:
            self.detection_sub = self.create_subscription(
                DetectionArray,
                '/detections',
                self.detection_callback,
                10
            )
        
        # Publisher for closest object ID
        self.closest_id_pub = self.create_publisher(
            Int32,
            '/closest_object_id',
            10
        )
        
        # Timer for periodic output
        self.timer = self.create_timer(0.5, self.print_distance)
        
        self.get_logger().info('Distance Test Node Started')
        self.get_logger().info('가장 가까운 객체를 빨간색으로 표시합니다')
        self.get_logger().info('=' * 60)
    
    def scan_callback(self, msg):
        """LiDAR 스캔 데이터 수신"""
        self.latest_scan = msg
    
    def detection_callback(self, msg):
        """객체 감지 데이터 수신"""
        self.latest_detections = msg.detections
    
    def get_distance_from_lidar(self, center_x, bbox_width):
        """
        바운딩 박스 중심점에 해당하는 LiDAR 거리 계산
        """
        if self.latest_scan is None:
            return None
        
        # 이미지 중심에서의 픽셀 오프셋 계산
        pixel_offset = center_x - (self.image_width / 2.0)
        
        # 픽셀 오프셋을 각도로 변환
        angle_per_pixel = self.camera_fov / self.image_width
        angle_offset = pixel_offset * angle_per_pixel
        angle_offset_rad = math.radians(angle_offset)
        
        # LiDAR 스캔에서 해당 각도의 인덱스 찾기
        # LiDAR는 -180도에서 +180도 범위
        # 카메라는 정면 방향 (0도 근처)
        target_angle = angle_offset_rad
        
        # LiDAR 스캔 인덱스 계산
        angle_min = self.latest_scan.angle_min
        angle_max = self.latest_scan.angle_max
        angle_increment = self.latest_scan.angle_increment
        
        # 각도를 인덱스로 변환
        if target_angle < angle_min or target_angle > angle_max:
            return None
        
        index = int((target_angle - angle_min) / angle_increment)
        
        if 0 <= index < len(self.latest_scan.ranges):
            distance = self.latest_scan.ranges[index]
            
            # 유효한 거리 범위 체크
            if self.latest_scan.range_min < distance < self.latest_scan.range_max:
                return distance
        
        # 주변 범위 평균으로 보정 (더 안정적)
        window = 10  # ±10 포인트
        start_idx = max(0, index - window)
        end_idx = min(len(self.latest_scan.ranges), index + window)
        
        valid_ranges = [
            r for r in self.latest_scan.ranges[start_idx:end_idx]
            if self.latest_scan.range_min < r < self.latest_scan.range_max
        ]
        
        if valid_ranges:
            return sum(valid_ranges) / len(valid_ranges)
        
        return None
    
    def print_distance(self):
        """터미널에 거리 정보 출력 - 가장 가까운 객체 기준"""
        if self.latest_detections is None or len(self.latest_detections) == 0:
            self.get_logger().info('대기 중... (객체 감지 없음)', throttle_duration_sec=2.0)
            # ID -1 발행 (객체 없음)
            msg = Int32()
            msg.data = -1
            self.closest_id_pub.publish(msg)
            return
        
        if self.latest_scan is None:
            self.get_logger().warn('LiDAR 데이터 없음 - 비전 기반 추정 사용', throttle_duration_sec=2.0)
            # LiDAR 없이 비전 기반 거리 추정
            self.estimate_distance_from_vision()
            return
        
        # 모든 객체의 거리 계산
        detections_with_distance = []
        
        for det in self.latest_detections:
            center_x = det.center_x
            bbox_width = det.x_max - det.x_min
            distance = self.get_distance_from_lidar(center_x, bbox_width)
            
            if distance is not None:
                detections_with_distance.append({
                    'detection': det,
                    'distance': distance
                })
        
        if not detections_with_distance:
            # LiDAR 거리 없으면 비전 기반
            self.estimate_distance_from_vision()
            return
        
        # 가장 가까운 객체 찾기
        closest = min(detections_with_distance, key=lambda x: x['distance'])
        closest_detection = closest['detection']
        closest_distance = closest['distance']
        
        # 가장 가까운 객체 ID 발행
        msg = Int32()
        msg.data = int(closest_detection.track_id)
        self.closest_id_pub.publish(msg)
        
        # 터미널 출력
        bbox_width = closest_detection.x_max - closest_detection.x_min
        bbox_height = closest_detection.y_max - closest_detection.y_min
        
        output = f'\n{"=" * 60}\n'
        output += f'🔴 CLOSEST OBJECT (빨간색 박스)\n'
        output += f'🎯 Track ID: {closest_detection.track_id}\n'
        output += f'📦 Class: {closest_detection.class_name}\n'
        output += f'📊 Confidence: {closest_detection.confidence:.2f}\n'
        output += f'📏 Bbox Size: {int(bbox_width)}x{int(bbox_height)} pixels\n'
        output += f'📍 Distance: {closest_distance:.2f} m (LiDAR)\n'
        
        # 다른 객체들 정보
        if len(detections_with_distance) > 1:
            output += f'\n🟢 Other objects: {len(detections_with_distance) - 1}\n'
            for item in detections_with_distance:
                if item['detection'].track_id != closest_detection.track_id:
                    output += f'  - ID {item["detection"].track_id}: {item["distance"]:.2f}m\n'
        
        output += f'{"=" * 60}'
        
        self.get_logger().info(output)
    
    def estimate_distance_from_bbox(self, detection):
        """바운딩 박스 크기로 거리 추정 (LiDAR 없을 때)"""
        bbox_height = detection.y_max - detection.y_min
        
        # 사람의 평균 키: 1.7m
        # 간단한 비율 계산
        # distance = (real_height * focal_length) / pixel_height
        # 근사치: focal_length ≈ image_height
        
        if bbox_height < 10:  # 너무 작은 박스는 제외
            return 10.0
        
        assumed_height = 1.7  # meters
        estimated_distance = (assumed_height * self.image_height) / (bbox_height * 2.0)
        
        return max(0.5, min(10.0, estimated_distance))  # 0.5m ~ 10m 범위로 제한
    
    def estimate_distance_from_vision(self):
        """비전만으로 거리 추정 - 가장 가까운 것으로 추정되는 객체"""
        if not self.latest_detections:
            return
        
        # 모든 객체의 추정 거리 계산
        detections_with_est = []
        for det in self.latest_detections:
            est_dist = self.estimate_distance_from_bbox(det)
            detections_with_est.append({
                'detection': det,
                'distance': est_dist
            })
        
        # 가장 가까운 객체
        closest = min(detections_with_est, key=lambda x: x['distance'])
        closest_detection = closest['detection']
        estimated_dist = closest['distance']
        
        # ID 발행
        msg = Int32()
        msg.data = int(closest_detection.track_id)
        self.closest_id_pub.publish(msg)
        
        output = f'\n{"=" * 60}\n'
        output += f'🔴 CLOSEST OBJECT (빨간색 박스)\n'
        output += f'🎯 Track ID: {closest_detection.track_id}\n'
        output += f'📦 Class: {closest_detection.class_name}\n'
        output += f'⚠️  LiDAR 없음 - 비전 기반 추정만 가능\n'
        output += f'📍 Distance: ~{estimated_dist:.2f} m (비전 추정)\n'
        output += f'{"=" * 60}'
        
        self.get_logger().info(output)


def main(args=None):
    rclpy.init(args=args)
    node = DistanceTestNode()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
