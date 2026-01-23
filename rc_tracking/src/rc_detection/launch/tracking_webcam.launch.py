#!/usr/bin/env python3
"""
Launch file for tracking system with built-in webcam
Uses laptop's built-in camera for testing
"""

from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    # Declare arguments
    camera_device_arg = DeclareLaunchArgument(
        'camera_device',
        default_value='0',
        description='Camera device ID (0 for built-in webcam)'
    )

    camera_width_arg = DeclareLaunchArgument(
        'camera_width',
        default_value='640',
        description='Camera frame width'
    )

    camera_height_arg = DeclareLaunchArgument(
        'camera_height',
        default_value='480',
        description='Camera frame height'
    )

    camera_fps_arg = DeclareLaunchArgument(
        'camera_fps',
        default_value='30',
        description='Camera FPS'
    )

    model_path_arg = DeclareLaunchArgument(
        'model_path',
        default_value='yolo26n.pt',
        description='Path to YOLO model file'
    )

    target_class_arg = DeclareLaunchArgument(
        'target_class',
        default_value='person',
        description='Class name to track (e.g., person, car, bottle)'
    )

    confidence_threshold_arg = DeclareLaunchArgument(
        'confidence_threshold',
        default_value='0.5',
        description='YOLO confidence threshold'
    )

    show_preview_arg = DeclareLaunchArgument(
        'show_preview',
        default_value='true',
        description='Show detection visualization window'
    )

    # Webcam Publisher Node
    webcam_node = Node(
        package='rc_detection',
        executable='webcam_publisher',
        name='webcam_publisher',
        output='screen',
        parameters=[{
            'device_id': LaunchConfiguration('camera_device'),
            'width': LaunchConfiguration('camera_width'),
            'height': LaunchConfiguration('camera_height'),
            'fps': LaunchConfiguration('camera_fps'),
            'frame_id': 'camera_link',
        }]
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

    # Sensor Fusion Node (optional, comment out if not using LiDAR)
    # fusion_node = Node(
    #     package='rc_fusion',
    #     executable='sensor_fusion_node',
    #     name='sensor_fusion_node',
    #     output='screen',
    #     parameters=[{
    #         'lidar_topic': '/scan_points',
    #         'detection_topic': '/detections',
    #         'camera_info_topic': '/camera/camera_info',
    #         'target_track_id': -1,
    #         'image_width': LaunchConfiguration('camera_width'),
    #         'image_height': LaunchConfiguration('camera_height'),
    #         'control_kp': 0.01,
    #     }]
    # )

    return LaunchDescription([
        camera_device_arg,
        camera_width_arg,
        camera_height_arg,
        camera_fps_arg,
        model_path_arg,
        target_class_arg,
        confidence_threshold_arg,
        show_preview_arg,
        webcam_node,
        yolo_node,
        # fusion_node,  # Uncomment if using LiDAR
    ])
