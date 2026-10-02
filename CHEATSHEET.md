# Cheat sheet

## Every new terminal

```bash
source /opt/ros/humble/setup.bash
source ~/turtle_quest/install/setup.bash
```

## Building

```bash
cd ~/turtle_quest                                   # always at the workspace root
colcon build --symlink-install                      # every package
colcon build --symlink-install --packages-select my_turtle   # just one
source install/setup.bash                           # after every build
```

After editing a `.py` file, just run it again. After editing `setup.py` or `package.xml`, or adding a launch file, build and source again.

## CLI commands

| I want to... | Command |
|---|---|
| list nodes | `ros2 node list` |
| see what a node sends/receives | `ros2 node info /turtlesim_plus` |
| list topics | `ros2 topic list` (`-t` shows types) |
| eavesdrop on a topic | `ros2 topic echo /turtle1/pose` (`--once` = one message) |
| type + who publishes/subscribes | `ros2 topic info -v /turtle1/cmd_vel` |
| measure the rate | `ros2 topic hz /turtle1/pose` |
| send a message | `ros2 topic pub --once /turtle1/say std_msgs/msg/String "{data: 'hi'}"` |
| keep sending | `ros2 topic pub --rate 1 ...` (stop with Ctrl+C) |
| see a msg/srv/action definition | `ros2 interface show geometry_msgs/msg/Twist` |
| list services | `ros2 service list` (`-t` shows types) |
| a service's type | `ros2 service type /spawn_turtle` |
| call a service | `ros2 service call /turtle1/eat std_srvs/srv/Empty` |
| parameters | `ros2 param list` · `ros2 param get <node> <name>` · `ros2 param set <node> <name> <value>` |
| actions | `ros2 action list` · `ros2 action send_goal <action> <type> "<yaml>"` |
| run a program | `ros2 run <package> <executable>` |
| ... with namespace/parameters | `ros2 run <pkg> <exe> --ros-args -r __ns:=/turtle2 -p max_speed:=2.0` |
| launch | `ros2 launch <package> <file>.launch.py arg:=value` |
| see the whole system | `rqt_graph` |

## YAML in `ros2 topic pub` / `ros2 service call`

```bash
"{linear: {x: 1.0}, angular: {z: 0.5}}"                    # nest with {}, missing fields = 0
"{data: '100'}"                                            # digits-only text needs '...'
"{r: 255, g: 0, b: 0, width: 3, 'off': 0}"                 # off/on/yes/no are YAML keywords: quote them
"{name: [left_shoulder, left_elbow], position: [0.5, -1.0]}"   # lists use []
```

## Angles (radians)

| 30° | 45° | 60° | 90° | 180° | 360° |
|---|---|---|---|---|---|
| 0.5236 | 0.7854 | 1.0472 | 1.5708 | 3.1416 | 6.2832 |

```python
import math
math.radians(90)                                # degrees -> radians
math.atan2(dy, dx)                              # direction of the vector (dx, dy)
math.atan2(math.sin(a), math.cos(a))            # wrap an angle into -pi..pi
math.hypot(dx, dy)                              # distance
```

## Python node template

```python
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from std_srvs.srv import Empty
from turtlesim.msg import Pose


class MyNode(Node):
    def __init__(self):
        super().__init__('my_node')
        # parameter
        self.declare_parameter('speed', 1.0)
        # publisher
        self.publisher = self.create_publisher(Twist, 'cmd_vel', 10)
        # subscriber
        self.pose = None
        self.create_subscription(Pose, 'pose', self.pose_callback, 10)
        # service client
        self.client = self.create_client(Empty, 'eat')
        self.future = None
        # timer
        self.create_timer(0.05, self.loop)

    def pose_callback(self, msg: Pose):
        self.pose = msg                  # callback: just remember the data

    def loop(self):                      # timer: decide + command
        if self.pose is None:
            return
        cmd = Twist()
        cmd.linear.x = self.get_parameter('speed').value
        self.publisher.publish(cmd)
        if self.future is None or self.future.done():
            self.future = self.client.call_async(Empty.Request())   # never wait for the answer in a callback!

        self.get_logger().info(f'x={self.pose.x:.2f}', throttle_duration_sec=1.0)


def main():
    rclpy.init()
    node = MyNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
```

Register it in `setup.py`:

```python
entry_points={'console_scripts': ['my_node = my_turtle.my_node:main']},
```

## Launch file template

```python
# <pkg>/launch/my.launch.py  (+ add it to data_files in setup.py)
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        Node(package='my_turtle', executable='my_node', namespace='turtle1',
             parameters=[{'speed': 2.0}], remappings=[('pose', '/turtle2/pose')]),
    ])
```

