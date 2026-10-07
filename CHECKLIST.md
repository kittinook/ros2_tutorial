# Progress checklist

Keep track of where you are in the course. Copy this file (or print it) and tick a box when it's done:
change `- [ ]` to `- [x]`, or just tick it with a pen.

For every mission there are three kinds of box:

- **Objectives**: what mission control checks. It ticks these in the window too.
- **Steps**: the steps of the mission guide, so you can see where you stopped last time.
- **Can you...?**: the skills the mission is really about. The same questions are on the checklist slide of each mission in `slides/`. If you can't answer one yet, the mission guide (or [CONCEPTS.md](CONCEPTS.md)) explains it.

Your best stars are saved too: `ros2 run mission_control progress`.

## Overview

| # | Mission | Done | Stars |
|---|---|---|---|
| 0 | [Landing](missions/00-landing.md) | ☐ | ___ / 3 |
| 1 | [Telemetry](missions/01-telemetry.md) | ☐ | ___ / 3 |
| 2 | [Manual Drive](missions/02-manual-drive.md) | ☐ | ___ / 3 |
| 3 | [Mission Control](missions/03-mission-control.md) | ☐ | ___ / 3 |
| 4 | [Survey Square](missions/04-survey-square.md) | ☐ | ___ / 3 |
| 5 | [Waypoints](missions/05-waypoints.md) | ☐ | ___ / 3 |
| 6 | [Sample Hunter](missions/06-sample-hunter.md) | ☐ | ___ / 3 |
| 7 | [Rover Fleet](missions/07-rover-fleet.md) | ☐ | ___ / 3 |
| 8 | [Boss: Power Crisis](missions/08-boss-power-crisis.md) | ☐ | ___ / 3 |
| 9 | [Arm Check](missions/09-arm-check.md) | ☐ | ___ / 3 |
| 10 | [Frames](missions/10-frames.md) | ☐ | ___ / 3 |
| 11 | [Drill & Stow](missions/11-drill-and-stow.md) | ☐ | ___ / 3 |
| 12 | [Boss: Meteorite Recovery](missions/12-boss-meteorite-recovery.md) | ☐ | ___ / 3 |

---

## Part 1: the rover

### Mission 0: Landing

Objectives
- [ ] Make the rover move
- [ ] Drive to beacon 1

Steps
- [ ] 1. Install what you need
- [ ] 2. Build the workspace
- [ ] 3. Launch the mission
- [ ] 4. Drive

Can you...?
- [ ] build the workspace with `colcon build`?
- [ ] explain why every new terminal needs `source`?
- [ ] launch a mission and say what each part of the window shows?
- [ ] drive the rover with teleop and explain what `-r cmd_vel:=/rover1/cmd_vel` does?
- [ ] name the three nodes that were running?

### Mission 1: Telemetry

Objectives
- [ ] Send anything on rover1's radio
- [ ] Confirm the code from Earth on the radio
- [ ] Radio how many times per second /rover1/odom is published

Steps
- [ ] 1. Who's in the system?
- [ ] 2. Listen to the rover's position
- [ ] 3. Use the radio
- [ ] 4. Find the message from Earth
- [ ] 5. Measure the rate

Can you...?
- [ ] list the nodes and topics in a running system?
- [ ] listen to a topic with `ros2 topic echo`?
- [ ] find a topic's message type and the fields of that type?
- [ ] send a message yourself with `ros2 topic pub`?
- [ ] measure how often a topic is published?
- [ ] explain why a publisher doesn't need to know who is listening?

### Mission 2: Manual Drive

Objectives
- [ ] Reach the beacons in order 1 → 2 → 3
- [ ] Drive one full circle around the crater

Steps
- [ ] 1. Take it for a spin
- [ ] 2. Plan the route to the beacons
- [ ] 3. Drive a circle around the crater

