#!/usr/bin/env python3
"""
Nav2 Navigation Launch File
Nav2 스택과 goal_bridge를 함께 실행하는 런치 파일

사용법:
    ros2 launch slam_mapping2 nav2_navigation.launch.py map:=s4_map
"""

import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, GroupAction
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node, SetParameter
from launch_ros.substitutions import FindPackageShare
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    # 패키지 경로
    pkg_share = get_package_share_directory('slam_mapping2')
    nav2_bringup_dir = get_package_share_directory('nav2_bringup')

    # Launch arguments
    map_arg = DeclareLaunchArgument(
        'map',
        default_value='s4_map',
        description='Map name (without extension)'
    )

    use_sim_time_arg = DeclareLaunchArgument(
        'use_sim_time',
        default_value='false',
        description='Use simulation time'
    )

    simulation_arg = DeclareLaunchArgument(
        'simulation',
        default_value='true',
        description='Run cmd_vel_bridge in simulation mode'
    )

    autostart_arg = DeclareLaunchArgument(
        'autostart',
        default_value='true',
        description='Automatically start Nav2 lifecycle nodes'
    )

    # 설정 파일 경로
    nav2_params_file = os.path.join(pkg_share, 'config', 'nav2_params.yaml')

    # 맵 파일 경로 (slam_mapping 패키지 내 maps 디렉토리)
    # 실제 경로는 스크립트에서 설정
    maps_dir = os.path.join(os.path.dirname(pkg_share), 'slam_mapping', 'maps')
    if not os.path.exists(maps_dir):
        # fallback: 상위 디렉토리에서 찾기
        maps_dir = os.path.join(os.path.dirname(os.path.dirname(pkg_share)), 'slam_mapping', 'maps')

    # Map Server
    map_server_node = Node(
        package='nav2_map_server',
        executable='map_server',
        name='map_server',
        output='screen',
        parameters=[{
            'use_sim_time': LaunchConfiguration('use_sim_time'),
            'yaml_filename': PathJoinSubstitution([
                maps_dir,
                [LaunchConfiguration('map'), '.yaml']
            ])
        }],
        remappings=[('/map', '/map')]
    )

    # Controller Server
    controller_server_node = Node(
        package='nav2_controller',
        executable='controller_server',
        name='controller_server',
        output='screen',
        parameters=[nav2_params_file, {'use_sim_time': LaunchConfiguration('use_sim_time')}],
        remappings=[
            ('/cmd_vel', '/cmd_vel'),
            ('/odom', '/odom')
        ]
    )

    # Planner Server
    planner_server_node = Node(
        package='nav2_planner',
        executable='planner_server',
        name='planner_server',
        output='screen',
        parameters=[nav2_params_file, {'use_sim_time': LaunchConfiguration('use_sim_time')}]
    )

    # Behavior Server
    behavior_server_node = Node(
        package='nav2_behaviors',
        executable='behavior_server',
        name='behavior_server',
        output='screen',
        parameters=[nav2_params_file, {'use_sim_time': LaunchConfiguration('use_sim_time')}]
    )

    # BT Navigator
    bt_navigator_node = Node(
        package='nav2_bt_navigator',
        executable='bt_navigator',
        name='bt_navigator',
        output='screen',
        parameters=[nav2_params_file, {'use_sim_time': LaunchConfiguration('use_sim_time')}]
    )

    # Velocity Smoother
    velocity_smoother_node = Node(
        package='nav2_velocity_smoother',
        executable='velocity_smoother',
        name='velocity_smoother',
        output='screen',
        parameters=[nav2_params_file, {'use_sim_time': LaunchConfiguration('use_sim_time')}],
        remappings=[
            ('/cmd_vel', '/cmd_vel_nav'),
            ('/cmd_vel_smoothed', '/cmd_vel')
        ]
    )

    # Lifecycle Manager
    lifecycle_manager_node = Node(
        package='nav2_lifecycle_manager',
        executable='lifecycle_manager',
        name='lifecycle_manager_navigation',
        output='screen',
        parameters=[{
            'use_sim_time': LaunchConfiguration('use_sim_time'),
            'autostart': LaunchConfiguration('autostart'),
            'node_names': [
                'map_server',
                'controller_server',
                'planner_server',
                'behavior_server',
                'bt_navigator',
                'velocity_smoother'
            ]
        }]
    )

    # Goal Bridge (웹 API <-> Nav2 브릿지)
    goal_bridge_node = Node(
        package='slam_mapping2',
        executable='goal_bridge',
        name='goal_bridge',
        output='screen',
        parameters=[{
            'bridge_port': 8851,
            'web_server_url': 'http://localhost:8850',
            'feedback_rate': 5.0
        }]
    )

    # Cmd Vel Bridge (모터 드라이버 또는 시뮬레이션)
    cmd_vel_bridge_node = Node(
        package='slam_mapping2',
        executable='cmd_vel_bridge',
        name='cmd_vel_bridge',
        output='screen',
        parameters=[{
            'simulation': LaunchConfiguration('simulation'),
            'publish_odom': True,
            'publish_tf': False,  # Cartographer가 TF 관리
            'max_linear_vel': 0.22,
            'max_angular_vel': 1.0
        }]
    )

    return LaunchDescription([
        # Arguments
        map_arg,
        use_sim_time_arg,
        simulation_arg,
        autostart_arg,

        # Nav2 Nodes
        map_server_node,
        controller_server_node,
        planner_server_node,
        behavior_server_node,
        bt_navigator_node,
        velocity_smoother_node,
        lifecycle_manager_node,

        # Custom Nodes
        goal_bridge_node,
        cmd_vel_bridge_node,
    ])
