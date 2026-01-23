from setuptools import find_packages
from setuptools import setup

setup(
    name='rc_detection',
    version='0.0.1',
    packages=find_packages(
        include=('rc_detection', 'rc_detection.*')),
)
