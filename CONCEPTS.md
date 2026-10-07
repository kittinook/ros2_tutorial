# ROS 2, part by part

This page lists the parts ROS 2 is made of, shows which mission teaches each one, and then explains every part with an example.
Use the table to see where a topic comes up, the checklist to see what you can already do, and the sections as a reference when you get stuck.

The last group, "Not covered yet", lists the parts of ROS 2 this course doesn't teach. Each one still gets a short explanation and a tested example, so you know what to learn next and where it connects to what you've done.

[ARCHITECTURE.md](ARCHITECTURE.md) is the companion page: it is about how these parts fit together into a system. This page is about the parts themselves.

## Coverage map

● taught in this mission · ○ used again or mentioned · ◇ not in the course, but a good next step after this mission

| Part | [0](missions/00-landing.md) | [1](missions/01-telemetry.md) | [2](missions/02-manual-drive.md) | [3](missions/03-mission-control.md) | [4](missions/04-survey-square.md) | [5](missions/05-waypoints.md) | [6](missions/06-sample-hunter.md) | [7](missions/07-rover-fleet.md) | [8](missions/08-boss-power-crisis.md) | [9](missions/09-arm-check.md) | [10](missions/10-frames.md) | [11](missions/11-drill-and-stow.md) | [12](missions/12-boss-meteorite-recovery.md) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **The ROS graph** | | | | | | | | | | | | | |
| [1. Nodes](#1-nodes) | ○ | ● | | | ● | ○ | ○ | ○ | ○ | | ○ | ○ | ○ |
| [2. Topics and messages](#2-topics-and-messages) | ○ | ● | ● | | ● | ● | ○ | ○ | ○ | ● | ○ | ○ | ○ |
| [3. Services](#3-services) | | | | ● | | | ● | | ○ | ● | | ○ | ○ |
| [4. Actions](#4-actions) | | | | | | | | | | | | ● | |
| [5. Parameters](#5-parameters) | ○ | | | ○ | | | | ● | | | | | |
| [6. Interfaces](#6-interfaces) | | ● | ○ | ● | | | ○ | | | ○ | | ○ | |
| [7. Names, namespaces and remapping](#7-names-namespaces-and-remapping) | ● | | | ○ | | | | ● | | | | | |
| **Building and running** | | | | | | | | | | | | | |
| [8. Workspaces, colcon and source](#8-workspaces-colcon-and-source) | ● | | | | ○ | ○ | | ○ | | | | | |
| [9. Packages](#9-packages) | | | | | ● | ○ | | ○ | | | ○ | ○ | ○ |
| [10. ros2 run and its arguments](#10-ros2-run-and-its-arguments) | ● | | | | ○ | | | ● | | | | | |
| [11. Launch files](#11-launch-files) | ○ | | | | | | | ● | | | | | |
| **Writing nodes in Python** | | | | | | | | | | | | | |
| [12. Publishers and timers](#12-publishers-and-timers) | | | | | ● | ○ | ○ | | ○ | | ○ | ○ | ○ |
| [13. Subscribers and callbacks](#13-subscribers-and-callbacks) | | | | | | ● | ○ | | ○ | | ○ | ○ | ○ |
| [14. Service clients and futures](#14-service-clients-and-futures) | | | | | | | ● | | ○ | | | ○ | ○ |
| [15. Action clients](#15-action-clients) | | | | | | | | | | | | ● | |
| [16. The executor](#16-the-executor) | | | | | ○ | ○ | ● | | | | | ○ | |
| [17. Parameters in code](#17-parameters-in-code) | | | | | | | | ● | | | | | |
| [18. Logging and time](#18-logging-and-time) | | | | | ○ | ● | ○ | | ○ | | ○ | ○ | ○ |
| **Tools** | | | | | | | | | | | | | |
| [19. The ros2 command line](#19-the-ros2-command-line) | ○ | ● | ● | ● | | | ○ | ● | | ● | | ● | |
| [20. rqt](#20-rqt) | | ○ | | | | ○ | | | ○ | | | | |
| [21. RViz](#21-rviz) | | | | | | | | | | ○ | ○ | | |
| **Under the hood** | | | | | | | | | | | | | |
| [22. DDS, discovery and domains](#22-dds-discovery-and-domains) | | | | | | | | | | | | | |
| [23. Quality of service](#23-quality-of-service) | | | | | ○ | | | | | | | | |
| **Messages** | | | | | | | | | | | | | |
| [24. Standard message packages](#24-standard-message-packages) | | ● | ● | ● | | ● | ● | | ● | ● | | | |
| [25. Quaternions and orientation](#25-quaternions-and-orientation) | | | | | | ● | ○ | ○ | ○ | | ○ | ○ | ○ |
| **Robotics on top of ROS** | | | | | | | | | | | | | |
| [26. Control loops](#26-control-loops) | | | | | ● | ● | ○ | | ○ | | | ○ | ○ |
| [27. State machines](#27-state-machines) | | | | | | | | | ● | | | ● | ○ |
| [28. Frames and tf2](#28-frames-and-tf2) | | | | | | | ○ | | | ● | ● | ○ | ○ |
| [29. Kinematics](#29-kinematics) | | | | | | | | | | ● | ● | ○ | ○ |
| [30. Many robots, one codebase](#30-many-robots-one-codebase) | | | | ○ | | | | ● | | | | | |
| [31. Mobile manipulation](#31-mobile-manipulation) | | | | | | | | | | | | ○ | ● |
| **Not covered yet** | | | | | | | | | | | | | |
| [32. Your own interfaces](#32-your-own-interfaces) | | | | | | | ◇ | | | | | ◇ | |
| [33. Service servers](#33-service-servers) | | | | | | | | | ◇ | | | | |
| [34. Action servers](#34-action-servers) | | | | | | | | | | | | ◇ | ◇ |
| [35. Broadcasting frames with tf2](#35-broadcasting-frames-with-tf2) | | | | | | | | | | | ◇ | | |
| [36. Recording with ros2 bag](#36-recording-with-ros2-bag) | | | | | | ◇ | | | | | | | |
| [37. Multi-threaded executors and callback groups](#37-multi-threaded-executors-and-callback-groups) | | | | | | | ◇ | | | | | | |
| [38. Testing](#38-testing) | | | | | | | | | | | ◇ | | |
| [39. C++ with rclcpp](#39-c-with-rclcpp) | | | | | ◇ | | | | | | | | |
| [40. Robot description: URDF and robot_state_publisher](#40-robot-description-urdf-and-robot_state_publisher) | | | | | | | | | | ◇ | | | |
| [41. Simulators and simulated time](#41-simulators-and-simulated-time) | | | | | | | | | | | | | ◇ |
| [42. Lifecycle nodes and composition](#42-lifecycle-nodes-and-composition) | | | | | | | | | | | | | ◇ |
| [43. ros2_control, Nav2 and MoveIt 2](#43-ros2_control-nav2-and-moveit-2) | | | | | | | | | ◇ | ◇ | | | ◇ |

DDS and discovery (part 22) don't belong to any one mission; they're explained in [ARCHITECTURE.md](ARCHITECTURE.md#under-the-hood-how-messages-actually-travel) and the classroom setup in [TEACHER.md](TEACHER.md).

## Self-check

Tick these off as you go. If you can't do one, the linked section explains it.

**After Part 1 (missions 0 to 8)**
- [ ] I can build a workspace and explain why every new terminal needs `source` ([8](#8-workspaces-colcon-and-source))
- [ ] I can run teleop and remap its `cmd_vel` to `/rover1/cmd_vel` ([7](#7-names-namespaces-and-remapping), [10](#10-ros2-run-and-its-arguments))
- [ ] I can list the nodes and topics of a running system and see who publishes what ([1](#1-nodes), [19](#19-the-ros2-command-line))
- [ ] I can find a topic's message type and its fields, and publish one from the terminal ([2](#2-topics-and-messages), [6](#6-interfaces))
- [ ] I can measure how often a topic is published ([19](#19-the-ros2-command-line))
- [ ] I can call a service from the terminal and read its `success` and `message` ([3](#3-services))
- [ ] I can say when to use a topic, a service, an action or a parameter ([ARCHITECTURE.md](ARCHITECTURE.md#which-one-do-i-need))
- [ ] I can create a Python package and register a node in `setup.py` ([9](#9-packages))
- [ ] I can write a node with a publisher and a timer ([12](#12-publishers-and-timers))
- [ ] I can write a subscriber whose callback only stores the data ([13](#13-subscribers-and-callbacks))
- [ ] I can turn the quaternion in `nav_msgs/Odometry` into a yaw ([25](#25-quaternions-and-orientation))
- [ ] I can tell which direction each ray of a `LaserScan` points in ([24](#24-standard-message-packages))
- [ ] I can call a service from code without blocking the executor ([14](#14-service-clients-and-futures), [16](#16-the-executor))
- [ ] I can run the same node for two rovers in two namespaces ([7](#7-names-namespaces-and-remapping))
- [ ] I can declare a parameter, set it at start-up and change it while the node runs ([5](#5-parameters), [17](#17-parameters-in-code))
- [ ] I can write a launch file that starts several nodes ([11](#11-launch-files))
- [ ] I can explain why sand ruins an open-loop plan, and write a P controller that doesn't care ([26](#26-control-loops))
- [ ] I can design a behaviour as states and transitions, like "go home and charge before the battery runs out" ([27](#27-state-machines))

**After Part 2 (missions 9 to 12)**
- [ ] I can command joints with `sensor_msgs/JointState` and read their state back ([24](#24-standard-message-packages))
- [ ] I can find out where a gripper is with `tf2_echo` ([28](#28-frames-and-tf2))
- [ ] I can let tf2 convert a point from the `map` frame into a shoulder frame in my own node ([28](#28-frames-and-tf2))
- [ ] I can compute forward and inverse kinematics of a 2-link arm ([29](#29-kinematics))
- [ ] I can send an action goal, follow its feedback, cancel it and read the result, from the terminal and from code ([4](#4-actions), [15](#15-action-clients))
- [ ] I can move a state machine forward on events (action finished, service answered, arm arrived) instead of guessed delays ([27](#27-state-machines))
- [ ] I can reuse my own Python module in several nodes ([9](#9-packages))

**Next steps**
- [ ] I've written my own message or action type ([32](#32-your-own-interfaces))
- [ ] I've written a service server and an action server ([33](#33-service-servers), [34](#34-action-servers))
- [ ] I've broadcast a frame with tf2 and looked it up ([35](#35-broadcasting-frames-with-tf2))
- [ ] I've recorded and replayed a run with `ros2 bag` ([36](#36-recording-with-ros2-bag))
- [ ] I've written a test for my own code ([38](#38-testing))
- [ ] I've written one node in C++ ([39](#39-c-with-rclcpp))
- [ ] I've described part of the rover in URDF ([40](#40-robot-description-urdf-and-robot_state_publisher))

---

## The ROS graph

### 1. Nodes

A node is one running program with one job. A robot is many nodes working together: one reads the laser, one plans, one drives the motors. Nodes don't call each other's functions. They only talk through topics, services, actions and parameters, which is why you can swap one out without touching the others.

Every Python node follows the same lifecycle: start ROS, create the node, spin (wait for events and run callbacks) until `Ctrl+C`, then shut down.

```python
def main():
    rclpy.init()           # 1. start ROS 2
    node = Square()        # 2. create the node
    try:
        rclpy.spin(node)   # 3. run callbacks until Ctrl+C
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()  # 4. shut down
```

To see the nodes of a running system:

```bash
ros2 node list
ros2 node info /mars_sim     # everything it publishes, subscribes to and serves
```

In the course: `mars_sim`, `mission_control` and `teleop_twist_keyboard` are nodes from mission 0. You inspect them in mission 1 and write your first one in mission 4.

### 2. Topics and messages

A topic is a named channel that carries a stream of messages of one type. Publishers send, subscribers receive, and neither side knows about the other. Any number of each can share a topic. Topics are for data that keeps flowing: positions, sensor readings, velocity commands.

```bash
ros2 topic echo --once /rover1/odom           # read one message
ros2 topic hz /rover1/odom                    # how often it's published (about 50 times a second)
ros2 topic pub --rate 1 --times 4 /rover1/cmd_vel geometry_msgs/msg/Twist "{linear: {x: 1.0}}"   # 4 m forward
```

Several publishers on one topic all get through, and the subscriber can't tell them apart. That's why the rover obeys teleop and your node at the same time, and why mission_control looks at the publisher's node name instead of the messages to catch teleop.

In the course: missions 1 and 2 from the terminal, mission 4 (publishing from code), mission 5 (subscribing), mission 9 (arm topics).

### 3. Services

A service is a request with exactly one response. The client asks, the server answers, and the exchange is over. Use one for short jobs where you want to know the outcome: spawn a rover, take a photo, collect a sample, close a gripper.

```bash
ros2 service type /spawn_rover              # mars_interfaces/srv/SpawnRover
ros2 service call /spawn_rover mars_interfaces/srv/SpawnRover "{name: scout, x: 5.0, y: 3.0, yaw: 0.0}"
ros2 service call /rover1/take_photo std_srvs/srv/Trigger
```

```text
response:
mars_interfaces.srv.SpawnRover_Response(name='scout')

response:
std_srvs.srv.Trigger_Response(success=False, message='No landmark in the picture. Get within 3 m and point the camera at it (less than 30 deg off).')
```

A service can answer with useful data (the name the rover actually got), with a yes or no and a reason (`std_srvs/srv/Trigger`, which most rover services use), or with nothing at all (`/rover1/teleport`, which just means "done"). Read the `message`: it usually tells you what to fix.

In the course: mission 3 from the terminal, mission 6 from code (`collect`), mission 8 (`unload`), and missions 9, 11 and 12 for the grippers.

### 4. Actions

An action is for a job that takes a while. The client sends a goal, the server accepts it, sends feedback while it works, and finally sends a result. The client can cancel at any time. Under the hood an action is three services and two topics.

The rover's drill is an action. Park on a drill site, then:

```bash
ros2 action list -t
ros2 action send_goal --feedback /rover1/drill mars_interfaces/action/Drill "{depth: 0.3}"
```

```text
Feedback:
    depth: 0.128
temperature: 68.0
^C
Canceling goal...
Goal canceled.
Result:
    success: false
message: Stopped at 0.14 m.
Goal finished with status: CANCELED
```

`Ctrl+C` on `send_goal` cancels the goal. That's the point of an action: the feedback tells you the bit is getting hot (it breaks above 80 °C), and cancel lets you stop in time. A goal can end three ways: succeeded, canceled, or aborted (the server gave up, for example because the rover wasn't parked on a site).

Real robots use actions for anything long: Nav2's `navigate_to_pose` (drive somewhere, feedback is the distance left) and MoveIt's `move_action` (move an arm along a planned path).

In the course: mission 11, from the terminal and then from code (section [15](#15-action-clients)). Section [34](#34-action-servers) shows how to write the server side.

### 5. Parameters

Parameters are named settings that live inside a node: speeds, gains, sensor ranges. Each has a type (bool, int, double, string or arrays of those). They can be set at start-up and changed while the node runs.

```bash
ros2 param list /rover2/sample_hunter
ros2 param get /rover2/sample_hunter max_speed
ros2 param set /rover2/sample_hunter max_speed 0.6
ros2 param dump /rover2/sample_hunter          # all of them, as YAML
```

`ros2 param dump` prints a file you can load back at start-up:

```yaml
/rover2/sample_hunter:
  ros__parameters:
    max_speed: 0.6
    patrol_start: 3
```

```bash
ros2 run my_rover sample_hunter --ros-args -r __ns:=/rover2 --params-file fleet.yaml
```

Every change is announced on the `/parameter_events` topic, which is how mission_control notices it in mission 7. The simulator has parameters too (`ros2 param list /mars_sim`): `mission.launch.py` sets `arms`, `battery_start` and `battery_drain` for each mission.

In the course: mission 7. The parameter services (`/mars_sim/describe_parameters` and friends) first show up in `ros2 service list` in mission 3.

### 6. Interfaces

"Interface" is the umbrella word for message types (`.msg`), service types (`.srv`) and action types (`.action`). They are the contract between nodes: two nodes only connect if they use the same type on the same name.

```bash
ros2 interface show mars_interfaces/srv/SpawnRover
```

```text
# Put a new rover into the world. An empty or taken name gets a free one.
string name
float64 x
float64 y
float64 yaw
---
string name        # the name the new rover actually got
```

In a service the `---` separates request from response. An action has two separators: goal, result, feedback (`ros2 interface show mars_interfaces/action/Drill`). Messages can contain other messages: `DetectionArray` is a header plus a list of `Detection`, and `Twist` is two `Vector3`.

The full name has three parts: package, kind, type (`mars_interfaces/msg/DetectionArray`). In Python it becomes `from mars_interfaces.msg import DetectionArray`.

In the course: missions 1 and 3 introduce `ros2 interface show`; mission 6 uses a message from the course's own interface package, `mars_interfaces`; mission 11 its action.

### 7. Names, namespaces and remapping

Every topic, service and node has a name. How a name in your code becomes the final name depends on how you write it:

| In the code | Node in namespace `/rover2` gets |
|---|---|
| `'/rover1/scan'` (absolute) | `/rover1/scan`, always |
| `'scan'` (relative) | `/rover2/scan` |
| `'~/status'` (private) | `/rover2/sample_hunter/status` |

Write relative names and the same code serves any rover; choose the namespace when you start the node:

```bash
ros2 run my_rover sample_hunter --ros-args -r __ns:=/rover2
```

You can also rename a single name without touching the code. That's remapping, and you used it in mission 0: `teleop_twist_keyboard` publishes on `cmd_vel`, which nobody listens to, so you point it at the rover:

```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -r cmd_vel:=/rover1/cmd_vel
```

This is how ROS tools written by other people plug into your robot: they use generic names, and you remap them.

In the course: mission 0 (remapping teleop), mission 3 (spawning `scout` creates a whole set of names under `/scout`), and mission 7 (using namespaces on purpose).

## Building and running

### 8. Workspaces, colcon and source

A workspace is a folder with your packages in `src/`. `colcon build` builds all of them into `build/` and `install/`; `source install/setup.bash` tells the current terminal where the results are.

```bash
cd ~/mars_rover
colcon build --symlink-install --packages-select my_rover
source install/setup.bash
```

Two habits save hours. Always build from the workspace root, never from inside `src/`. And `source` in every new terminal: "Package not found" is nearly always a terminal that wasn't sourced.

With `--symlink-install`, Python files in `install/` point back to `src/`, so editing a `.py` file needs no rebuild. Changing `setup.py`, `package.xml` or adding a launch file does.

In the course: mission 0, and again whenever you add a program (missions 4, 5, 7).

### 9. Packages

A package is the unit ROS builds, installs and shares. A Python package looks like this:

```text
src/my_rover/
├── my_rover/            your Python modules
├── package.xml          name, version, dependencies
├── setup.py             which programs `ros2 run` can start
├── setup.cfg
├── resource/
└── test/
```

`package.xml` lists what the package needs (`rclpy`, `geometry_msgs`, `nav_msgs`, ...). `setup.py` maps program names to functions and lists extra files to install:

```python
entry_points={'console_scripts': ['square = my_rover.square:main']},
```

Because all your nodes live in one Python package, they can import from each other. A module doesn't have to be a node: keep mission 10's inverse kinematics in a plain `arm_kinematics.py`, and missions 11 and 12 reuse it with `from my_rover.arm_kinematics import inverse_kinematics`.

C++ packages and interface packages use `ament_cmake` and a `CMakeLists.txt` instead (sections [32](#32-your-own-interfaces) and [39](#39-c-with-rclcpp)).

In the course: mission 4 creates the package, mission 7 installs a launch folder through `data_files`, missions 10 to 12 share a module.

### 10. ros2 run and its arguments

`ros2 run <package> <program>` starts one program. Everything after `--ros-args` configures the node without changing its code:

```bash
ros2 run my_rover sample_hunter --ros-args -r __ns:=/rover2 -r __node:=hunter2 -p max_speed:=0.6 --log-level debug
```

| Argument | Effect |
|---|---|
| `-r __ns:=/rover2` | put the node in a namespace |
| `-r __node:=hunter2` | rename the node |
| `-r cmd_vel:=/rover1/cmd_vel` | remap one topic or service name |
| `-p max_speed:=0.6` | set a parameter |
| `--params-file fleet.yaml` | set parameters from a file |
| `--log-level debug` | show debug messages |

In the course: mission 0 runs teleop with a remap, mission 4 runs your own node, mission 7 adds `-r __ns` and `-p`.

### 11. Launch files

A launch file starts a whole set of nodes with their namespaces, parameters and remappings in one command. In ROS 2 it is a Python file:

```python
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        Node(package='my_rover', executable='sample_hunter', namespace='rover1',
             parameters=[{'patrol_start': 0}]),
        Node(package='my_rover', executable='sample_hunter', namespace='rover2',
             parameters=[{'patrol_start': 3}]),
        # renaming a topic: remappings=[('cmd_vel', '/rover1/cmd_vel')]
    ])
```

Launch files can take arguments (`mission:=7`) and include other launch files (`IncludeLaunchDescription`). The `mission.launch.py` you've used since mission 0 takes arguments and uses the mission number to choose the simulator's parameters, for example `arms: true` from mission 9 on.

In the course: you use one from mission 0 and write one in mission 7.

## Writing nodes in Python

### 12. Publishers and timers

A publisher sends messages on a topic. A timer calls a function at a fixed rate. Together they are the simplest useful node:

```python
self.publisher = self.create_publisher(Twist, '/rover1/cmd_vel', 10)
self.timer = self.create_timer(0.1, self.timer_callback)

def timer_callback(self):
    msg = Twist()
    msg.linear.x = 1.0
    msg.angular.z = 0.5
    self.publisher.publish(msg)
```

The `10` is the queue depth (section [23](#23-quality-of-service)). Robots usually send commands at a steady rate even when nothing changes. The rover stops one second after the last `cmd_vel`, so a crashed controller can't leave it driving forever. Real robots have the same watchdog.

In the course: mission 4, then in every coding mission.

### 13. Subscribers and callbacks

A subscriber calls your function every time a message arrives:

```python
self.create_subscription(Odometry, '/rover1/odom', self.odom_callback, 10)

def odom_callback(self, msg: Odometry):
    self.pose = msg.pose.pose   # just remember it
```

Keep callbacks short. The pattern used throughout the course is that subscriber callbacks only store the latest data, and one timer makes all the decisions with whatever is newest. That keeps the logic in one place and keeps the node responsive ([ARCHITECTURE.md, pattern 2](ARCHITECTURE.md#pattern-2-inside-a-node-callbacks-remember-and-a-timer-decides)).

In the course: mission 5, then every coding mission after it.

### 14. Service clients and futures

A client sends a request and gets a future back immediately. The future becomes `done()` when the response arrives:

```python
self.collect_client = self.create_client(Trigger, '/rover1/collect')

def collect(self):
    if self.collect_future is None or self.collect_future.done():   # one request at a time
        self.collect_future = self.collect_client.call_async(Trigger.Request())
```

On a later tick you check `future.done()` and read `future.result()`. In mission 11, `future.result().success` of the gripper service decides whether the state machine stows the core or tries again.

Never block waiting for the answer inside a callback (section [16](#16-the-executor)).

In the course: mission 6, then missions 8, 11 and 12.

### 15. Action clients

An action client sends a goal and gets three kinds of callbacks: goal accepted or rejected, feedback, and the result. Each step hands the next step to a callback, so nothing waits:

```python
from action_msgs.msg import GoalStatus
from rclpy.action import ActionClient
from mars_interfaces.action import Drill

# in __init__
self.drill = ActionClient(self, Drill, '/rover1/drill')

def start(self):
    future = self.drill.send_goal_async(Drill.Goal(depth=0.3), feedback_callback=self.on_feedback)
    future.add_done_callback(self.on_accepted)

def on_accepted(self, future):
    self.goal_handle = future.result()
    if not self.goal_handle.accepted:
        return                                    # rejected: try again later
    self.goal_handle.get_result_async().add_done_callback(self.on_result)

def on_feedback(self, msg):
    if msg.feedback.temperature > 70.0:
        self.goal_handle.cancel_goal_async()      # stop before the bit breaks

def on_result(self, future):
    answer = future.result()                      # .status and .result
    if answer.status == GoalStatus.STATUS_SUCCEEDED:
        self.state = 'reach'
    elif answer.status == GoalStatus.STATUS_CANCELED:
        self.state = 'cool'
    self.get_logger().info(answer.result.message)
```

The status tells you how the goal ended (`STATUS_SUCCEEDED`, `STATUS_CANCELED`, `STATUS_ABORTED`), and the result carries the server's answer. A cancelled goal still sends a result, so `on_result` is the one place where you learn the goal is over.

In the course: mission 11.

### 16. The executor

`rclpy.spin(node)` runs an executor: a loop that waits for something to happen (a message, a timer tick, a service response) and runs the matching callback. The default executor runs one callback at a time.

That has one big consequence. If a callback waits (with `time.sleep`, a `while` loop, or a blocking service call), nothing else runs meanwhile. No messages arrive, no timers fire, and the service response you're waiting for can't be delivered either, so the node deadlocks. Hence the rules from the missions: no `sleep` in callbacks, use timers instead of loops, use `call_async` instead of waiting, and use done-callbacks for actions.

In the course: mission 4 (why a timer and not `while True`), mission 5 (what `sleep` in a callback does), mission 6 (the deadlock), mission 11 (action callbacks). Section [37](#37-multi-threaded-executors-and-callback-groups) shows how to run callbacks in parallel when you really need to.

### 17. Parameters in code

Declare a parameter with a default, then read it:

```python
self.declare_parameter('max_speed', 0.8)
...
speed = self.get_parameter('max_speed').value
```

Read it where you use it if it should respond to `ros2 param set` while the node runs; read it once in `__init__` if it only matters at start-up. A parameter you didn't declare can't be set from outside (the node rejects it).

In the course: mission 7.

### 18. Logging and time

Use the node's logger instead of `print`. Messages get a level, a timestamp and the node name, and can be throttled:

```python
self.get_logger().info(f'x={x:.2f} yaw={yaw:.2f}', throttle_duration_sec=1.0)
self.get_logger().warning('target out of reach')
```

Levels are debug, info, warning, error and fatal. `--ros-args --log-level debug` shows debug messages.

For time, use the node's clock rather than Python's `time`, because a simulator can supply its own clock (section [41](#41-simulators-and-simulated-time)):

```python
now = self.get_clock().now().nanoseconds / 1e9   # seconds
```

In the course: mission 5 introduces logging; mission 4 times its plan with the clock, and mission 11 times the drill's cool-down.

## Tools

### 19. The ros2 command line

The `ros2` command can inspect and poke every part of a running system. The ones you'll use most:

| Need | Command |
|---|---|
| what's running | `ros2 node list`, `ros2 node info <node>` |
| topics | `ros2 topic list -t`, `echo`, `info -v`, `hz`, `pub` |
| services | `ros2 service list -t`, `type`, `call` |
| actions | `ros2 action list -t`, `info`, `send_goal --feedback` |
| parameters | `ros2 param list`, `get`, `set`, `dump` |
| types | `ros2 interface show <type>` |
| frames | `ros2 run tf2_ros tf2_echo <from> <to>`, `ros2 run tf2_tools view_frames` |
| packages | `ros2 pkg create`, `ros2 pkg list`, `ros2 pkg executables <pkg>` |
| health check | `ros2 doctor` |

Commands like `ros2 topic pub` and `ros2 topic echo` run as short-lived nodes of their own (named `_ros2cli_...`), which is how mission_control can spot them.

In the course: missions 1, 2, 3 and 9 are entirely command line; mission 7 adds `ros2 param` and mission 11 `ros2 action`. [CHEATSHEET.md](CHEATSHEET.md) has the full list.

### 20. rqt

rqt is a set of small GUI tools. Two are worth knowing early:

```bash
ros2 run rqt_graph rqt_graph                                          # the live node graph
ros2 run rqt_plot rqt_plot /rover1/odom/pose/pose/position/x /rover1/odom/pose/pose/position/y
```

`rqt_graph` is the fastest way to answer "is my node connected to what I think it is?". `rqt_plot` makes controller tuning visible: you can see the overshoot when `K_ANGULAR` is too high, or watch `/rover1/battery/percentage` drop during mission 8.

In the course: extras in missions 1, 5 and 8.

### 21. RViz

RViz is the standard 3-D viewer of ROS. It doesn't simulate anything; it draws what is on the ROS graph. Start it with `rviz2` (it comes with the desktop install), set the Fixed Frame to `map`, and add displays:

| Display | Topic | Shows |
|---|---|---|
| TF | `/tf` | every frame of the rover, arms included |
| MarkerArray | `/mars/markers` | the rocks, samples, lander and meteorites |
| LaserScan | `/rover1/scan` | the laser rays |
| Odometry | `/rover1/odom` | where the rover has been |

If RViz and the simulator window agree, your frames are right. RViz is also where you'd check a URDF (section [40](#40-robot-description-urdf-and-robot_state_publisher)).

In the course: optional in missions 9 and 10, to see the frames that `tf2_echo` prints.

## Under the hood

### 22. DDS, discovery and domains

ROS 2 has no central server. Each node finds the others on its own (discovery) and they exchange messages directly through a middleware called DDS. Two practical consequences:

- Nodes on different computers talk the same way as nodes on one computer, as long as they're on the same network.
- Everyone on the network with the same `ROS_DOMAIN_ID` sees each other. In a classroom, give each person their own number, or keep ROS on each machine with `ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST` (Humble: `ROS_LOCALHOST_ONLY=1`).

```bash
export ROS_DOMAIN_ID=17       # put it in ~/.bashrc
```

See [ARCHITECTURE.md](ARCHITECTURE.md#under-the-hood-how-messages-actually-travel) for the layer diagram and [TEACHER.md](TEACHER.md) for classroom setup.

### 23. Quality of service

Every publisher and subscriber has QoS settings: how many messages to keep, and whether delivery must be reliable. The `10` you've passed everywhere means "keep the last 10 messages", with reliable delivery.

Sensors often use "best effort" instead: if a reading is lost, the next one will be along in a moment, and resending an old one would only add delay. ROS has a ready-made profile for that:

```python
from rclpy.qos import qos_profile_sensor_data

self.create_subscription(LaserScan, '/rover1/scan', self.scan_callback, qos_profile_sensor_data)
```

Publisher and subscriber must be compatible. A best-effort subscriber can read from a reliable publisher, but not the other way round: a reliable subscriber gets nothing from a best-effort publisher, silently. mars_sim publishes everything reliable, so both work here. Many real LiDAR and camera drivers publish best effort. `ros2 topic info -v` shows each side's settings when messages mysteriously don't arrive.

In the course: only the `10`. This is a common source of "my node receives nothing" once you work with real sensors.

## Messages

### 24. Standard message packages

Before inventing a message type, check whether a standard one fits. Other tools (RViz, plotters, recorders, other people's nodes) understand the standard ones. mars_sim uses them wherever it can:

| Package | Types used in the course | For |
|---|---|---|
| `std_msgs` | `String`, `Int32` | the radio, messages from Earth, counters |
| `std_srvs` | `Trigger`, `SetBool` (also `Empty`) | photo, collect, unload; the grippers |
| `geometry_msgs` | `Twist`, `PoseArray`, `PointStamped` | velocity commands, beacons, points for tf2 |
| `nav_msgs` | `Odometry` | where the rover is and how fast it moves |
| `sensor_msgs` | `LaserScan`, `BatteryState`, `JointState` (also `Image`, `Imu`, `NavSatFix`) | sensors and joints |
| `tf2_msgs`, `visualization_msgs` | `TFMessage`, `MarkerArray` | `/tf`, and the world for RViz |
| `mars_interfaces` | `DetectionArray`, `SpawnRover`, `Teleport`, `Drill` | the course's own, where no standard type fits |

A few fields trip people up:

- `Odometry`: the pose is in `msg.pose.pose` (position, plus orientation as a quaternion, section [25](#25-quaternions-and-orientation)) and the speed in `msg.twist.twist`. It is the pose of `rover1/base_link` (`child_frame_id`) in the `map` frame (`header.frame_id`).
- `LaserScan`: `ranges[i]` is the distance along the ray at angle `angle_min + i * angle_increment`, in the laser's frame. The rover's 181 rays go from −90° (right) to +90° (left), one degree apart, so `ranges[90]` points straight ahead. `inf` means the ray hit nothing within 8 m.
- `BatteryState`: `percentage` goes from 0 to 1, not 0 to 100.
- `JointState`: parallel lists, `name[i]` goes with `position[i]`. As a command you can send just the joints you want to move.

`sensor_msgs/JointState` is a good example of a standard paying off. It's the same message real arms publish, and `robot_state_publisher` and RViz read it directly (section [40](#40-robot-description-urdf-and-robot_state_publisher)). Mission 9 uses it in both directions, as a command and as the state.

In the course: `std_msgs` in mission 1, `geometry_msgs` in mission 2, `std_srvs` in mission 3, `Odometry` in mission 5, `LaserScan` in mission 6, `BatteryState` in mission 8, `JointState` and `SetBool` in mission 9.

### 25. Quaternions and orientation

ROS stores every orientation as a quaternion `(x, y, z, w)`, not as an angle. Quaternions work in 3-D without the special cases that roll, pitch and yaw have, which is why tf2 and every standard message use them.

The rover only turns about the vertical axis, so its quaternion is simple: for a heading `yaw`, `z = sin(yaw / 2)` and `w = cos(yaw / 2)`, and `x = y = 0`. Facing north (`yaw = 1.5708`) is `(0, 0, 0.707, 0.707)`. To get the yaw back:

```python
q = msg.pose.pose.orientation
yaw = math.atan2(2.0 * (q.w * q.z + q.x * q.y), 1.0 - 2.0 * (q.y * q.y + q.z * q.z))
```

Libraries such as `transforms3d` do the general case, but for a ground robot this one line is all you need.

In the course: mission 5, then every node that reads `/rover1/odom`. From mission 10 on, tf2 handles rotations for you.

## Robotics on top of ROS

### 26. Control loops

An open-loop controller follows a plan without checking the result (mission 4's square: drive for 4 s, turn for a quarter turn, repeat). A closed-loop controller measures, compares with the goal, and corrects, over and over (mission 5). The simplest closed loop is the P controller: the command is proportional to the error.

```python
error = math.atan2(dy, dx) - yaw
error = math.atan2(math.sin(error), math.cos(error))   # wrap to -pi..pi
cmd.angular.z = K_ANGULAR * error
cmd.linear.x = min(K_LINEAR * distance, MAX_SPEED)
```

Mission 5 shows why this matters. On sand the rover only gets about 60 % of the speed you ask for, so an open-loop plan falls short and nothing notices. The closed loop sees the beacon is still ahead and keeps driving.

In ROS terms a control loop is a subscriber (the measurement), a timer (the controller) and a publisher (the command).

In the course: missions 4 and 5, reused in 6, 8, 11 and 12.

### 27. State machines

When a robot does a sequence of things, write down the states and what moves it from one to the next. In code, it's a `self.state` variable and an `if/elif` per state in the timer.

```python
if self.state == 'explore' and self.battery < needed:
    self.state = 'return'
elif self.state == 'return' and self.distance_home() < 0.4:
    self.state = 'charge'
...
```

Move on when something has actually finished (the arm arrived according to `joint_states`, the service answered, the action sent its result), not after a guessed delay. Sometimes the state can be read straight from a topic (the battery level in mission 8); sometimes you have to remember it (whether the drill was cancelled to cool down, in mission 11).

In the course: missions 8 and 11, and mission 12 combines one with two control loops. For bigger robots, people use behaviour trees (Nav2 is built on BehaviorTree.CPP).

### 28. Frames and tf2

A frame is a coordinate system. The beacons and drill sites are given in the `map` frame, the camera reports range and bearing from the rover's centre (`rover1/base_link`), the laser measures from `rover1/laser`, and the arm maths works in each shoulder's frame. Moving a point between frames is a rotation plus a translation:

```python
dx, dy = x - rover_x, y - rover_y
x_r = math.cos(yaw) * dx + math.sin(yaw) * dy      # the map point (x, y), seen from the rover
y_r = -math.sin(yaw) * dx + math.cos(yaw) * dy
```

tf2 does this for the whole robot. mars_sim publishes how every frame sits relative to its parent on `/tf` and `/tf_static`, and any node can ask "where is this point in that frame?":

```python
from geometry_msgs.msg import PointStamped
from tf2_ros import Buffer, TransformException, TransformListener
import tf2_geometry_msgs  # noqa: F401  (lets tf_buffer.transform() handle PointStamped)

# in __init__
self.tf_buffer = Buffer()
self.tf_listener = TransformListener(self.tf_buffer, self)

# in the timer
point = PointStamped()
point.header.frame_id = 'map'
point.point.x, point.point.y = 5.5, 7.0
try:
    p = self.tf_buffer.transform(point, 'rover1/left_shoulder').point
except TransformException:
    return                    # no transforms yet: try again next tick
```

With rover1 at (6, 6) facing north, that point comes out at (1.00, 0.50) in `rover1/base_link` (1 m ahead, 0.5 m to the left) and at (0.60, 0.25) in `rover1/left_shoulder`. From the terminal:

```bash
ros2 run tf2_ros tf2_echo map rover1/left_gripper     # where the gripper is, in the map
ros2 run tf2_tools view_frames                        # the whole tree, as frames.pdf
```

[ARCHITECTURE.md](ARCHITECTURE.md#tf2-where-everything-is) draws the tree.

In the course: mission 6 (the camera's range and bearing are in the rover frame), mission 9 (`tf2_echo`), mission 10 (tf2 in code), missions 11 and 12 (using it). Section [35](#35-broadcasting-frames-with-tf2) shows how to publish frames of your own.

### 29. Kinematics

Forward kinematics turns joint angles into a gripper position; inverse kinematics does the reverse. For one of the rover's 2-link arms (upper arm `L1 = 0.6` m, forearm `L2 = 0.5` m), both fit in a few lines, in the shoulder frame:

```python
# forward: angles -> gripper
x = L1 * math.cos(q1) + L2 * math.cos(q1 + q2)
y = L1 * math.sin(q1) + L2 * math.sin(q1 + q2)

# inverse: gripper -> angles (None if out of reach)
c2 = (x * x + y * y - L1 * L1 - L2 * L2) / (2 * L1 * L2)
q2 = math.acos(c2) * (-1 if side == 'left' else 1)     # only if -1 <= c2 <= 1; elbow bends outwards
q1 = math.atan2(y, x) - math.atan2(L2 * math.sin(q2), L1 + L2 * math.cos(q2))
```

Check one by hand: with the left arm at `[0.5, -1.0]`, the gripper is at (0.97, 0.05) from the shoulder, so (1.37, 0.30) in `rover1/base_link`, which is what `tf2_echo rover1/base_link rover1/left_gripper` prints. Every reachable point has two solutions (elbow in or out); the sign of `q2` picks one.

For real arms, the joint layout comes from a URDF (section [40](#40-robot-description-urdf-and-robot_state_publisher)) and MoveIt solves the IK (section [43](#43-ros2_control-nav2-and-moveit-2)).

In the course: mission 9 (forward kinematics, by trying angles), mission 10 (inverse kinematics), missions 11 and 12 (using it).

### 30. Many robots, one codebase

Real fleets run identical software on every robot and tell them apart by namespace and parameters. That needs three things from your code: relative names, settings in parameters rather than constants, and a launch file to start each copy. The mission 7 fleet is exactly this ([ARCHITECTURE.md, pattern 3](ARCHITECTURE.md#pattern-3-one-node-many-robots-namespaces--parameters--launch)).

In the course: mission 3 shows that every rover gets its own namespace; mission 7 builds on it.

### 31. Mobile manipulation

A mobile manipulator drives and uses arms at the same time, which means two control loops (base and arms) coordinated by one state machine, sharing the same frames. Mission 11 keeps them apart: park, then use the arm. Mission 12 needs both arms on one heavy meteorite while the rover drives. A good way to keep it manageable is to hold both arms in one fixed posture, so that gripping becomes a parking problem. Real systems do the same: pick a good base pose first, then plan the arm.

In the course: mission 12, prepared by mission 11. [ARCHITECTURE.md, pattern 4](ARCHITECTURE.md#pattern-4-split-big-jobs-into-small-nodes) shows how you'd split such a node into layers.

## Not covered yet

Each example below was run against the simulator before it was written here. They live in your workspace next to `my_rover`.

### 32. Your own interfaces

When no standard type fits, define your own in a separate `ament_cmake` package. The course's `mars_interfaces` is one; look at `src/mars_interfaces/` for real examples of a message, a service and an action. To make your own:

```bash
cd ~/mars_rover/src
ros2 pkg create --build-type ament_cmake my_rover_interfaces
cd my_rover_interfaces && rm -rf include src && mkdir msg action
```

`my_rover_interfaces/msg/RoverStatus.msg`:

```text
string rover            # which rover
float32 battery         # 0-1, like sensor_msgs/BatteryState.percentage
int32 samples_onboard   # samples in the cache
string state            # what the rover is doing: explore, return, charge ...
```

`my_rover_interfaces/action/GoTo.action`:

```text
# Drive to a point in the map frame.
float64 x
float64 y
---
bool success
string message
---
float64 distance_left   # metres to go
```

Add to `CMakeLists.txt`, before `ament_package()`:

```cmake
find_package(rosidl_default_generators REQUIRED)
rosidl_generate_interfaces(${PROJECT_NAME}
  "msg/RoverStatus.msg"
  "action/GoTo.action"
)
```

and to `package.xml`:

```xml
<buildtool_depend>rosidl_default_generators</buildtool_depend>
<depend>action_msgs</depend>
<exec_depend>rosidl_default_runtime</exec_depend>
<member_of_group>rosidl_interface_packages</member_of_group>
```

Build it, then use it like any other type:

```bash
cd ~/mars_rover
colcon build --packages-select my_rover_interfaces && source install/setup.bash
ros2 interface show my_rover_interfaces/action/GoTo
```

```python
from my_rover_interfaces.action import GoTo
from my_rover_interfaces.msg import RoverStatus
```

Keep interfaces in their own package so that any package, Python or C++, can depend on them. A package that uses them adds `<depend>my_rover_interfaces</depend>` to its `package.xml`.

### 33. Service servers

So far you've only called services. Offering one is just as short: give `create_service` a callback that fills in the response and returns it. This node answers "how is the rover doing?":

```python
import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from sensor_msgs.msg import BatteryState
from std_msgs.msg import Int32
from std_srvs.srv import Trigger


class Report(Node):
    def __init__(self):
        super().__init__('report')
        self.battery = None
        self.onboard = 0
        self.create_subscription(BatteryState, 'battery', self.battery_callback, 10)
        self.create_subscription(Int32, 'samples_onboard', self.onboard_callback, 10)
        # server: answer every request on <namespace>/report with report_callback
        self.create_service(Trigger, 'report', self.report_callback)

    def battery_callback(self, msg: BatteryState):
        self.battery = msg.percentage

    def onboard_callback(self, msg: Int32):
        self.onboard = msg.data

    def report_callback(self, request: Trigger.Request, response: Trigger.Response):
        if self.battery is None:
            response.success = False
            response.message = 'no battery reading yet'
        else:
            response.success = True
            response.message = f'battery {self.battery:.0%}, {self.onboard} samples on board'
        return response


def main():
    rclpy.init()
    node = Report()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
```

```bash
ros2 run my_rover report --ros-args -r __ns:=/rover1
ros2 service call /rover1/report std_srvs/srv/Trigger
# std_srvs.srv.Trigger_Response(success=True, message='battery 100%, 0 samples on board')
```

The server callback must answer quickly, for the same reason as any other callback. A job that takes seconds should be an action.

### 34. Action servers

In mission 11 you used the drill's action server. Here is one of your own: `base_controller` from [ARCHITECTURE.md, pattern 4](ARCHITECTURE.md#pattern-4-split-big-jobs-into-small-nodes). It takes a `GoTo` goal (section [32](#32-your-own-interfaces)), drives the rover there with mission 5's P controller, reports the distance left as feedback, and stops when the goal is cancelled.

```python
import math

import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.action import ActionServer, CancelResponse
from rclpy.node import Node
from rclpy.task import Future
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from my_rover_interfaces.action import GoTo

K_LINEAR = 1.5
K_ANGULAR = 3.0
MAX_SPEED = 1.0
ARRIVED = 0.15     # metres: close enough


def yaw_from_quaternion(q) -> float:
    return math.atan2(2.0 * (q.w * q.z + q.x * q.y), 1.0 - 2.0 * (q.y * q.y + q.z * q.z))


class BaseController(Node):
    def __init__(self):
        super().__init__('base_controller')
        self.pose = None
        self.goal_handle = None    # the goal we are driving to, or None
        self.finished = None       # a Future the timer completes when that goal is over
        self.create_subscription(Odometry, 'odom', self.odom_callback, 10)
        self.publisher = self.create_publisher(Twist, 'cmd_vel', 10)
        self.server = ActionServer(self, GoTo, 'go_to', execute_callback=self.execute,
                                   cancel_callback=lambda goal_handle: CancelResponse.ACCEPT)
        self.create_timer(0.05, self.control_loop)
        self.create_timer(0.5, self.send_feedback)

    def odom_callback(self, msg: Odometry):
        p = msg.pose.pose
        self.pose = (p.position.x, p.position.y, yaw_from_quaternion(p.orientation))

    async def execute(self, goal_handle):
        """Runs once per accepted goal. It only waits: the timer does the driving."""
        if self.goal_handle is not None:          # a new goal replaces the old one
            self.finish(self.goal_handle.abort, False, 'replaced by a new goal')
        self.goal_handle = goal_handle
        self.finished = Future()
        return await self.finished

    def finish(self, end, success: bool, message: str):
        self.publisher.publish(Twist())           # stop
        end()                                     # mark the goal succeeded, canceled or aborted
        self.finished.set_result(GoTo.Result(success=success, message=message))
        self.goal_handle = None

    def distance_left(self) -> float:
        goal = self.goal_handle.request
        return math.hypot(goal.x - self.pose[0], goal.y - self.pose[1])

    def send_feedback(self):
        if self.goal_handle is not None and self.pose is not None:
            self.goal_handle.publish_feedback(GoTo.Feedback(distance_left=self.distance_left()))

    def control_loop(self):
        if self.goal_handle is None or self.pose is None:
            return
        distance = self.distance_left()
        if self.goal_handle.is_cancel_requested:
            self.finish(self.goal_handle.canceled, False, f'cancelled {distance:.2f} m before the goal')
            return
        if distance < ARRIVED:
            self.finish(self.goal_handle.succeed, True, f'arrived, {distance:.2f} m from the goal')
            return
        x, y, yaw = self.pose
        goal = self.goal_handle.request
        error = math.atan2(goal.y - y, goal.x - x) - yaw
        error = math.atan2(math.sin(error), math.cos(error))
        cmd = Twist()
        cmd.angular.z = K_ANGULAR * error
        if abs(error) < 0.5:
            cmd.linear.x = min(K_LINEAR * distance, MAX_SPEED)
        self.publisher.publish(cmd)


def main():
    rclpy.init()
    node = BaseController()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
```

Three things are worth noticing:

- The course rules still hold. `execute` is an `async` function: rclpy runs it as a coroutine, and while it waits at `await`, the executor carries on with odometry and timer callbacks. The timer drives the rover, exactly as in mission 5, and completes the future when the goal is over. Many tutorials write `execute` as a loop with `time.sleep` instead; that only works with a multi-threaded executor (section [37](#37-multi-threaded-executors-and-callback-groups)).
- The server decides how each goal ends: `succeed()`, `canceled()` or `abort()`, then the result. By default an rclpy action server refuses every cancel request; the `cancel_callback` accepts them.
- A new goal replaces the old one, which ends as aborted. Nav2 does the same: when you click a new goal, the robot turns towards it.

Add `<depend>my_rover_interfaces</depend>` to `my_rover/package.xml`, register `base_controller` in `setup.py`, build, and drive the rover from the terminal:

```bash
ros2 run my_rover base_controller --ros-args -r __ns:=/rover1
ros2 action send_goal --feedback /rover1/go_to my_rover_interfaces/action/GoTo "{x: 7.0, y: 5.0}"
```

```text
Goal accepted with ID: 7fb41a06b61540119ed73a0794da8c52
Feedback:
    distance_left: 4.45
...
Feedback:
    distance_left: 0.24
Result:
    success: true
message: arrived, 0.14 m from the goal
Goal finished with status: SUCCEEDED
```

`Ctrl+C` during the drive cancels it: the rover stops and the result says `cancelled 7.49 m before the goal`, with status `CANCELED`. With this server, the brain of mission 12 only has to send goals, and the same node also drives missions 5, 6 and 8.

### 35. Broadcasting frames with tf2

In missions 9 to 12 you looked frames up. Publishing one is just as short: fill in a `TransformStamped` and send it with a `TransformBroadcaster`. This node gives every sample the camera sees a frame of its own, as a child of the rover:

```python
import math

import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from geometry_msgs.msg import TransformStamped
from mars_interfaces.msg import DetectionArray
from tf2_ros import TransformBroadcaster


class SampleFrames(Node):
    def __init__(self):
        super().__init__('sample_frames')
        self.broadcaster = TransformBroadcaster(self)
        self.create_subscription(DetectionArray, '/rover1/camera/detections', self.detections_callback, 10)

    def detections_callback(self, msg: DetectionArray):
        frames = []
        for d in msg.detections:
            if d.kind != 'sample':
                continue
            t = TransformStamped()
            t.header.stamp = msg.header.stamp          # when the camera saw it
            t.header.frame_id = msg.header.frame_id    # parent: rover1/base_link
            t.child_frame_id = d.id                    # e.g. sample_3
            t.transform.translation.x = d.range * math.cos(d.bearing)
            t.transform.translation.y = d.range * math.sin(d.bearing)
            t.transform.rotation.w = 1.0               # no rotation
            frames.append(t)
        if frames:
            self.broadcaster.sendTransform(frames)


def main():
    rclpy.init()
    node = SampleFrames()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
```

Run it in mission 6 and drive until a sample is in view. tf2 now chains `map → rover1/base_link → sample_3`, so you get the sample's map position without writing the maths:

```bash
ros2 run tf2_ros tf2_echo map sample_3
# - Translation: [6.000, 5.500, 0.000]      (where sample_3 lies on the map)
```

Any node can now `transform()` into `sample_3`, or look up where it is from a shoulder. Once the sample leaves the camera's view, its frame stops updating: tf2 keeps the last position, but lookups at the current time start to fail.

A frame that never moves needs no node at all:

```bash
ros2 run tf2_ros static_transform_publisher --x 3 --y 3 --frame-id map --child-frame-id lander
ros2 run tf2_ros tf2_echo lander rover1/base_link     # the rover, seen from the lander
```

On a real robot the tree has one more level: `map → odom → base_link`. Wheel odometry drifts, so the odometry node publishes `odom → base_link` (smooth, but slowly wrong), and a localization node publishes `map → odom` (the correction). mars_sim's odometry is perfect, so it skips `odom`.

### 36. Recording with ros2 bag

`ros2 bag` records topics to disk and plays them back later with the original timing. Use it to debug a run after the fact, to test a node on the same data again and again, or to share a problem with someone.

```bash
ros2 bag record -o survey /rover1/odom /rover1/cmd_vel     # Ctrl+C to stop
ros2 bag info survey                                       # topics, counts, duration
ros2 bag play survey --topics /rover1/cmd_vel              # replay just the commands
```

```text
Duration:          43.440118871s
Messages:          2555
Topic information: Topic: /rover1/cmd_vel | Type: geometry_msgs/msg/Twist | Count: 382 | Serialization Format: cdr
                   Topic: /rover1/odom | Type: nav_msgs/msg/Odometry | Count: 2173 | Serialization Format: cdr
```

Record your mission 4 square, then replay only `cmd_vel` into a fresh mission 4: the rover drives the same square again, through the same beacons. That shows that the rover's motion depends on nothing but the commands it receives and the ground it drives on. Don't replay `/rover1/odom` while the simulator runs, or there will be two publishers of odometry telling different stories. `ros2 bag record -a` records everything.

### 37. Multi-threaded executors and callback groups

The default executor runs one callback at a time (section [16](#16-the-executor)). That's why a blocking `client.call()` inside a timer deadlocks: the answer can't be delivered while the timer callback waits for it. Sometimes waiting really is the simplest way to write a node, and then you need two things: an executor with more than one thread, and the client in its own callback group so its answer can be handled while the timer is still running.

```python
import rclpy
from rclpy.callback_groups import MutuallyExclusiveCallbackGroup
from rclpy.executors import ExternalShutdownException, MultiThreadedExecutor
from rclpy.node import Node
from std_srvs.srv import Trigger


class Photographer(Node):
    def __init__(self):
        super().__init__('photographer')
        # the client gets its own group, so its answer can arrive while the timer waits
        self.client = self.create_client(Trigger, 'take_photo',
                                         callback_group=MutuallyExclusiveCallbackGroup())
        self.create_timer(2.0, self.timer_callback)

    def timer_callback(self):
        if not self.client.service_is_ready():
            return
        response = self.client.call(Trigger.Request())   # blocks this callback until the answer is in
        self.get_logger().info(f'{response.success}: {response.message}')


def main():
    rclpy.init()
    node = Photographer()
    executor = MultiThreadedExecutor()
    executor.add_node(node)
    try:
        executor.spin()
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
```

```bash
ros2 run my_rover photographer --ros-args -r __ns:=/rover1
# [INFO] [rover1.photographer]: True: Photo of Olympus Rock sent to Earth.
```

Both parts matter. With `rclpy.spin()` instead of the multi-threaded executor, the node prints nothing and hangs. With the executor but without the separate group, it hangs too: callbacks in the same mutually exclusive group (the node's default group) never run at the same time, however many threads there are. A `ReentrantCallbackGroup` is the other kind: its callbacks may even run alongside themselves.

Parallel callbacks can touch the same variables at the same time, so you're into thread-safety territory. The course's pattern (store in callbacks, decide in one timer, `call_async` and check on a later tick) avoids needing this for most nodes.

### 38. Testing

The parts of a node that don't touch ROS (maths, decisions) are the easiest to test, which is one more reason to keep them in plain functions. This test checks mission 10's IK by running the answer back through forward kinematics:

```python
import math

import pytest

from my_rover.arm_kinematics import L1, L2, inverse_kinematics


def forward_kinematics(q1, q2):
    """Where the gripper is, in the shoulder frame."""
    x = L1 * math.cos(q1) + L2 * math.cos(q1 + q2)
    y = L1 * math.sin(q1) + L2 * math.sin(q1 + q2)
    return x, y


@pytest.mark.parametrize('side', ['left', 'right'])
@pytest.mark.parametrize('target', [(0.6, 0.5), (1.0, 0.0), (0.5, -0.4), (0.2, 0.9)])
def test_ik_reaches_the_target(side, target):
    angles = inverse_kinematics(*target, side)
    assert angles is not None
    assert forward_kinematics(*angles) == pytest.approx(target, abs=1e-9)


@pytest.mark.parametrize('side, sign', [('left', -1), ('right', 1)])
def test_elbow_bends_outwards(side, sign):
    q1, q2 = inverse_kinematics(0.6, 0.5, side)
    assert q2 * sign > 0


def test_out_of_reach_returns_none():
    assert inverse_kinematics(1.2, 0.0, 'left') is None     # longer than L1 + L2 = 1.1 m
    assert inverse_kinematics(0.05, 0.0, 'left') is None    # closer than L1 - L2 = 0.1 m
```

It tests the `arm_kinematics.py` you wrote in mission 10. It brings its own forward kinematics on purpose: if it used yours, one mistake in both functions could cancel out. Save it as `src/my_rover/test/test_arm_kinematics.py` and run:

```bash
cd ~/mars_rover/src/my_rover
python3 -m pytest test/test_arm_kinematics.py
# 11 passed
```

No simulator, no `source`, a fraction of a second. `colcon test` runs every package's tests, including the style checks `ros2 pkg create` put in `test/`. Testing whole nodes together is done with `launch_testing`.

### 39. C++ with rclcpp

Everything you learned carries over to C++; only the syntax changes. Mission 4's square in C++:

```cpp
#include <chrono>
#include <cmath>
#include <memory>
#include <vector>

#include "geometry_msgs/msg/twist.hpp"
#include "rclcpp/rclcpp.hpp"

using namespace std::chrono_literals;

struct Step
{
  double linear;    // m/s
  double angular;   // rad/s
  double duration;  // s
};

class Square : public rclcpp::Node
{
public:
  Square()
  : Node("square")
  {
    const std::vector<Step> side = {
      {1.0, 0.0, 4.0},             // drive one side
      {0.0, 0.0, 1.0},             // let it roll to a stop
      {0.0, 2.0, M_PI / 2 / 2.0},  // turn left 90 degrees
      {0.0, 0.0, 0.7},             // let the turn settle
    };
    for (int i = 0; i < 4; ++i) {
      plan_.insert(plan_.end(), side.begin(), side.end());
    }
    publisher_ = create_publisher<geometry_msgs::msg::Twist>("/rover1/cmd_vel", 10);
    step_started_ = now();
    timer_ = create_wall_timer(100ms, [this]() {timer_callback();});
  }

private:
  void timer_callback()
  {
    geometry_msgs::msg::Twist msg;   // all zeros: stand still
    if (step_ < plan_.size()) {
      if ((now() - step_started_).seconds() >= plan_[step_].duration) {
        ++step_;                     // this step is over -> next step
        step_started_ = now();
        return;
      }
      msg.linear.x = plan_[step_].linear;
      msg.angular.z = plan_[step_].angular;
    }
    publisher_->publish(msg);
  }

  std::vector<Step> plan_;
  size_t step_ = 0;
  rclcpp::Time step_started_;
  rclcpp::Publisher<geometry_msgs::msg::Twist>::SharedPtr publisher_;
  rclcpp::TimerBase::SharedPtr timer_;
};

int main(int argc, char ** argv)
{
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<Square>());
  rclcpp::shutdown();
  return 0;
}
```

Create the package with `ros2 pkg create --build-type ament_cmake my_rover_cpp --dependencies rclcpp geometry_msgs`, save the file as `src/square.cpp`, and add to `CMakeLists.txt`, before `ament_package()`:

```cmake
add_executable(square src/square.cpp)
target_link_libraries(square PUBLIC rclcpp::rclcpp ${geometry_msgs_TARGETS})
install(TARGETS square DESTINATION lib/${PROJECT_NAME})
```

Then `colcon build --packages-select my_rover_cpp` and `ros2 run my_rover_cpp square`. Older tutorials use `ament_target_dependencies(square rclcpp geometry_msgs)` instead of `target_link_libraries`; it still works on Jazzy and Humble but is deprecated from Kilted on.

The Python and C++ versions are interchangeable: mission_control can't tell which one is driving, and the C++ square finishes mission 4 the same way. Teams often prototype in Python and move the time-critical nodes to C++.

### 40. Robot description: URDF and robot_state_publisher

A URDF file describes a robot's links and joints: lengths, joint axes, limits, and the shapes to draw. `robot_state_publisher` reads the URDF plus `/joint_states` and publishes a tf2 frame for every link. RViz then draws the robot from those frames.

mars_sim does that job itself: it knows the arm geometry and publishes the frames you used in missions 9 to 12. Written as a URDF, the left arm looks like this:

```xml
<?xml version="1.0"?>
<robot name="rover">
  <link name="base_link"/>
  <link name="left_shoulder"/>
  <link name="left_upper_arm"/>
  <link name="left_forearm"/>
  <link name="left_gripper"/>

  <joint name="left_shoulder_mount" type="fixed">
    <parent link="base_link"/>
    <child link="left_shoulder"/>
    <origin xyz="0.4 0.25 0.2"/>
  </joint>
  <joint name="left_shoulder" type="revolute">
    <parent link="left_shoulder"/>
    <child link="left_upper_arm"/>
    <axis xyz="0 0 1"/>
    <limit lower="-3.14" upper="3.14" effort="10" velocity="2.0"/>
  </joint>
  <joint name="left_elbow" type="revolute">
    <parent link="left_upper_arm"/>
    <child link="left_forearm"/>
    <origin xyz="0.6 0 0"/>
    <axis xyz="0 0 1"/>
    <limit lower="-2.8" upper="2.8" effort="10" velocity="2.0"/>
  </joint>
  <joint name="left_gripper_mount" type="fixed">
    <parent link="left_forearm"/>
    <child link="left_gripper"/>
    <origin xyz="0.5 0 0"/>
  </joint>
</robot>
```

Feed it the simulator's joint states, with a frame prefix so its frames don't clash with the simulator's:

```bash
ros2 run robot_state_publisher robot_state_publisher --ros-args \
  -p robot_description:="$(cat left_arm.urdf)" -p frame_prefix:=urdf/ -r joint_states:=/rover1/joint_states
ros2 run tf2_ros tf2_echo urdf/base_link urdf/left_gripper
```

The gripper comes out exactly where `tf2_echo rover1/base_link rover1/left_gripper` puts it. The joint names (`left_shoulder`, `left_elbow`) are what connects the two: they're the names in `JointState`. Add a `<visual>` with a box or cylinder to each link and RViz's RobotModel display draws the arm. Real robots work this way, usually with `xacro` to keep the URDF short. The [URDF tutorials](https://docs.ros.org/en/jazzy/Tutorials/Intermediate/URDF/URDF-Main.html) walk through building a description step by step.

### 41. Simulators and simulated time

mars_sim is a 2-D teaching simulator. For real robots the usual choice is Gazebo (Harmonic is the version paired with Jazzy; Humble uses Fortress), which simulates physics, sensors and 3-D worlds and talks to ROS through the same topics a real robot uses: `cmd_vel` in, `odom`, `scan` and `joint_states` out. Your mission 5 controller would drive a Gazebo robot after a remap or two.

Simulators often run faster or slower than real time, so they publish their own clock on `/clock`. Nodes started with `use_sim_time:=true` take their time from it. mars_sim runs in real time and has no `/clock`, but section [18](#18-logging-and-time) still says to use `self.get_clock()` rather than Python's `time`: code written that way works in any simulation and on the robot unchanged.

### 42. Lifecycle nodes and composition

A lifecycle (managed) node has explicit states: unconfigured, inactive, active and finalized. A supervisor can configure every node first and activate them all together, or deactivate a misbehaving one without killing it. Nav2 is built from lifecycle nodes; `ros2 lifecycle` inspects and changes their states.

Composition runs several nodes in one process instead of one process each, so messages between them can skip the network layer. `ros2 component` loads nodes into a running container. You don't need either until performance or start-up order become real problems.

### 43. ros2_control, Nav2 and MoveIt 2

Three large frameworks do, for real robots, what you did by hand in the course:

| Framework | Does | You did it in |
|---|---|---|
| ros2_control | hardware drivers and controllers, with command and state interfaces per joint; its `diff_drive_controller` takes `cmd_vel` and publishes odometry, its `joint_state_broadcaster` publishes `/joint_states` | missions 2 to 5 (`cmd_vel` in, `odom` out) and 9 to 11 (`arm/joint_command` in, `joint_states` out) |
| Nav2 | maps, localization, path planning and obstacle avoidance; driven by the `navigate_to_pose` action, and it outputs `cmd_vel` | missions 5, 6 and 8, and the `go_to` server in section [34](#34-action-servers) |
| MoveIt 2 | arm motion planning, IK solvers and collision checking, from the robot's URDF | missions 10 to 12 |

Each one builds on the parts above: topics for streams, actions for long jobs, parameters for configuration, tf2 for frames, URDF for the robot's shape, lifecycle nodes for start-up. Once those make sense, the frameworks are mostly a matter of reading their configuration files.

## How to continue

A good order after mission 12:

1. Write `my_rover_interfaces` and the `go_to` action server (sections [32](#32-your-own-interfaces) and [34](#34-action-servers)), then split your mission 12 node into the three layers of [ARCHITECTURE.md, pattern 4](ARCHITECTURE.md#pattern-4-split-big-jobs-into-small-nodes).
2. Record a mission with `ros2 bag` and put your IK under a test (sections [36](#36-recording-with-ros2-bag) and [38](#38-testing)). Both pay off on every project after this one.
3. Describe the rover in URDF and look at it in RViz (sections [21](#21-rviz) and [40](#40-robot-description-urdf-and-robot_state_publisher)).
4. Move to Gazebo and Nav2 with one of the robots from the [Nav2 getting-started guide](https://docs.nav2.org/getting_started/index.html). You'll recognise the pieces: `cmd_vel`, `odom`, `scan`, tf2 frames and a `navigate_to_pose` action.

---

**Home:** [README](README.md) · **See also:** [ARCHITECTURE.md](ARCHITECTURE.md) · [CHEATSHEET.md](CHEATSHEET.md) · [CHECKLIST.md](CHECKLIST.md)
