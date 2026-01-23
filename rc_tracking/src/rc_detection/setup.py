from setuptools import setup
import os
from glob import glob

package_name = 'rc_detection'

setup(
    name=package_name,
    version='0.0.1',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
        (os.path.join('share', package_name, 'config'), glob('config/*.yaml')),
        (os.path.join('share', package_name, 'config'), glob('config/*.rviz')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='your_name',
    maintainer_email='your_email@example.com',
    description='YOLO + DeepSORT detection for RC car',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'yolo_deepsort_node = rc_detection.yolo_deepsort_node:main',
            'test_data_publisher = rc_detection.test_data_publisher:main',
            'webcam_publisher = rc_detection.webcam_publisher:main',
            'map_saver = rc_detection.map_saver:main',
            'distance_test_node = rc_detection.distance_test_node:main',
            'distance_lidar_node = rc_detection.distance_lidar_node:main',
        ],
    },
)