Can you...?
- [ ] say what `linear.x` and `angular.z` in a `Twist` mean, with their units?
- [ ] convert an angle in degrees to radians?
- [ ] work out how far a command moves the rover, using the 1-second rule and the top speed?
- [ ] use `--once`, `--rate` and `--times`, and put them in the right place?
- [ ] drive a circle and predict its radius?
- [ ] explain how mission control can tell teleop from your commands?

### Mission 3: Mission Control

Objectives
- [ ] Spawn a second rover named scout
- [ ] Photograph the landmarks

Steps
- [ ] 1. Open the phone book
- [ ] 2. Spawn a second rover
- [ ] 3. Take a photo
- [ ] 4. Teleport to the landmarks

Can you...?
- [ ] list the services and find the type a service uses?
- [ ] read a service definition and say which part is the request and which the response?
- [ ] call a service from the terminal and read `success` and `message` in a `Trigger` response?
- [ ] explain why spawning a rover creates a whole new set of topics and services?
- [ ] say when to use a topic and when to use a service?

### Mission 4: Survey Square

Objectives
- [ ] Drive a square through the beacons 1 → 2 → 3 → 4
- [ ] Drive the rover with your own node

Steps
- [ ] 1. Create a package
- [ ] 2. A first node that drives in circles
- [ ] 3. Register the program
- [ ] 4. Build and run
- [ ] 5. Drive the square

Can you...?
- [ ] create a Python package with `ros2 pkg create`?
- [ ] write a node with a publisher and a timer?
- [ ] register a program in `setup.py` and start it with `ros2 run`?
- [ ] say when you have to build and source again, and when you don't?
- [ ] explain the difference between a package, an executable and a node?
- [ ] explain why this node is "open loop", and why it ends a little off its start?

### Mission 5: Waypoints

Objectives
- [ ] Reach the beacons in order (5)
- [ ] Drive the rover with your own node

Steps
- [ ] 1. Listen first
- [ ] 2. From quaternion to yaw
- [ ] 3. A little maths
- [ ] 4. Decide with a P controller

Can you...?
- [ ] write a subscriber whose callback only stores the data?
- [ ] explain why the decisions happen in a timer and not in the callback?
- [ ] get x, y and the yaw out of a `nav_msgs/Odometry` message?
- [ ] compute the distance and heading error to a point with `hypot` and `atan2`, wrapped into −π..π?
- [ ] write a P controller and say what each gain changes?
- [ ] explain why sand ruins an open-loop plan but not a closed loop?

### Mission 6: Sample Hunter

Objectives
- [ ] Collect samples (5)
- [ ] Drive the rover with your own node

Steps
- [ ] 1. Look around
- [ ] 2. Drive in and collect
- [ ] 3. Nothing in sight, so patrol
- [ ] 4. Don't hit the rocks

Can you...?
- [ ] pick the closest sample from a `DetectionArray`, and say what range and bearing mean?
- [ ] find the angle of laser ray `i` and the closest obstacle in front?
- [ ] create a service client and call it with `call_async`?
- [ ] say what a future is and when to check `.done()`?
- [ ] explain why waiting inside a callback causes a deadlock?
- [ ] describe the hunter's decision: chase, patrol, or steer around a rock?

### Mission 7: Rover Fleet

Objectives
- [ ] Run nodes in the `/rover1` and `/rover2` namespaces
- [ ] Change a parameter while the node is running
- [ ] Each rover collects at least 3 samples
- [ ] Samples collected in total (10)

Steps
- [ ] 1. Namespaces take the rover's name out of the code
- [ ] 2. Parameters you can change from outside
- [ ] 3. A launch file for the whole fleet

Can you...?
- [ ] run the same node for two rovers with `__ns`?
- [ ] explain how a relative name like `'cmd_vel'` becomes `/rover2/cmd_vel`?
- [ ] declare a parameter in code and read it?
- [ ] set a parameter at start-up and change it while the node runs?
- [ ] write a launch file and install it from `setup.py`?

### Mission 8 (boss): Power Crisis

Objectives
- [ ] Samples delivered to the lander (6)
- [ ] Drive the rover with your own node

