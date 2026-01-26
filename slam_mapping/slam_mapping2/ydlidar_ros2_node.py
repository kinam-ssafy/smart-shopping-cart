#!/usr/bin/env python3
"""
YDLidar ROS2 Node - 독립 실행형
TF 동기화 문제 완전 수정 버전
"""

import sys
import os
import argparse
import math

import rclpy
from rclpy.node import Node
from rclpy.time import Time
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy
from sensor_msgs.msg import LaserScan
from geometry_msgs.msg import TransformStamped
from tf2_ros import TransformBroadcaster, StaticTransformBroadcaster

# YDLidar SDK - Dynamic path resolution
ydlidar_sdk_path = os.path.expanduser('~/YDLidar-SDK/build/python')
if os.path.exists(ydlidar_sdk_path):
    sys.path.insert(0, ydlidar_sdk_path)

try:
    import ydlidar
except ImportError:
    print("YDLidar SDK not found!")
    print("Install: cd ~/YDLidar-SDK/build && cmake .. && make")
    sys.exit(1)


class YDLidarROS2Node(Node):
    def __init__(self, port='/dev/ttyUSB0'):
        super().__init__('ydlidar_ros2_node')

        self.port = port
        self.frame_id = 'laser'

        # QoS 설정
        qos = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            durability=DurabilityPolicy.VOLATILE,
            depth=10
        )

        # 퍼블리셔
        self.scan_pub = self.create_publisher(LaserScan, '/scan', qos)

        # TF 브로드캐스터
        self.tf_broadcaster = TransformBroadcaster(self)
        self.static_tf_broadcaster = StaticTransformBroadcaster(self)

        # Static TF 퍼블리시 (한 번만)
        self.publish_static_tf()

        # YDLidar 초기화
        self.laser = None
        self.scan_data = None
        self.initialized = False

        # 타임스탬프 추적
        self.last_stamp_ns = 0

        if self.init_lidar():
            # 타이머 (약 10Hz)
            self.timer = self.create_timer(0.1, self.scan_loop)
            self.get_logger().info(f'YDLidar started on {self.port}')
        else:
            self.get_logger().error('Failed to init YDLidar')

    def publish_static_tf(self):
        """정적 TF 퍼블리시"""
        now = self.get_clock().now().to_msg()

        transforms = []

        # base_link -> laser
        t1 = TransformStamped()
        t1.header.stamp = now
        t1.header.frame_id = 'base_link'
        t1.child_frame_id = 'laser'
        t1.transform.translation.x = 0.0
        t1.transform.translation.y = 0.0
        t1.transform.translation.z = 0.05
        t1.transform.rotation.w = 1.0
        transforms.append(t1)

        # base_footprint -> base_link
        t2 = TransformStamped()
        t2.header.stamp = now
        t2.header.frame_id = 'base_footprint'
        t2.child_frame_id = 'base_link'
        t2.transform.translation.z = 0.025
        t2.transform.rotation.w = 1.0
        transforms.append(t2)

        self.static_tf_broadcaster.sendTransform(transforms)
        self.get_logger().info('Static TF published: base_footprint -> base_link -> laser')

    def init_lidar(self):
        """YDLidar 초기화"""
        try:
            ydlidar.os_init()
            self.laser = ydlidar.CYdLidar()

            # 포트 감지
            ports = ydlidar.lidarPortList()
            port = self.port
            for k, v in ports.items():
                port = v
                self.get_logger().info(f'Found LiDAR: {port}')

            # YDLidar X4-Pro 설정
            self.laser.setlidaropt(ydlidar.LidarPropSerialPort, port)
            self.laser.setlidaropt(ydlidar.LidarPropSerialBaudrate, 128000)
            self.laser.setlidaropt(ydlidar.LidarPropLidarType, ydlidar.TYPE_TRIANGLE)
            self.laser.setlidaropt(ydlidar.LidarPropDeviceType, ydlidar.YDLIDAR_TYPE_SERIAL)
            self.laser.setlidaropt(ydlidar.LidarPropScanFrequency, 6.0)
            self.laser.setlidaropt(ydlidar.LidarPropSampleRate, 4)
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
        """스캔 루프"""
        if not self.initialized:
            return

        if not self.laser.doProcessSimple(self.scan_data):
            return

        if self.scan_data.points.size() == 0:
            return

        # 현재 ROS 시간
        now = self.get_clock().now()
        current_ns = now.nanoseconds

        # 타임스탬프 순차성 보장
        if current_ns <= self.last_stamp_ns:
            current_ns = self.last_stamp_ns + 50_000_000  # +50ms

        self.last_stamp_ns = current_ns
        stamp = Time(nanoseconds=current_ns).to_msg()

        # 1. 먼저 odom -> base_footprint TF 퍼블리시
        self.publish_odom_tf(stamp)

        # 2. LaserScan 퍼블리시
        self.publish_scan(stamp)

    def publish_odom_tf(self, stamp):
        """odom -> base_footprint 동적 TF"""
        t = TransformStamped()
        t.header.stamp = stamp
        t.header.frame_id = 'odom'
        t.child_frame_id = 'base_footprint'
        t.transform.rotation.w = 1.0
        self.tf_broadcaster.sendTransform(t)

    def publish_scan(self, stamp):
        """LaserScan 메시지 퍼블리시"""
        msg = LaserScan()
        msg.header.stamp = stamp
        msg.header.frame_id = self.frame_id

        msg.angle_min = self.scan_data.config.min_angle
        msg.angle_max = self.scan_data.config.max_angle
        msg.angle_increment = self.scan_data.config.angle_increment
        msg.time_increment = self.scan_data.config.time_increment
        msg.scan_time = self.scan_data.config.scan_time
        msg.range_min = 0.12
        msg.range_max = 10.0

        ranges = []
        intensities = []
        for p in self.scan_data.points:
            if 0.12 <= p.range <= 10.0:
                ranges.append(p.range)
            else:
                ranges.append(float('inf'))
            intensities.append(float(p.intensity))

        msg.ranges = ranges
        msg.intensities = intensities

        self.scan_pub.publish(msg)

    def destroy_node(self):
        if self.laser:
            self.laser.turnOff()
            self.laser.disconnecting()
            self.get_logger().info('YDLidar disconnected')
        super().destroy_node()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', default='/dev/ttyUSB0', help='LiDAR port')
    args = parser.parse_args()

    rclpy.init()
    node = YDLidarROS2Node(port=args.port)

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
