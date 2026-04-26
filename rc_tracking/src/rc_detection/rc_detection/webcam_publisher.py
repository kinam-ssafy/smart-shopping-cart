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
import subprocess


class WebcamPublisher(Node):
    def __init__(self):
        super().__init__('webcam_publisher')

        # Parameters
        self.declare_parameter('device_id', 0)
        self.declare_parameter('width', 640)
        self.declare_parameter('height', 480)
        self.declare_parameter('fps', 30)
        self.declare_parameter('frame_id', 'camera_link')
        # ✅ v4l2 설정 파라미터
        self.declare_parameter('auto_exposure', True)  # True=자동, False=수동
        self.declare_parameter('exposure_value', 700)   # 수동 노출값 (1-5000)
        self.declare_parameter('auto_white_balance', True)  # True=자동, False=수동

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

        # ✅ v4l2 설정 적용 (노출/화이트밸런스 고정)
        self._apply_v4l2_settings(device_id)

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
        self.camera_info_msg.distortion_model = 'plumb_bob'

        # ✅ 실제 체커보드 캘리브레이션 값 적용
        self.camera_info_msg.k = [
            610.26342, 0.0, 315.92736,
            0.0, 613.56133, 227.36159,
            0.0, 0.0, 1.0
        ]

        self.camera_info_msg.d = [0.102756, -0.193953, -0.00135, 0.008299, 0.0]
        
        self.camera_info_msg.r = [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0]
        
        self.camera_info_msg.p = [
            617.87634, 0.0, 319.60332, 0.0,
            0.0, 624.29059, 226.34803, 0.0,
            0.0, 0.0, 1.0, 0.0
        ]

        self.frame_count = 0

    def _apply_v4l2_settings(self, device_id):
        """v4l2-ctl로 카메라 설정 고정 (빛 변화에 안정적)"""
        try:
            device_path = f'/dev/video{device_id}'
            auto_exp = self.get_parameter('auto_exposure').value
            exp_val = self.get_parameter('exposure_value').value
            auto_wb = self.get_parameter('auto_white_balance').value
            
            # 노출 설정
            if auto_exp:
                subprocess.run(['v4l2-ctl', '-d', device_path, '-c', 'auto_exposure=3'], 
                             capture_output=True, timeout=2)
                self.get_logger().info('📷 Auto exposure: ON')
            else:
                subprocess.run(['v4l2-ctl', '-d', device_path, '-c', 'auto_exposure=1'], 
                             capture_output=True, timeout=2)
                subprocess.run(['v4l2-ctl', '-d', device_path, '-c', f'exposure_time_absolute={exp_val}'], 
                             capture_output=True, timeout=2)
                self.get_logger().info(f'📷 Manual exposure: {exp_val}')
            
            # 화이트밸런스 설정
            wb_val = 1 if auto_wb else 0
            subprocess.run(['v4l2-ctl', '-d', device_path, '-c', f'white_balance_automatic={wb_val}'], 
                         capture_output=True, timeout=2)
            self.get_logger().info(f'📷 Auto white balance: {"ON" if auto_wb else "OFF"}')
            
        except Exception as e:
            self.get_logger().warn(f'v4l2 설정 실패 (무시됨): {e}')

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