Steps
- [ ] 1. TODOs 1 and 3: the rover hunts like in mission 6 (and runs out of battery)
- [ ] 2. TODOs 4 and 5: it comes home in time
- [ ] 3. TODOs 2 and 6: it unloads, charges and goes out again

Can you...?
- [ ] list a robot node's inputs and outputs as sense, think, act?
- [ ] describe a multi-step job as states, and what makes the rover change state?
- [ ] read the battery from `sensor_msgs/BatteryState` and decide when to turn back?
- [ ] call two different services from one node without spamming them?
- [ ] turn a skeleton into a working node, one TODO at a time?

---

## Part 2: the arms

### Mission 9: Arm Check

Objectives
- [ ] Touch beacon 1 with the LEFT gripper
- [ ] Touch beacon 2 with the RIGHT gripper
- [ ] Pick up the sample with a gripper

Steps
- [ ] 1. Read the joints
- [ ] 2. Where is the gripper? Ask tf2
- [ ] 3. Move an arm
- [ ] 4. Touch the beacons
- [ ] 5. Pick up the sample

Can you...?
- [ ] read `/rover1/joint_states` and say which angle belongs to which joint?
- [ ] move one arm with `arm/joint_command` from the terminal?
- [ ] find where a gripper is with `ros2 run tf2_ros tf2_echo`?
- [ ] close and open a gripper with a `SetBool` service and read its answer?
- [ ] work out where the gripper is from two joint angles (forward kinematics)?

### Mission 10: Frames

Objectives
- [ ] Touch the targets in order (6)
- [ ] Move the arms with your own node

Steps
- [ ] 1. Add the Part 2 dependencies
- [ ] 2. The maths as plain Python
- [ ] 3. The node
- [ ] 4. Run it
- [ ] 5. (optional) See the frames

Can you...?
- [ ] convert a point from the map frame into the rover frame by hand?
- [ ] do the same with a tf2 `Buffer`, `TransformListener` and `transform()`?
- [ ] explain forward versus inverse kinematics?
- [ ] compute both joint angles of a 2-link arm with the law of cosines, and say when a point is out of reach?
- [ ] test your maths without starting ROS?

### Mission 11: Drill & Stow

Objectives
- [ ] Cores stowed in the cache (3)
- [ ] Drive the rover with your own node

Steps
- [ ] 1. Drill from the terminal
- [ ] 2. An action client in code
- [ ] 3. The node
- [ ] 4. Run it

Can you...?
- [ ] use `ros2 action list`, `info` and `send_goal --feedback`?
- [ ] send a goal from code and receive feedback and the result?
- [ ] cancel a goal, and tell SUCCEEDED, CANCELED and ABORTED apart?
- [ ] say when a job should be an action instead of a service?
- [ ] turn a camera detection into a point the arm can reach (range/bearing → base_link → tf2 → IK)?
- [ ] move to the next state when something has finished, not after a guessed delay?

### Mission 12 (boss): Meteorite Recovery

Objectives
- [ ] Meteorites set down on the lander (2)
- [ ] Drive the rover with your own node

Steps
- [ ] 1. TODOs 1 to 3: subscriptions, publishers, clients
- [ ] 2. TODO 4: the forklift posture
- [ ] 3. TODOs 5 and 6: grippers and parking
- [ ] 4. TODOs 7 to 11: the states

Can you...?
- [ ] run two control loops (driving and arms) from one state machine?
- [ ] turn a manipulation problem into a driving problem with a fixed arm posture?
- [ ] explain why both grippers must hold the meteorite, and what happens if they drift apart?
- [ ] sketch how you would split `meteorite_mover` into several nodes?

---

## After the course

The next steps (your own interfaces, service and action servers, broadcasting frames, URDF, ros2 bag, executors, testing, C++, Nav2) are in
[CONCEPTS.md](CONCEPTS.md#not-covered-yet), each with a short tested example, and a self-check of its own.
