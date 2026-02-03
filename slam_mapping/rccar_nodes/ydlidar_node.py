#!/usr/bin/env python3
"""
YDLidar X4-Pro ROS2 Driver Node
타임스탬프 동기화 문제 수정 버전 - Cartographer 호환
"""

import rclpy
from rclpy.node import Node
from rclpy.time import Time
from sensor_msgs.msg import LaserScan
from geometry_msgs.msg import TransformStamped
from tf2_ros import TransformBroadcaster, StaticTransformBroadcaster
import math

try:
    import ydlidar
except ImportError:
    print("Error: YDLidar SDK not found")
    print("Install: cd ~/YDLidar-SDK/build && cmake .. && make && sudo make install")
    raise


class YDLidarNode(Node):
    def __init__(self):
        super().__init__('ydlidar_node')

        # 파라미터 선언
        self.declare_parameter('port', '/dev/ttyUSB0')
        self.declare_parameter('baudrate', 128000)
        self.declare_parameter('frame_id', 'laser')
        self.declare_parameter('range_min', 0.12)
        self.declare_parameter('range_max', 10.0)
        self.declare_parameter('frequency', 6.0)
        self.declare_parameter('sample_rate', 4)

        self.port = self.get_parameter('port').value
        self.baudrate = self.get_parameter('baudrate').value
        self.frame_id = self.get_parameter('frame_id').value
        self.range_min = self.get_parameter('range_min').value
        self.range_max = self.get_parameter('range_max').value
        self.frequency = self.get_parameter('frequency').value
        self.sample_rate = self.get_parameter('sample_rate').value

        # 퍼블리셔
        self.scan_pub = self.create_publisher(LaserScan, '/scan', 10)

        # TF 브로드캐스터
        self.tf_broadcaster = TransformBroadcaster(self)
        self.static_tf_broadcaster = StaticTransformBroadcaster(self)

        # Static TF 퍼블리시 (base_link -> laser)
        self.publish_static_transforms()

        # YDLidar
        self.laser = None
        self.scan_data = None
        self.initialized = False

        # 타임스탬프 순차성 보장
        self.last_stamp_ns = 0

        if self.init_lidar():
            timer_period = 1.0 / (self.frequency * 1.5)
            self.timer = self.create_timer(timer_period, self.scan_callback)
            self.get_logger().info(f'YDLidar started: {self.port}, frame: {self.frame_id}')
        else:
            self.get_logger().error('Failed to initialize YDLidar')

    def publish_static_transforms(self):
        """정적 TF 퍼블리시"""
        transforms = []

        # base_link -> laser
        t1 = TransformStamped()
        t1.header.stamp = self.get_clock().now().to_msg()
        t1.header.frame_id = 'base_link'
        t1.child_frame_id = 'laser'
        t1.transform.translation.z = 0.05
        t1.transform.rotation.w = 1.0
        transforms.append(t1)

        # base_footprint -> base_link
        t2 = TransformStamped()
        t2.header.stamp = self.get_clock().now().to_msg()
        t2.header.frame_id = 'base_footprint'
        t2.child_frame_id = 'base_link'
        t2.transform.translation.z = 0.025
        t2.transform.rotation.w = 1.0
        transforms.append(t2)

        self.static_tf_broadcaster.sendTransform(transforms)
        self.get_logger().info('Published static transforms')

    def init_lidar(self):
        """YDLidar 초기화"""
        try:
            ydlidar.os_init()
            self.laser = ydlidar.CYdLidar()

            ports = ydlidar.lidarPortList()
            port = self.port
            for k, v in ports.items():
                port = v
                self.get_logger().info(f'Found LiDAR: {port}')

            self.laser.setlidaropt(ydlidar.LidarPropSerialPort, port)
            self.laser.setlidaropt(ydlidar.LidarPropSerialBaudrate, self.baudrate)
            self.laser.setlidaropt(ydlidar.LidarPropLidarType, ydlidar.TYPE_TRIANGLE)
            self.laser.setlidaropt(ydlidar.LidarPropDeviceType, ydlidar.YDLIDAR_TYPE_SERIAL)
            self.laser.setlidaropt(ydlidar.LidarPropScanFrequency, self.frequency)
            self.laser.setlidaropt(ydlidar.LidarPropSampleRate, self.sample_rate)
            self.laser.setlidaropt(ydlidar.LidarPropSingleChannel, True)

            if self.laser.initialize() and self.laser.turnOn():
                self.scan_data = ydlidar.LaserScan()
                self.initialized = True
                return True
            return False

        except Exception as e:
            self.get_logger().error(f'Init error: {e}')
            return False

    def scan_callback(self):
        """LaserScan 퍼블리시 (타임스탬프 동기화)"""
        if not self.initialized:
            return

        if not self.laser.doProcessSimple(self.scan_data):
            return

        if self.scan_data.points.size() == 0:
            return

        # 현재 시간 (나노초)
        now = self.get_clock().now()
        current_ns = now.nanoseconds

        # 타임스탬프 순차성 보장 (최소 10ms 간격)
        min_interval_ns = 10_000_000  # 10ms
        if current_ns <= self.last_stamp_ns:
            current_ns = self.last_stamp_ns + min_interval_ns

        self.last_stamp_ns = current_ns

        # ROS Time 객체 생성
        stamp_time = Time(nanoseconds=current_ns)
        stamp = stamp_time.to_msg()

        # 먼저 TF 퍼블리시 (스캔보다 먼저!)
        self.publish_odom_tf(stamp)

        # LaserScan 메시지
        msg = LaserScan()
        msg.header.stamp = stamp
        msg.header.frame_id = self.frame_id

        msg.angle_min = self.scan_data.config.min_angle
        msg.angle_max = self.scan_data.config.max_angle
        msg.angle_increment = self.scan_data.config.angle_increment
        msg.time_increment = self.scan_data.config.time_increment
        msg.scan_time = self.scan_data.config.scan_time
        msg.range_min = self.range_min
        msg.range_max = self.range_max

        ranges = []
        intensities = []
        for p in self.scan_data.points:
            if self.range_min <= p.range <= self.range_max:
                ranges.append(p.range)
            else:
                ranges.append(float('inf'))
            intensities.append(float(p.intensity))

        msg.ranges = ranges
        msg.intensities = intensities

        self.scan_pub.publish(msg)

    def publish_odom_tf(self, stamp):
        """odom -> base_footprint TF (스캔과 동일한 타임스탬프)"""
        t = TransformStamped()
        t.header.stamp = stamp
        t.header.frame_id = 'odom'
        t.child_frame_id = 'base_footprint'
        t.transform.rotation.w = 1.0
        self.tf_broadcaster.sendTransform(t)

    def destroy_node(self):
        if self.laser:
            self.laser.turnOff()
            self.laser.disconnecting()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = YDLidarNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
