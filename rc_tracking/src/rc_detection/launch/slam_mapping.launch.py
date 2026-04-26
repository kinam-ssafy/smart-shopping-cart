#!/usr/bin/env python3
"""
SLAM Mapping Launch File for YDLIDAR X4-PRO
Creates 2D map using slam_toolbox
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
import os


def generate_launch_description():
    # Arguments
    use_sim_time_arg = DeclareLaunchArgument(
        'use_sim_time',
        default_value='false',
        description='Use simulation time'
    )

    serial_port_arg = DeclareLaunchArgument(
        'serial_port',
        default_value='/dev/ydlidar',
        description='YDLiDAR serial port'
    )

    slam_params_arg = DeclareLaunchArgument(
        'slam_params_file',
        default_value='',
        description='Path to slam_toolbox params file (optional)'
    )

    # YDLiDAR Node
    ydlidar_node = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            PathJoinSubstitution([
                FindPackageShare('ydlidar_ros2_driver'),
                'launch',
                'ydlidar_launch.py'
            ])
        ])
    )

    # SLAM Toolbox (Online Async)
    slam_toolbox_node = Node(
        package='slam_toolbox',
        executable='async_slam_toolbox_node',
        name='slam_toolbox',
        output='screen',
        parameters=[
            {
                'use_sim_time': LaunchConfiguration('use_sim_time'),

                # SLAM Configuration
                'slam_mode': 'mapping',
                'map_update_interval': 1.0,

                # Solver parameters
                'solver_plugin': 'solver_plugins::CeresSolver',
                'ceres_linear_solver': 'SPARSE_NORMAL_CHOLESKY',
                'ceres_preconditioner': 'SCHUR_JACOBI',
                'ceres_trust_strategy': 'LEVENBERG_MARQUARDT',
                'ceres_dogleg_type': 'TRADITIONAL_DOGLEG',
                'ceres_loss_function': 'None',

                # Scan matching
                'use_scan_matching': True,
                'use_scan_barycenter': True,
                'minimum_travel_distance': 0.2,
                'minimum_travel_heading': 0.2,
                'scan_buffer_size': 10,
                'scan_buffer_maximum_scan_distance': 10.0,
                'link_match_minimum_response_fine': 0.1,
                'link_scan_maximum_distance': 1.5,
                'loop_search_maximum_distance': 3.0,
                'do_loop_closing': True,
                'loop_match_minimum_chain_size': 10,
                'loop_match_maximum_variance_coarse': 3.0,
                'loop_match_minimum_response_coarse': 0.35,
                'loop_match_minimum_response_fine': 0.45,

                # Correlation parameters
                'correlation_search_space_dimension': 0.5,
                'correlation_search_space_resolution': 0.01,
                'correlation_search_space_smear_deviation': 0.1,

                # Loop closure parameters
                'loop_search_space_dimension': 8.0,
                'loop_search_space_resolution': 0.05,
                'loop_search_space_smear_deviation': 0.03,

                # Scan matcher
                'distance_variance_penalty': 0.5,
                'angle_variance_penalty': 1.0,
                'fine_search_angle_offset': 0.00349,
                'coarse_search_angle_offset': 0.349,
                'coarse_angle_resolution': 0.0349,
                'minimum_angle_penalty': 0.9,
                'minimum_distance_penalty': 0.5,
                'use_response_expansion': True,

                # Map parameters
                'resolution': 0.05,  # 5cm per pixel
                'max_laser_range': 10.0,
                'minimum_time_interval': 0.5,
                'transform_publish_period': 0.02,
                'map_file_name': '/tmp/slam_map',
                'map_start_pose': [0.0, 0.0, 0.0],
                'map_start_at_dock': True,

                # TF parameters
                'odom_frame': 'odom',
                'map_frame': 'map',
                'base_frame': 'base_link',
                'scan_topic': '/scan',
                'mode': 'mapping',

                # Performance
                'throttle_scans': 1,
                'transform_timeout': 0.2,
                'tf_buffer_duration': 30.0,
                'stack_size_to_use': 40000000,
                'enable_interactive_mode': True,
            }
        ],
        remappings=[
            ('/scan', '/scan'),
        ]
    )

    # Static transform: map -> odom (초기에는 동일)
    # SLAM이 시작되면 slam_toolbox가 map->odom을 발행합니다
    map_to_odom_tf = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='map_to_odom_broadcaster',
        arguments=['0', '0', '0', '0', '0', '0', 'map', 'odom'],
        # SLAM 시작 후 자동으로 오버라이드됨
    )

    # Static transform: odom -> base_link (로봇이 움직이지 않으면 고정)
    # 실제 로봇에서는 odometry 노드가 이를 발행해야 합니다
    odom_to_base_tf = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='odom_to_base_broadcaster',
        arguments=['0', '0', '0', '0', '0', '0', 'odom', 'base_link'],
    )

    # RViz for visualization (optional)
    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='screen',
        arguments=['-d', PathJoinSubstitution([
            FindPackageShare('rc_detection'),
            'config',
            'slam_config.rviz'
        ])],
        condition=lambda context: False  # 기본적으로 비활성화, 필요시 True로 변경
    )

    return LaunchDescription([
        use_sim_time_arg,
        serial_port_arg,
        slam_params_arg,
        ydlidar_node,
        slam_toolbox_node,
        # map_to_odom_tf,  # slam_toolbox가 발행하므로 주석 처리
        odom_to_base_tf,
        # rviz_node,  # 필요시 활성화
    ])
