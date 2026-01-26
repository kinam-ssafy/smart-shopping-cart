#!/usr/bin/env python3
"""
Map Saver Launch File
생성된 맵을 저장합니다.
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess
from launch.substitutions import LaunchConfiguration
import os


def generate_launch_description():
    # Dynamic path resolution
    pkg_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    default_save_dir = os.path.join(pkg_path, 'maps')
    
    # Arguments
    map_name_arg = DeclareLaunchArgument(
        'map_name', default_value='map',
        description='Map file name (without extension)'
    )

    save_dir_arg = DeclareLaunchArgument(
        'save_dir', default_value=default_save_dir,
        description='Directory to save map'
    )

    # Map Saver CLI
    map_saver = ExecuteProcess(
        cmd=[
            'ros2', 'run', 'nav2_map_server', 'map_saver_cli',
            '-f', [LaunchConfiguration('save_dir'), '/', LaunchConfiguration('map_name')],
            '--ros-args', '-p', 'save_map_timeout:=5000'
        ],
        output='screen'
    )

    return LaunchDescription([
        map_name_arg,
        save_dir_arg,
        map_saver,
    ])
