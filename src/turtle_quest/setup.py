from glob import glob

from setuptools import setup

package_name = 'turtle_quest'

setup(
    name=package_name,
    version='1.0.0',
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
    description='Mission-based ROS 2 beginner course on top of turtlesim_plus',
    license='GPL-3.0-only',
    entry_points={
        'console_scripts': [
            'quest_master = turtle_quest.quest_master:main',
            'progress = turtle_quest.progress:main',
        ],
    },
)
