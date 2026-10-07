# Cheat sheet

## Every new terminal

```bash
source /opt/ros/jazzy/setup.bash           # or your distro: humble, kilted, rolling ...
source ~/mars_rover/install/setup.bash
```

## Building

```bash
cd ~/mars_rover                                     # always at the workspace root
colcon build --symlink-install                      # every package
colcon build --symlink-install --packages-select my_rover   # just one
source install/setup.bash                           # after every build
```

After editing a `.py` file, just run it again. After editing `setup.py` or `package.xml`, or adding a launch file, build and source again.

## CLI commands

| I want to... | Command |
|---|---|
| list nodes | `ros2 node list` |
| see what a node sends/receives | `ros2 node info /mars_sim` |
| list topics | `ros2 topic list` (`-t` shows types) |
| eavesdrop on a topic | `ros2 topic echo /rover1/odom` (`--once` = one message) |
| type + who publishes/subscribes | `ros2 topic info -v /rover1/cmd_vel` |
| measure the rate | `ros2 topic hz /rover1/odom` |
| send a message | `ros2 topic pub --once /rover1/radio std_msgs/msg/String "{data: 'hi'}"` |
| keep sending | `ros2 topic pub --rate 1 ...` (stop with Ctrl+C) · `--rate 1 --times 5` = five messages |
| see a msg/srv/action definition | `ros2 interface show geometry_msgs/msg/Twist` |
| list services | `ros2 service list` (`-t` shows types) |
| a service's type | `ros2 service type /spawn_rover` |
| call a service | `ros2 service call /rover1/collect std_srvs/srv/Trigger` |
| parameters | `ros2 param list` · `ros2 param get <node> <name>` · `ros2 param set <node> <name> <value>` |
| actions | `ros2 action list` · `ros2 action info /rover1/drill` · `ros2 action send_goal --feedback <action> <type> "<yaml>"` |
| where is a frame | `ros2 run tf2_ros tf2_echo map rover1/left_gripper` |
| all frames as a PDF | `ros2 run tf2_tools view_frames` |
| run a program | `ros2 run <package> <executable>` |
| ... with namespace/parameters | `ros2 run <pkg> <exe> --ros-args -r __ns:=/rover2 -p max_speed:=1.0` |
| ... with a renamed topic | `ros2 run <pkg> <exe> --ros-args -r cmd_vel:=/rover1/cmd_vel` |
| launch | `ros2 launch <package> <file>.launch.py arg:=value` |
| see the whole system | `rqt_graph` |

Put the options of `ros2 topic pub` right after `pub`: `ros2 topic pub --once /rover1/cmd_vel ...`. An option between the type and the data gives `unrecognized arguments`.

## YAML in `ros2 topic pub` / `ros2 service call` / `ros2 action send_goal`

```bash
"{linear: {x: 1.0}, angular: {z: 0.5}}"                    # nest with {}, missing fields = 0
"{data: '100'}"                                            # digits-only text needs '...'
"{data: true}"                                             # booleans: true / false
"{name: [left_shoulder, left_elbow], position: [0.5, -1.0]}"   # lists use []
```

## Driving

Each `cmd_vel` command lasts 1 second, then the rover stops. Distance = speed × seconds of commands:

```bash
T="/rover1/cmd_vel geometry_msgs/msg/Twist"
ros2 topic pub --rate 1 --times 4 $T "{linear: {x: 1.0}}"     # 4 m forward (top speed 1.0 m/s)
ros2 topic pub --once $T "{angular: {z: 1.5708}}"             # turn left 90° (top 2.0 rad/s)
ros2 topic pub --rate 1 $T "{linear: {x: 1.0}, angular: {z: 0.5}}"   # circle, radius = 1.0 / 0.5 = 2 m
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

# yaw (heading) from the quaternion in nav_msgs/Odometry
q = msg.pose.pose.orientation
yaw = math.atan2(2.0 * (q.w * q.z + q.x * q.y), 1.0 - 2.0 * (q.y * q.y + q.z * q.z))
```

## Python node template

