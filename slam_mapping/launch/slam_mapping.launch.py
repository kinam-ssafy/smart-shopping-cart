#!/usr/bin/env python3
"""
SLAM Mapping Launch File
YDLidar + Cartographer SLAM + RViz 시각화
타임스탬프 동기화 수정 버전
"""

from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
import os


def generate_launch_description():
    # Dynamic path resolution - get package path from this file's location
    pkg_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_dir = os.path.join(pkg_path, 'config')
    rviz_config = os.path.join(pkg_path, 'rviz', 'slam.rviz')

    # Arguments
    port_arg = DeclareLaunchArgument(
        'port', default_value='/dev/ttyUSB0',
        description='YDLidar serial port'
    )

    # YDLidar Node (TF도 직접 퍼블리시)
    ydlidar_node = Node(
        package='rccar_nodes',
        executable='ydlidar_node',
        name='ydlidar_node',
        parameters=[{
            'port': LaunchConfiguration('port'),
            'baudrate': 128000,
            'frame_id': 'laser',
            'range_min': 0.12,
            'range_max': 10.0,
            'frequency': 6.0,
        }],
        output='screen'
    )

    # Cartographer Node
    cartographer_node = Node(
        package='cartographer_ros',
        executable='cartographer_node',
        name='cartographer_node',
        arguments=[
            '-configuration_directory', config_dir,
            '-configuration_basename', 'ydlidar_2d.lua'
        ],
        remappings=[
            ('scan', '/scan'),
        ],
        output='screen'
    )

    # Cartographer Occupancy Grid Node
    occupancy_grid_node = Node(
        package='cartographer_ros',
        executable='cartographer_occupancy_grid_node',
        name='occupancy_grid_node',
        parameters=[{
            'resolution': 0.05,
            'publish_period_sec': 1.0,
        }],
        output='screen'
    )

    # RViz
    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        arguments=['-d', rviz_config],
        output='screen'
    )

    return LaunchDescription([
        port_arg,
        ydlidar_node,
        cartographer_node,
        occupancy_grid_node,
        rviz_node,
    ])
