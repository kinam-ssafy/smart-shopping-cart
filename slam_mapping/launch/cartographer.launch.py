#!/usr/bin/env python3
"""
Cartographer SLAM Launch File
"""
import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    # Launch arguments
    use_sim_time = LaunchConfiguration('use_sim_time')
    configuration_directory = LaunchConfiguration('configuration_directory')
    configuration_basename = LaunchConfiguration('configuration_basename')

    return LaunchDescription([
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='false',
            description='Use simulation time'),

        DeclareLaunchArgument(
            'configuration_directory',
            description='Full path to config directory'),

        DeclareLaunchArgument(
            'configuration_basename',
            default_value='ydlidar_2d.lua',
            description='Cartographer configuration file'),

        Node(
            package='cartographer_ros',
            executable='cartographer_node',
            name='cartographer_node',
            output='screen',
            parameters=[{'use_sim_time': use_sim_time}],
            arguments=[
                '-configuration_directory', configuration_directory,
                '-configuration_basename', configuration_basename
            ],
            remappings=[
                ('scan', 'scan'),
                ('imu', 'imu'),
            ]
        ),

        Node(
            package='cartographer_ros',
            executable='cartographer_occupancy_grid_node',
            name='cartographer_occupancy_grid_node',
            output='screen',
            parameters=[
                {'use_sim_time': use_sim_time},
                {'resolution': 0.05}
            ],
            arguments=['-resolution', '0.05']
        ),
    ])
