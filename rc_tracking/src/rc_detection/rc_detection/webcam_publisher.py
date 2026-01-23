#!/usr/bin/env python3
"""
Simple Webcam Publisher Node
Publishes webcam images to /camera/image_raw topic
Works with laptop built-in cameras without external packages
"""

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image, CameraInfo
from cv_bridge import CvBridge
import cv2
import numpy as np


class WebcamPublisher(Node):
    def __init__(self):
        super().__init__('webcam_publisher')

        # Parameters
        self.declare_parameter('device_id', 0)
        self.declare_parameter('width', 640)
        self.declare_parameter('height', 480)
        self.declare_parameter('fps', 30)
        self.declare_parameter('frame_id', 'camera_link')

        device_id = self.get_parameter('device_id').value
        width = self.get_parameter('width').value
        height = self.get_parameter('height').value
        fps = self.get_parameter('fps').value
        frame_id = self.get_parameter('frame_id').value

        # Open camera
        self.get_logger().info(f'Opening camera device {device_id}...')
        self.cap = cv2.VideoCapture(device_id)

        if not self.cap.isOpened():
            self.get_logger().error(f'Failed to open camera {device_id}')
            self.get_logger().info('Available devices:')
            for i in range(5):
                test_cap = cv2.VideoCapture(i)
                if test_cap.isOpened():
                    self.get_logger().info(f'  - Device {i} is available')
                    test_cap.release()
            raise RuntimeError(f'Camera {device_id} not available')

        # Set camera properties
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        self.cap.set(cv2.CAP_PROP_FPS, fps)

        # Get actual properties (may differ from requested)
        actual_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        actual_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        actual_fps = int(self.cap.get(cv2.CAP_PROP_FPS))

        self.get_logger().info(f'Camera opened successfully')
        self.get_logger().info(f'Resolution: {actual_width}x{actual_height}')
        self.get_logger().info(f'FPS: {actual_fps}')

        # CV Bridge
        self.bridge = CvBridge()

        # Publishers
        self.image_pub = self.create_publisher(Image, '/camera/image_raw', 10)
        self.camera_info_pub = self.create_publisher(CameraInfo, '/camera/camera_info', 10)

        # Timer for publishing
        timer_period = 1.0 / fps
        self.timer = self.create_timer(timer_period, self.timer_callback)

        # Camera info message (simple pinhole model)
        self.camera_info_msg = CameraInfo()
        self.camera_info_msg.header.frame_id = frame_id
        self.camera_info_msg.width = actual_width
        self.camera_info_msg.height = actual_height

        # Simple camera matrix (approximate)
        fx = fy = float(actual_width)  # Focal length approximation
        cx = float(actual_width) / 2.0
        cy = float(actual_height) / 2.0

        self.camera_info_msg.k = [
            float(fx), 0.0, float(cx),
            0.0, float(fy), float(cy),
            0.0, 0.0, 1.0
        ]

        self.camera_info_msg.d = [0.0, 0.0, 0.0, 0.0, 0.0]  # No distortion
        self.camera_info_msg.r = [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0]
        self.camera_info_msg.p = [
            float(fx), 0.0, float(cx), 0.0,
            0.0, float(fy), float(cy), 0.0,
            0.0, 0.0, 1.0, 0.0
        ]

        self.frame_count = 0

    def timer_callback(self):
        """Capture and publish frame"""
        ret, frame = self.cap.read()

        if not ret:
            self.get_logger().warn('Failed to capture frame')
            return

        # Create ROS message
        timestamp = self.get_clock().now().to_msg()

        # Publish image
        try:
            img_msg = self.bridge.cv2_to_imgmsg(frame, encoding='bgr8')
            img_msg.header.stamp = timestamp
            img_msg.header.frame_id = self.camera_info_msg.header.frame_id
            self.image_pub.publish(img_msg)

            # Publish camera info
            self.camera_info_msg.header.stamp = timestamp
            self.camera_info_pub.publish(self.camera_info_msg)

            self.frame_count += 1
            if self.frame_count % 30 == 0:
                self.get_logger().info(
                    f'Published {self.frame_count} frames',
                    throttle_duration_sec=5.0
                )

        except Exception as e:
            self.get_logger().error(f'Error publishing frame: {str(e)}')

    def destroy_node(self):
        """Cleanup"""
        if self.cap is not None:
            self.cap.release()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)

    try:
        node = WebcamPublisher()
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f'Error: {e}')
        import traceback
        traceback.print_exc()
    finally:
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
