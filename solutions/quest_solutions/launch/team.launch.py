"""Mission 7: run team_hunter twice, in two namespaces with different parameters

    ros2 launch quest_solutions team.launch.py
"""
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        Node(
            package='quest_solutions',
            executable='team_hunter',
            name='pizza_hunter',
            namespace='turtle1',  # -> /turtle1/pizza_hunter, using /turtle1/scan, /turtle1/cmd_vel, ...
            parameters=[{'max_speed': 3.0, 'patrol_start': 0}],
        ),
        Node(
            package='quest_solutions',
            executable='team_hunter',
            name='pizza_hunter',
            namespace='turtle2',
            parameters=[{'max_speed': 3.0, 'patrol_start': 2}],
        ),
    ])
