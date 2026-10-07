from glob import glob

from setuptools import setup

package_name = 'mission_control'

setup(
    name=package_name,
    version='0.1.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', glob('launch/*.launch.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='kittinook',
    maintainer_email='kitti.thamrong@gmail.com',
    description='Missions, objectives and stars for Mars Rover Academy, a mission-based ROS 2 course.',
    license='Apache-2.0',
    entry_points={
        'console_scripts': [
            'mission_control = mission_control.mission_control:main',
            'progress = mission_control.progress:main',
        ],
    },
)
