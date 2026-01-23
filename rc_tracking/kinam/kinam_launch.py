#!/usr/bin/env python3
"""
Kinam ROS2 Launch File
비전 노드 + 제어 노드를 함께 실행
"""

from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        # 비전 노드 (YOLO + DeepSORT + 락온)
        Node(
            package='rc_detection',
            executable='kinam_vision',
            name='kinam_vision',
            output='screen',
            emulate_tty=True,
        ),

        # 제어 노드 (LiDAR + 모터 제어)
        Node(
            package='rc_detection',
            executable='kinam_control',
            name='kinam_control',
            output='screen',
            emulate_tty=True,
        )
    ])
