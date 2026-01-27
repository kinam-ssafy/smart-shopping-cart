#!/usr/bin/env python3
"""
YDLidar Simple Node - TF 문제 완전 해결
Cartographer가 모든 TF를 관리하도록 최소한의 TF만 퍼블리시
"""

import sys
import os
import argparse
import math
import time

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy
from sensor_msgs.msg import LaserScan
from geometry_msgs.msg import TransformStamped
from visualization_msgs.msg import Marker
from tf2_ros import StaticTransformBroadcaster

# Dynamic path resolution for YDLidar SDK
ydlidar_sdk_path = os.path.expanduser('~/YDLidar-SDK/build/python')
if os.path.exists(ydlidar_sdk_path):
    sys.path.insert(0, ydlidar_sdk_path)

try:
    import ydlidar
except ImportError:
    print("YDLidar SDK not found!")
    sys.exit(1)


class YDLidarSimpleNode(Node):
    def __init__(self, port='/dev/ttyUSB0'):
        super().__init__('ydlidar_simple_node')

        self.port = port

        # QoS - Cartographer와 호환
        qos = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            durability=DurabilityPolicy.VOLATILE,
            depth=10
        )

        # LaserScan 퍼블리셔
        self.scan_pub = self.create_publisher(LaserScan, '/scan', qos)

        # 로봇 마커 퍼블리셔 (RViz에서 로봇 위치 표시)
        self.marker_pub = self.create_publisher(Marker, '/robot_marker', 10)

        # Static TF만 사용 (base_link -> laser)
        self.static_tf_broadcaster = StaticTransformBroadcaster(self)
        self.publish_static_tf()

        # YDLidar
        self.laser = None
        self.scan_data = None
        self.initialized = False
        self.scan_count = 0

        # 모노토닉 타임스탬프 (절대 뒤로 가지 않음)
        self.start_time_mono = time.monotonic_ns()
        self.start_time_ros = self.get_clock().now().nanoseconds
        self.last_stamp_ns = 0

        if self.init_lidar():
            # 빠른 폴링 (LiDAR 주파수에 맞춤)
            self.timer = self.create_timer(0.05, self.scan_loop)  # 20Hz 폴링
            self.get_logger().info(f'YDLidar ready on {self.port}')
        else:
            self.get_logger().error('Failed to init YDLidar')

    def publish_static_tf(self):
        """base_link -> laser 정적 TF (한 번만)"""
        t = TransformStamped()
        t.header.stamp = self.get_clock().now().to_msg()
        t.header.frame_id = 'base_link'
        t.child_frame_id = 'laser'
        t.transform.translation.z = 0.0  # 같은 높이
        t.transform.rotation.w = 1.0
        self.static_tf_broadcaster.sendTransform(t)
        self.get_logger().info('Static TF: base_link -> laser')

    def publish_robot_marker(self, stamp_sec, stamp_nanosec):
        """로봇 위치에 원형 마커 퍼블리시"""
        marker = Marker()
        marker.header.frame_id = 'base_link'
        marker.header.stamp.sec = stamp_sec
        marker.header.stamp.nanosec = stamp_nanosec
        marker.ns = 'robot'
        marker.id = 0
        marker.type = Marker.CYLINDER
        marker.action = Marker.ADD
        marker.pose.position.z = 0.05
        marker.pose.orientation.w = 1.0
        marker.scale.x = 0.3  # 직경 30cm
        marker.scale.y = 0.3
        marker.scale.z = 0.1  # 높이 10cm
        marker.color.r = 0.0
        marker.color.g = 0.5
        marker.color.b = 1.0
        marker.color.a = 0.8
        self.marker_pub.publish(marker)

    def init_lidar(self):
        """YDLidar 초기화"""
        try:
            ydlidar.os_init()
            self.laser = ydlidar.CYdLidar()

            ports = ydlidar.lidarPortList()
            port = self.port
            for k, v in ports.items():
                port = v
                self.get_logger().info(f'Found: {port}')

            self.laser.setlidaropt(ydlidar.LidarPropSerialPort, port)
            self.laser.setlidaropt(ydlidar.LidarPropSerialBaudrate, 128000)
            self.laser.setlidaropt(ydlidar.LidarPropLidarType, ydlidar.TYPE_TRIANGLE)
            self.laser.setlidaropt(ydlidar.LidarPropDeviceType, ydlidar.YDLIDAR_TYPE_SERIAL)
            self.laser.setlidaropt(ydlidar.LidarPropScanFrequency, 8.0)  # 더 빠른 스캔
            self.laser.setlidaropt(ydlidar.LidarPropSampleRate, 5)  # 더 많은 샘플
            self.laser.setlidaropt(ydlidar.LidarPropSingleChannel, True)

            if self.laser.initialize() and self.laser.turnOn():
                self.scan_data = ydlidar.LaserScan()
                self.initialized = True
                return True
            return False

        except Exception as e:
            self.get_logger().error(f'Init error: {e}')
            return False

    def scan_loop(self):
        """스캔 퍼블리시 (모노토닉 타임스탬프 - 절대 뒤로 가지 않음)"""
        if not self.initialized:
            return

        if not self.laser.doProcessSimple(self.scan_data):
            return

        num_points = self.scan_data.points.size()
        if num_points == 0:
            return

        # 모노토닉 시간 기반 타임스탬프 (절대 뒤로 가지 않음)
        mono_elapsed = time.monotonic_ns() - self.start_time_mono
        current_ns = self.start_time_ros + mono_elapsed

        # 추가 안전장치: 최소 1ms 간격 보장
        min_interval_ns = 1_000_000  # 1ms
        if current_ns <= self.last_stamp_ns:
            current_ns = self.last_stamp_ns + min_interval_ns

        self.last_stamp_ns = current_ns

        # 타임스탬프 생성
        stamp_sec = current_ns // 1_000_000_000
        stamp_nanosec = current_ns % 1_000_000_000

        # LaserScan 메시지
        msg = LaserScan()
        msg.header.stamp.sec = stamp_sec
        msg.header.stamp.nanosec = stamp_nanosec
        msg.header.frame_id = 'laser'

        msg.angle_min = self.scan_data.config.min_angle
        msg.angle_max = self.scan_data.config.max_angle
        msg.angle_increment = self.scan_data.config.angle_increment
        msg.time_increment = self.scan_data.config.time_increment
        msg.scan_time = self.scan_data.config.scan_time
        msg.range_min = 0.1
        msg.range_max = 12.0

        ranges = []
        intensities = []

        # 스캔 포인트 처리 (최대 720개로 제한하여 버퍼 오버플로우 방지)
        points_list = list(self.scan_data.points)
        max_points = 720
        step = max(1, len(points_list) // max_points)

        for i in range(0, len(points_list), step):
            p = points_list[i]
            r = p.range
            if 0.1 <= r <= 12.0 and math.isfinite(r):
                ranges.append(r)
            else:
                ranges.append(float('inf'))
            intensities.append(float(p.intensity))

        # angle_increment 조정 (다운샘플링에 맞게)
        if step > 1 and len(ranges) > 1:
            total_angle = msg.angle_max - msg.angle_min
            msg.angle_increment = total_angle / (len(ranges) - 1)

        msg.ranges = ranges
        msg.intensities = intensities

        self.scan_pub.publish(msg)

        # 로봇 마커 퍼블리시
        self.publish_robot_marker(stamp_sec, stamp_nanosec)

        self.scan_count += 1
        if self.scan_count % 100 == 0:
            self.get_logger().info(f'Scans: {self.scan_count}, Points: {num_points}')

    def destroy_node(self):
        if self.laser:
            self.laser.turnOff()
            self.laser.disconnecting()
        super().destroy_node()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', default='/dev/ttyUSB0')
    args = parser.parse_args()

    rclpy.init()
    node = YDLidarSimpleNode(port=args.port)

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
