#!/usr/bin/env python3
"""
Full System Launch File
Webcam + YOLO + DeepSORT + YDLiDAR + Sensor Fusion
Complete object detection and distance measurement system
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, ExecuteProcess
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution, FindExecutable
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
import os


def generate_launch_description():
    # Get the source directory
    src_dir = os.path.join(os.path.expanduser('~'), 'rc_tracking', 'src', 'rc_detection', 'rc_detection')
    
    # Arguments
    camera_device_arg = DeclareLaunchArgument(
        'camera_device',
        default_value='0',
        description='Camera device ID (0 for /dev/video0)'
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

    model_path_arg = DeclareLaunchArgument(
        'model_path',
        default_value='yolo11n.pt',
        description='Path to YOLO model file'
    )

    target_class_arg = DeclareLaunchArgument(
        'target_class',
        default_value='person',
        description='Class name to track (person, car, bottle, etc.)'
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

    # 1. Webcam Publisher Node
    webcam_node = ExecuteProcess(
        cmd=['python3', os.path.join(src_dir, 'webcam_publisher.py'),
             '--ros-args',
             '-p', ['device_id:=', LaunchConfiguration('camera_device')],
             '-p', ['width:=', LaunchConfiguration('camera_width')],
             '-p', ['height:=', LaunchConfiguration('camera_height')],
             '-p', 'fps:=30',
             '-p', 'frame_id:=camera_link'],
        output='screen',
    )

    # 2. YOLO + DeepSORT Detection Node
    yolo_node = ExecuteProcess(
        cmd=['python3', os.path.join(src_dir, 'yolo_deepsort_node.py'),
             '--ros-args',
             '-p', ['model_path:=', LaunchConfiguration('model_path')],
             '-p', ['target_class:=', LaunchConfiguration('target_class')],
             '-p', ['confidence_threshold:=', LaunchConfiguration('confidence_threshold')],
             '-p', ['show_preview:=', LaunchConfiguration('show_preview')],
             '-p', 'image_topic:=/camera/image_raw'],
        output='screen',
    )

    # 3. YDLiDAR Driver Node
    ydlidar_node = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            PathJoinSubstitution([
                FindPackageShare('ydlidar_ros2_driver'),
                'launch',
                'ydlidar_launch.py'
            ])
        ])
    )

    # 4. Sensor Fusion Node (C++)
    fusion_node = Node(
        package='rc_fusion',
        executable='sensor_fusion_node',
        name='sensor_fusion_node',
        output='screen',
        parameters=[{
            'lidar_topic': '/scan',
            'detection_topic': '/detections',
            'camera_info_topic': '/camera/camera_info',
            'target_track_id': -1,  # -1 = track closest object
            'image_width': LaunchConfiguration('camera_width'),
            'image_height': LaunchConfiguration('camera_height'),
            'control_kp': 0.01,
        }]
    )

    return LaunchDescription([
        camera_device_arg,
        camera_width_arg,
        camera_height_arg,
        model_path_arg,
        target_class_arg,
        confidence_threshold_arg,
        show_preview_arg,
        webcam_node,
        yolo_node,
        ydlidar_node,
        fusion_node,
    ])
