#!/usr/bin/env python3
"""
Fake Odometry Publisher for Testing
실제 로봇 없이 테스트할 때 사용하는 가상 오도메트리 퍼블리셔
Cartographer는 오도메트리 없이도 동작 가능하지만, TF는 필요함
"""

import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry
from geometry_msgs.msg import TransformStamped
from tf2_ros import TransformBroadcaster
import math


class OdomPublisher(Node):
    def __init__(self):
        super().__init__('odom_publisher')

        self.declare_parameter('publish_rate', 50.0)
        self.declare_parameter('odom_frame', 'odom')
        self.declare_parameter('base_frame', 'base_link')

        self.odom_frame = self.get_parameter('odom_frame').value
        self.base_frame = self.get_parameter('base_frame').value
        rate = self.get_parameter('publish_rate').value

        # 퍼블리셔
        self.odom_pub = self.create_publisher(Odometry, '/odom', 10)

        # TF 브로드캐스터
        self.tf_broadcaster = TransformBroadcaster(self)

        # 타이머
        self.timer = self.create_timer(1.0 / rate, self.publish_odom)

        self.get_logger().info('Fake Odometry Publisher started (for testing without robot)')

    def publish_odom(self):
        """정적 오도메트리 퍼블리시 (위치 변화 없음)"""
        now = self.get_clock().now()

        # Odometry 메시지
        odom = Odometry()
        odom.header.stamp = now.to_msg()
        odom.header.frame_id = self.odom_frame
        odom.child_frame_id = self.base_frame

        # 정적 위치 (원점)
        odom.pose.pose.position.x = 0.0
        odom.pose.pose.position.y = 0.0
        odom.pose.pose.position.z = 0.0
        odom.pose.pose.orientation.w = 1.0

        self.odom_pub.publish(odom)

        # TF 브로드캐스트 (odom -> base_link)
        tf = TransformStamped()
        tf.header.stamp = now.to_msg()
        tf.header.frame_id = self.odom_frame
        tf.child_frame_id = self.base_frame
        tf.transform.rotation.w = 1.0

        self.tf_broadcaster.sendTransform(tf)


def main(args=None):
    rclpy.init(args=args)
    node = OdomPublisher()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
