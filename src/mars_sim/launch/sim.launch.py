"""Just the simulator, without a mission: rover1 on the lander, an empty map.

    ros2 launch mars_sim sim.launch.py
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, Shutdown
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument('show_grid', default_value='true'),
        Node(
            package='mars_sim',
            executable='mars_sim',
            name='mars_sim',
            output='screen',
            parameters=[{'show_grid': LaunchConfiguration('show_grid')}],
            on_exit=Shutdown(),
        ),
    ])
