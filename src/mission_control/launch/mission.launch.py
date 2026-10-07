"""Start mars_sim together with mission_control for one mission.

    ros2 launch mission_control mission.launch.py mission:=0
    ros2 launch mission_control mission.launch.py mission:=5 seed:=42   # same random world for everyone

Closing the simulator window ends the whole launch.
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction, Shutdown
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

from mission_control.missions import MISSIONS


def nodes_for_mission(context):
    number = int(LaunchConfiguration('mission').perform(context))
    mission = MISSIONS.get(number)
    sim_params = {'show_grid': LaunchConfiguration('show_grid')}
    if mission is not None:
        sim_params.update(mission.sim_params)
    return [
        Node(
            package='mars_sim',
            executable='mars_sim',
            name='mars_sim',
            output='screen',
            parameters=[sim_params],
            on_exit=Shutdown(),
        ),
        Node(
            package='mission_control',
            executable='mission_control',
            name='mission_control',
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
