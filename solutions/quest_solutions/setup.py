from glob import glob

from setuptools import setup

package_name = 'quest_solutions'

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
    description='Reference solutions for the Turtle Quest coding missions (4-8, 10-12)',
    license='GPL-3.0-only',
    entry_points={
        'console_scripts': [
            'square = quest_solutions.square:main',
            'go_to_goal = quest_solutions.go_to_goal:main',
            'pizza_hunter = quest_solutions.pizza_hunter:main',
            'team_hunter = quest_solutions.team_hunter:main',
            'delivery = quest_solutions.delivery:main',
            'arm_reach = quest_solutions.arm_reach:main',
            'pick_place = quest_solutions.pick_place:main',
            'crate_mover = quest_solutions.crate_mover:main',
        ],
    },
)
