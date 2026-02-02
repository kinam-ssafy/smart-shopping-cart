from setuptools import setup
import os
from glob import glob

package_name = 'slam_mapping2'

setup(
    name=package_name,
    version='1.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.py')),
        (os.path.join('share', package_name, 'config'), glob('config/*.lua')),
        (os.path.join('share', package_name, 'config'), glob('config/*.yaml')),
        (os.path.join('share', package_name, 'rviz'), glob('rviz/*.rviz')),
        (os.path.join('share', package_name, 'urdf'), glob('urdf/*.urdf')),
        # maps/ 디렉토리는 런타임에 생성되므로 패키지에 포함하지 않음
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='user',
    maintainer_email='user@example.com',
    description='YDLidar Cartographer SLAM with RViz Visualization',
    license='MIT',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'ydlidar_node = slam_mapping2.ydlidar_node:main',
            'odom_publisher = slam_mapping2.odom_publisher:main',
            'tf_to_web = slam_mapping2.tf_to_web:main',
            'goal_bridge = slam_mapping2.goal_bridge:main',
            'cmd_vel_bridge = slam_mapping2.cmd_vel_bridge:main',
        ],
    },
)