```python
import math

import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from std_srvs.srv import Trigger


class MyNode(Node):
    def __init__(self):
        super().__init__('my_node')
        # parameter
        self.declare_parameter('speed', 0.5)
        # publisher (relative name: lives under the node's namespace)
        self.publisher = self.create_publisher(Twist, 'cmd_vel', 10)
        # subscriber
        self.pose = None
        self.create_subscription(Odometry, 'odom', self.odom_callback, 10)
        # service client
        self.client = self.create_client(Trigger, 'collect')
        self.future = None
        # timer
        self.create_timer(0.05, self.loop)

    def odom_callback(self, msg: Odometry):
        self.pose = msg.pose.pose            # callback: just remember the data

    def loop(self):                          # timer: decide + command
        if self.pose is None:
            return
        cmd = Twist()
        cmd.linear.x = self.get_parameter('speed').value
        self.publisher.publish(cmd)
        if self.future is None or self.future.done():
            self.future = self.client.call_async(Trigger.Request())   # never wait for the answer in a callback!

        self.get_logger().info(f'x={self.pose.position.x:.2f}', throttle_duration_sec=1.0)


def main(args=None):
    rclpy.init(args=args)
    node = MyNode()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):   # Ctrl+C
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
```

Register it in `setup.py` and run it for a rover:

```python
entry_points={'console_scripts': ['my_node = my_rover.my_node:main']},
```

```bash
ros2 run my_rover my_node --ros-args -r __ns:=/rover1
```

## Launch file template

```python
# <pkg>/launch/my.launch.py  (+ add it to data_files in setup.py)
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        Node(package='my_rover', executable='my_node', namespace='rover1',
             parameters=[{'speed': 0.8}]),
        Node(package='my_rover', executable='my_node', namespace='rover2',
             parameters=[{'speed': 0.5}]),
        # renaming a topic: remappings=[('cmd_vel', '/rover1/cmd_vel')]
    ])
```

## tf2: a map point seen from another frame

```python
from geometry_msgs.msg import PointStamped
from tf2_ros import Buffer, TransformException, TransformListener
import tf2_geometry_msgs  # noqa: F401  (lets tf_buffer.transform() handle PointStamped)

# in __init__
self.tf_buffer = Buffer()
self.tf_listener = TransformListener(self.tf_buffer, self)

# later, in a timer
point = PointStamped()
point.header.frame_id = 'map'
point.point.x, point.point.y = x, y
try:
    p = self.tf_buffer.transform(point, 'rover1/left_shoulder').point   # p.x, p.y from the shoulder
except TransformException:
    return                                       # no transforms yet: try again next tick
```

Frames: `map` → `rover1/base_link` (x forward, y left) → `rover1/laser`, `rover1/drill`, `rover1/cache`,
`rover1/left_shoulder` → `rover1/left_upper_arm` → `rover1/left_forearm` → `rover1/left_gripper` (and the same for `right`).

## Action client (the drill)

```python
from rclpy.action import ActionClient
from action_msgs.msg import GoalStatus
from mars_interfaces.action import Drill

self.drill = ActionClient(self, Drill, '/rover1/drill')

def start(self):
    future = self.drill.send_goal_async(Drill.Goal(depth=0.3), feedback_callback=self.on_feedback)
    future.add_done_callback(self.on_accepted)

def on_accepted(self, future):
    self.goal_handle = future.result()            # .accepted tells you if the server took it
    self.goal_handle.get_result_async().add_done_callback(self.on_result)

def on_feedback(self, msg):
    if msg.feedback.temperature > 70.0:
        self.goal_handle.cancel_goal_async()      # stop before the bit breaks (80 °C)

def on_result(self, future):
    status = future.result().status               # GoalStatus.STATUS_SUCCEEDED / STATUS_CANCELED / STATUS_ABORTED
    self.get_logger().info(future.result().result.message)
```

## Arm kinematics (2-link planar arm)