## Arm kinematics (2-link planar arm)

```python
L1, L2 = 0.8, 0.7                            # upper arm, forearm
SHOULDER_Y = {'left': 0.3, 'right': -0.3}    # in the turtle frame (x forward, y left)

# world -> turtle frame
dx, dy = x - pose.x, y - pose.y
x_t, y_t = math.cos(pose.theta) * dx + math.sin(pose.theta) * dy, -math.sin(pose.theta) * dx + math.cos(pose.theta) * dy

# forward kinematics (turtle frame)
elbow = (0 + L1 * math.cos(q1), SHOULDER_Y[side] + L1 * math.sin(q1))
tip = (elbow[0] + L2 * math.cos(q1 + q2), elbow[1] + L2 * math.sin(q1 + q2))

# inverse kinematics (turtle frame); None if out of reach
dx, dy = x_t, y_t - SHOULDER_Y[side]
c2 = (dx * dx + dy * dy - L1 * L1 - L2 * L2) / (2 * L1 * L2)
q2 = math.acos(c2) * (-1 if side == 'left' else 1)        # only if -1 <= c2 <= 1
q1 = math.atan2(dy, dx) - math.atan2(L2 * math.sin(q2), L1 + L2 * math.cos(q2))
```

## turtlesim_plus interfaces

### World

| Name | Kind | Type |
|---|---|---|
| `/spawn_turtle` | service | `turtlesim/srv/Spawn` |
| `/remove_turtle` | service | `turtlesim/srv/Kill` |
| `/spawn_pizza`, `/spawn_parcel`, `/spawn_crate` | service | `turtlesim_plus_interfaces/srv/GivePosition` |
| `/clear` (erase lines), `/clear_objects` (remove pizzas/parcels/crates) | service | `std_srvs/srv/Empty` |
| `/hud` | topic (in) | `std_msgs/msg/String`: text in the side panel |
| `/mission/goals` | topic (in) | `geometry_msgs/msg/PoseArray`: flags to draw (z = radius) |
| `/judge/objects` | topic (out) | `turtlesim_plus_interfaces/msg/WorldObjectArray`: the referee's view (hands off in missions) |

### Per turtle (`/turtle1/...`)

| Name | Kind | Type |
|---|---|---|
| `cmd_vel` | topic (in) | `geometry_msgs/msg/Twist`: stops by itself 1 s after the last command |
| `say` | topic (in) | `std_msgs/msg/String`: speech bubble for 5 s |
| `pose` | topic (out) | `turtlesim/msg/Pose`: 100 times/s |
| `scan` | topic (out) | `turtlesim_plus_interfaces/msg/ScannerDataArray`: empty = nothing in sight |
| `pizza_count`, `parcel_count` | topic (out) | `std_msgs/msg/Int64` |
| `carrying_parcel` | topic (out) | `std_msgs/msg/Bool` |
| `eat`, `pickup`, `dropoff`, `stop` | service | `std_srvs/srv/Empty` |
| `set_pen` | service | `turtlesim/srv/SetPen` |
| `teleport_absolute`, `teleport_relative` | service | `turtlesim/srv/TeleportAbsolute`, `TeleportRelative` |
| `detect_pizza` | action | `turtlesim_plus_interfaces/action/GetData` |

### Arms (only with `arms:=true`; missions 9-12 do it for you)

| Name | Kind | Type |
|---|---|---|
| `joint_command` | topic (in) | `sensor_msgs/msg/JointState`: target angles by joint name |
| `joint_states` | topic (out) | `sensor_msgs/msg/JointState`: `left_shoulder`, `left_elbow`, `right_shoulder`, `right_elbow` |
| `left_arm/tip`, `right_arm/tip` | topic (out) | `geometry_msgs/msg/Point`: gripper position, world frame |
| `left_gripper`, `right_gripper` | service | `std_srvs/srv/SetBool`: true = grab, false = release |
| `left_gripper/holding`, `right_gripper/holding` | topic (out) | `std_msgs/msg/String`: `''`, `Pizza`, `Parcel` or `Crate` |

**Sizes:** world 10.88 × 10.88 m · turtle starts at (5.44, 5.44) · scanner 4 m / 60° · eat & pickup 2 m / 60° · DROP-OFF (9.38, 9.38) radius 1.2 m
· arms: shoulders ±0.3 m, links 0.8 + 0.7 m, shoulder ±π, elbow ±2.7 rad, 2 rad/s · grab within 0.4 m (crate: 0.65 m from its centre)
