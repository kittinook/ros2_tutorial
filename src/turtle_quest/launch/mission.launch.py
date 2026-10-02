"""Start turtlesim_plus together with quest_master for one mission.

    ros2 launch turtle_quest mission.launch.py mission:=0
    ros2 launch turtle_quest mission.launch.py mission:=5 seed:=42   # same random world for everyone

Missions that need arms (9 and up) start the simulator with arms:=true automatically.
Closing the simulator window ends the whole launch.
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction, Shutdown
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

from turtle_quest.missions import MISSIONS


def nodes_for_mission(context):
    number = int(LaunchConfiguration('mission').perform(context))
    mission = MISSIONS.get(number)
    arms = mission is not None and mission.arms
    return [
        Node(
            package='turtlesim_plus',
            executable='turtlesim_plus_node.py',
            name='turtlesim_plus',
            output='screen',
            parameters=[{'show_grid': LaunchConfiguration('show_grid'), 'arms': arms}],
            on_exit=Shutdown(),
        ),
        Node(
            package='turtle_quest',
            executable='quest_master',
            name='quest_master',
            output='screen',
            parameters=[{
                'mission': number,
                'seed': LaunchConfiguration('seed'),
            }],
        ),
    ]


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument('mission', default_value='0', description=f'mission number (0-{max(MISSIONS)})'),
        DeclareLaunchArgument('seed', default_value='-1',
                              description='random seed for the mission world (-1 = different every run)'),
        DeclareLaunchArgument('show_grid', default_value='true'),
        OpaqueFunction(function=nodes_for_mission),
    ])
