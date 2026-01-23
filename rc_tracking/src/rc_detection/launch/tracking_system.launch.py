#!/usr/bin/env python3
"""
Launch file for RC car object tracking system
Starts camera, LiDAR, detection, and fusion nodes
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
    
    # YOLO Detection Node (Python)
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
        }],
        remappings=[
            ('/camera/image_raw', '/camera/image_raw'),
        ]
    )
    
    # Sensor Fusion Node (C++)
    fusion_node = Node(
        package='rc_fusion',
        executable='sensor_fusion_node',
        name='sensor_fusion_node',
        output='screen',
        parameters=[{
            'lidar_topic': '/scan_points',
            'detection_topic': '/detections',
            'camera_info_topic': '/camera/camera_info',
            'target_track_id': -1,  # -1 = track closest object
            'image_width': 640,
            'image_height': 480,
            'control_kp': 0.01,
        }]
    )
    
    # Optional: Camera driver node (uncomment and configure for your camera)
    # camera_node = Node(
    #     package='v4l2_camera',
    #     executable='v4l2_camera_node',
    #     name='camera',
    #     parameters=[{
    #         'video_device': '/dev/video0',
    #         'image_size': [640, 480],
    #         'camera_frame_id': 'camera_link',
    #     }]
    # )
    
    # Optional: LiDAR driver node (example for RPLidar)
    # lidar_node = Node(
    #     package='rplidar_ros',
    #     executable='rplidar_composition',
    #     name='rplidar',
    #     parameters=[{
    #         'serial_port': '/dev/ttyUSB0',
    #         'serial_baudrate': 115200,
    #         'frame_id': 'laser_frame',
    #         'angle_compensate': True,
    #     }]
    # )
    
    return LaunchDescription([
        model_path_arg,
        target_class_arg,
        confidence_threshold_arg,
        show_preview_arg,
        yolo_node,
        fusion_node,
        # camera_node,  # Uncomment if using
        # lidar_node,   # Uncomment if using
    ])
