#!/usr/bin/env python3
"""
Launch file for RC car with YDLiDAR X4-Pro
Includes YDLiDAR driver, camera, detection, and fusion nodes
"""

from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    # Declare arguments
    model_path_arg = DeclareLaunchArgument(
        'model_path',
        default_value='yolov11n.pt',
        description='Path to YOLO model file'
    )
    
    target_class_arg = DeclareLaunchArgument(
        'target_class',
        default_value='person',
        description='Class name to track'
    )
    
    confidence_threshold_arg = DeclareLaunchArgument(
        'confidence_threshold',
        default_value='0.5',
        description='YOLO confidence threshold'
    )
    
    show_preview_arg = DeclareLaunchArgument(
        'show_preview',
        default_value='true',
        description='Show detection visualization'
    )
    
    serial_port_arg = DeclareLaunchArgument(
        'serial_port',
        default_value='/dev/ydlidar',
        description='YDLiDAR serial port (default: /dev/ydlidar, or /dev/ttyUSB0)'
    )
    
    # YDLiDAR X4-Pro Driver Node
    ydlidar_node = Node(
        package='ydlidar_ros2_driver',
        executable='ydlidar_ros2_driver_node',
        name='ydlidar_node',
        output='screen',
        parameters=[{
            'port': LaunchConfiguration('serial_port'),
            'frame_id': 'laser_frame',
            'ignore_array': '',
            'baudrate': 128000,
            'lidar_type': 1,  # TYPE_TRIANGLE
            'device_type': 0,  # YDLIDAR_TYPE_SERIAL
            'sample_rate': 5,
            'abnormal_check_count': 4,
            'fixed_resolution': True,
            'reversion': True,
            'inverted': True,
            'auto_reconnect': True,
            'isSingleChannel': False,
            'intensity': False,
            'support_motor_dtr': False,
            'angle_max': 180.0,
            'angle_min': -180.0,
            'range_max': 10.0,
            'range_min': 0.12,
            'frequency': 8.0,
            'invalid_range_is_inf': False,
        }],
        remappings=[
            ('/scan', '/scan'),
        ]
    )
    
    # YOLO Detection Node
    yolo_node = Node(
        package='rc_detection',
        executable='yolo_deepsort_node',
        name='yolo_deepsort_node',
        output='screen',
        parameters=[{
            'model_path': LaunchConfiguration('model_path'),
            'target_class': LaunchConfiguration('target_class'),
            'confidence_threshold': LaunchConfiguration('confidence_threshold'),
            'show_preview': LaunchConfiguration('show_preview'),
            'image_topic': '/camera/image_raw',
        }]
    )
    
    # Sensor Fusion Node (YDLiDAR optimized)
    fusion_node = Node(
        package='rc_fusion',
        executable='sensor_fusion_ydlidar_node',
        name='sensor_fusion_ydlidar_node',
        output='screen',
        parameters=[{
            'lidar_topic': '/scan',
            'detection_topic': '/detections',
            'camera_info_topic': '/camera/camera_info',
            'target_track_id': -1,
            'image_width': 640,
            'image_height': 480,
            'control_kp': 0.01,
            'lidar_height': 0.15,  # Adjust based on your mounting
            'min_range': 0.12,
            'max_range': 10.0,
        }]
    )
    
    # Optional: Camera driver (uncomment and configure)
    # For USB cameras:
    # camera_node = Node(
    #     package='v4l2_camera',
    #     executable='v4l2_camera_node',
    #     name='camera',
    #     parameters=[{
    #         'video_device': '/dev/video0',
    #         'image_size': [640, 480],
    #         'camera_frame_id': 'camera_link',
    #         'camera_info_url': 'file:///path/to/camera_calibration.yaml',
    #     }]
    # )
    
    # For Raspberry Pi Camera:
    # camera_node = Node(
    #     package='camera_ros',
    #     executable='camera_node',
    #     name='camera',
    #     parameters=[{
    #         'camera_info_url': 'file:///path/to/camera_calibration.yaml',
    #     }]
    # )
    
    # Static transform between camera and LiDAR
    # Adjust these values based on your actual mounting
    static_tf_node = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='camera_to_laser_tf',
        arguments=[
            '0.05', '0.0', '0.0',  # x, y, z (LiDAR 5cm behind camera)
            '0', '0', '0', '1',     # qx, qy, qz, qw (no rotation)
            'camera_link',
            'laser_frame'
        ]
    )
    
    return LaunchDescription([
        model_path_arg,
        target_class_arg,
        confidence_threshold_arg,
        show_preview_arg,
        serial_port_arg,
        ydlidar_node,
        yolo_node,
        fusion_node,
        static_tf_node,
        # camera_node,  # Uncomment when configured
    ])