```python
L1, L2 = 0.6, 0.5                                   # upper arm, forearm
SHOULDER = {'left': (0.4, 0.25), 'right': (0.4, -0.25)}   # in rover1/base_link (x forward, y left)

# forward kinematics, in the shoulder frame
elbow = (L1 * math.cos(q1), L1 * math.sin(q1))
tip = (elbow[0] + L2 * math.cos(q1 + q2), elbow[1] + L2 * math.sin(q1 + q2))

# inverse kinematics, (x, y) in the shoulder frame; None if out of reach
c2 = (x * x + y * y - L1 * L1 - L2 * L2) / (2 * L1 * L2)
q2 = math.acos(c2) * (-1 if side == 'left' else 1)     # only if -1 <= c2 <= 1; elbow bends outwards
q1 = math.atan2(y, x) - math.atan2(L2 * math.sin(q2), L1 + L2 * math.cos(q2))
```

## mars_sim interfaces

### World

| Name | Kind | Type |
|---|---|---|
| `/spawn_rover` | service | `mars_interfaces/srv/SpawnRover` |
| `/earth/uplink` | topic (out) | `std_msgs/msg/String`: messages from Earth (mission 1) |
| `/earth/downlink` | topic (out) | `std_msgs/msg/String`: every photo sent to Earth |
| `/lander/samples`, `/lander/meteorites` | topic (out) | `std_msgs/msg/Int32`: what the lander has received |
| `/mission/goals` | topic | `geometry_msgs/msg/PoseArray`: beacons/targets still to reach, next one first (z = drawing radius) |
| `/mission/items` | topic | `geometry_msgs/msg/PoseArray`: things the mission tells you about (drill sites, meteorites) |
| `/tf`, `/tf_static` | topic (out) | every frame, see above |
| `/mars/markers` | topic (out) | `visualization_msgs/msg/MarkerArray`: the world for RViz |
| `/judge/state` | topic (out) | the referee's view (hands off in missions) |

### Per rover (`/rover1/...`)

| Name | Kind | Type |
|---|---|---|
| `cmd_vel` | topic (in) | `geometry_msgs/msg/Twist`: stops by itself 1 s after the last command |
| `radio` | topic (in) | `std_msgs/msg/String`: speech bubble for 5 s |
| `odom` | topic (out) | `nav_msgs/msg/Odometry`: 50 times/s, frame `map` |
| `scan` | topic (out) | `sensor_msgs/msg/LaserScan`: 181 rays from −90° (right) to +90° (left), `inf` = nothing |
| `camera/detections` | topic (out) | `mars_interfaces/msg/DetectionArray`: kind, id, range, bearing (+ = left) |
| `battery` | topic (out) | `sensor_msgs/msg/BatteryState`: `percentage` 0-1 |
| `bumps`, `samples_onboard` | topic (out) | `std_msgs/msg/Int32` |
| `take_photo`, `collect`, `unload` | service | `std_srvs/srv/Trigger` |
| `teleport` | service | `mars_interfaces/srv/Teleport` (a simulator tool, not something real rovers can do) |
| `drill` | action | `mars_interfaces/action/Drill`: goal depth · feedback depth, temperature · result success, message |

### Arms (missions 9-12)

| Name | Kind | Type |
|---|---|---|
| `arm/joint_command` | topic (in) | `sensor_msgs/msg/JointState`: target angles by joint name |
| `joint_states` | topic (out) | `sensor_msgs/msg/JointState`: `left_shoulder`, `left_elbow`, `right_shoulder`, `right_elbow` |
| `left_gripper`, `right_gripper` | service | `std_srvs/srv/SetBool`: true = grab, false = release |
| `left_gripper/holding`, `right_gripper/holding` | topic (out) | `std_msgs/msg/String`: id of what it holds, `''` = nothing |

**Sizes:** map 20 × 20 m, (0, 0) bottom-left · lander (3, 3), radius 1.5 m · rover 0.8 × 0.6 m, top speed 1.0 m/s and 2.0 rad/s
· camera 6 m / 60° · laser 8 m / 180° · collect 1.0 m / ±30° · photo 3 m / ±30° · sand: 60 % speed
· arms: shoulders at (0.4, ±0.25), links 0.6 + 0.5 m, 2 rad/s · grab within 0.3 m (meteorite: its edge + 0.15 m, both grippers, at most 1.2 m apart)
· cache at (−0.15, 0), 6 places · drill: within 0.35 m of the rover's centre, 0.04 m/s, +15 °C/s, −10 °C/s when stopped, breaks above 80 °C, a core needs 0.3 m
