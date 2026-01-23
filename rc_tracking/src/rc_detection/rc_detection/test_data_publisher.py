#!/usr/bin/env python3
"""
Test node to publish fake camera and LiDAR data
Useful for testing the fusion pipeline without real sensors
"""

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image, PointCloud2, PointField, CameraInfo
from std_msgs.msg import Header
import numpy as np
import cv2
from cv_bridge import CvBridge
import struct


class TestDataPublisher(Node):
    def __init__(self):
        super().__init__('test_data_publisher')
        
        # Publishers
        self.image_pub = self.create_publisher(Image, '/camera/image_raw', 10)
        self.camera_info_pub = self.create_publisher(CameraInfo, '/camera/camera_info', 10)
        self.pointcloud_pub = self.create_publisher(PointCloud2, '/scan_points', 10)
        
        # CV Bridge
        self.bridge = CvBridge()
        
        # Timers
        self.create_timer(0.1, self.publish_image)  # 10 Hz
        self.create_timer(0.1, self.publish_pointcloud)  # 10 Hz
        
        self.get_logger().info('Test data publisher started')
    
    def publish_image(self):
        """Publish a test image with a colored rectangle (simulating detected object)"""
        # Create blank image
        img = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # Draw background
        img[:] = (50, 50, 50)
        
        # Draw a moving rectangle (simulating an object)
        t = self.get_clock().now().nanoseconds / 1e9
        x = int(320 + 150 * np.sin(t * 0.5))
        y = 240
        
        cv2.rectangle(img, (x - 40, y - 60), (x + 40, y + 60), (0, 255, 0), -1)
        cv2.putText(img, 'Test Object', (x - 35, y), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
        
        # Convert to ROS message
        msg = self.bridge.cv2_to_imgmsg(img, encoding='bgr8')
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = 'camera_link'
        
        self.image_pub.publish(msg)
        
        # Publish camera info
        camera_info = CameraInfo()
        camera_info.header = msg.header
        camera_info.height = 480
        camera_info.width = 640
        camera_info.distortion_model = 'plumb_bob'
        camera_info.d = [0.0, 0.0, 0.0, 0.0, 0.0]
        camera_info.k = [500.0, 0.0, 320.0,
                        0.0, 500.0, 240.0,
                        0.0, 0.0, 1.0]
        camera_info.r = [1.0, 0.0, 0.0,
                        0.0, 1.0, 0.0,
                        0.0, 0.0, 1.0]
        camera_info.p = [500.0, 0.0, 320.0, 0.0,
                        0.0, 500.0, 240.0, 0.0,
                        0.0, 0.0, 1.0, 0.0]
        
        self.camera_info_pub.publish(camera_info)
    
    def publish_pointcloud(self):
        """Publish a test point cloud (simulating LiDAR scan)"""
        points = []
        
        # Create a simple point cloud (semi-circle in front)
        t = self.get_clock().now().nanoseconds / 1e9
        center_x = 1.0 + 0.3 * np.sin(t * 0.5)
        
        # Points around the object
        for angle in np.linspace(-np.pi/2, np.pi/2, 50):
            x = center_x + 0.3 * np.cos(angle)
            y = 0.3 * np.sin(angle)
            z = 0.0
            points.append([x, y, z])
        
        # Create PointCloud2 message
        header = Header()
        header.stamp = self.get_clock().now().to_msg()
        header.frame_id = 'laser_frame'
        
        fields = [
            PointField(name='x', offset=0, datatype=PointField.FLOAT32, count=1),
            PointField(name='y', offset=4, datatype=PointField.FLOAT32, count=1),
            PointField(name='z', offset=8, datatype=PointField.FLOAT32, count=1),
        ]
        
        cloud_data = []
        for point in points:
            cloud_data.append(struct.pack('fff', *point))
        
        msg = PointCloud2()
        msg.header = header
        msg.height = 1
        msg.width = len(points)
        msg.fields = fields
        msg.is_bigendian = False
        msg.point_step = 12
        msg.row_step = msg.point_step * len(points)
        msg.is_dense = True
        msg.data = b''.join(cloud_data)
        
        self.pointcloud_pub.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = TestDataPublisher()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
