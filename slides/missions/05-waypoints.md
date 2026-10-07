---
marp: true
title: "Mission 5: Waypoints"
description: Step-by-step teaching slides for Mars Rover Academy mission 5
paginate: true
size: 16:9
footer: Mars Rover Academy · Mission 5
style: |
  @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;600;700&family=JetBrains+Mono:wght@400;600&display=swap');
  section {
    background: #F6F4EE;
    color: #1B2A3A;
    font-family: 'IBM Plex Sans', Arial, sans-serif;
    font-size: 26px;
    padding: 64px 72px 72px;
    justify-content: flex-start;
  }
  h1 { font-size: 44px; font-weight: 600; color: #13293D; margin: 0 0 24px; }
  h3 { font-size: 28px; font-weight: 600; color: #13293D; margin: 0 0 6px; }
  strong { color: #13293D; }
  header {
    font-size: 16px; font-weight: 600; letter-spacing: 2px; text-transform: uppercase;
    color: #2F7A4F; top: 28px; left: 72px;
  }
  footer { font-size: 15px; color: #7A8590; left: 72px; }
  section::after { font-size: 15px; color: #7A8590; right: 72px; }
  code { font-family: 'JetBrains Mono', 'Courier New', monospace; background: #E9E5DA; color: #13293D; border-radius: 6px; padding: 1px 6px; }
  pre { background: #0B1C2C; border-radius: 12px; padding: 20px 26px; font-size: 20px; line-height: 1.5; }
  pre code { background: transparent; color: #D7E3DC; padding: 0; }
  code, pre code { font-variant-ligatures: none; }
  pre code span { color: #D7E3DC; }
  pre .hljs-comment { color: #8FA3B0; }
  pre .hljs-string { color: #F2C27B; }
  pre .hljs-keyword, pre .hljs-built_in, pre .hljs-title { color: #9CD3B0; }
  table { font-size: 22px; border-collapse: collapse; margin: 0 auto; }
  th { background: #E9E5DA; color: #13293D; }
  th, td { border: 1px solid #DDD8CC; padding: 8px 16px; }
  td { background: #FDFCF8; }
  p:has(> img:only-child) { text-align: center; margin: 12px 0; }
  blockquote { border-left: 6px solid #E07A1F; background: #FBEBDD; color: #4A2C10; padding: 10px 20px; margin: 16px 0; }

  section.lead { background: #13293D; color: #EEF2EC; justify-content: center; }
  section.lead h1 { font-size: 68px; color: #F6F4EE; margin-bottom: 16px; }
  section.lead p { font-size: 28px; color: #BFD0C8; }
  section.lead strong { color: #F2A541; }
  section.lead header { color: #F2A541; }
  section.lead footer, section.lead::after { color: #8FA3B0; }

  section.roadmap table { font-size: 20px; }
  section.roadmap th, section.roadmap td { padding: 6px 16px; }

  section.checklist ul { list-style: none; padding-left: 0; }
  section.checklist li { font-size: 26px; margin: 10px 0; }
  section.checklist li::before { content: "☐  "; color: #2F7A4F; font-weight: 700; }
---

<!-- _class: lead -->
<!-- _paginate: false -->
<!-- header: Mars Rover Academy · Part 1 -->

# Mission 5: Waypoints

Five beacons at random spots, different every run, and sand on most of the way. The rover has to check where it is, check where the beacon is, and steer there by itself.

**You will learn:** subscribers · callbacks · `Odometry` · quaternion → yaw · closed loop · atan2 and angle wrapping · P controller

<!--
Suggested time: 45 to 60 minutes. Drawing the atan2 triangle and the quaternion → yaw formula on the board helps a lot, so keep a whiteboard free for Steps 2 and 3.
Goal of the session: everyone has a go_to_goal node that drives the rover through all five beacons without help.
This builds on my_rover from mission 4. Anyone whose square.py doesn't run yet should fix that first.
-->

---

<!-- _class: roadmap -->
<!-- header: Where we are -->

# Part 1 roadmap

| | # | Mission | You learn |
|---|---|---|---|
| ✓ | 0 | Landing | workspace, build, launch, teleop, remapping |
| ✓ | 1 | Telemetry | nodes, topics, messages |
| ✓ | 2 | Manual Drive | publishing `Twist`, speeds and angles |
| ✓ | 3 | Mission Control | services: request and response |
| ✓ | 4 | Survey Square | a package and a Python publisher |
| **▶** | **5** | **Waypoints** | **subscribers, `Odometry`, closed-loop control** |
| | 6 | Sample Hunter | camera and laser, service clients in code |
| | 7 | Rover Fleet | namespaces, parameters, launch files |
| | 8 | Boss: Power Crisis | all of the above, state machines, battery |

<!--
About 1 minute.
Last time our node could only talk. Today it also listens. This controller comes back in missions 6, 7 and 8 (and in Part 2), so it's worth getting it right.
-->

---

<!-- header: Mission 5 · Goal -->

# Today's goal

<style scoped>p, li { font-size: 24px; } pre { font-size: 18px; }</style>

![bg right:38% contain](../../docs/images/mars/mission-5.png)

**Objectives**
1. Reach the beacons in order (0/5)
2. Drive the rover with your own node (no teleop, `ros2 topic pub` or teleport)

**Stars:** ≤ 1.3 × route length + 8 s = ⭐⭐⭐ · ≤ 2 × route length + 20 s = ⭐⭐ · the clock starts when the rover starts moving

```bash
# Terminal 1
ros2 launch mission_control mission.launch.py mission:=5
```

```text
[mission_control]: Route length 53.1 m: 3 stars within 77 s
```

<!--
About 2 minutes. Launch it now and leave it running.
The route is different every run, so the star times are too; terminal 1 prints them when the mission starts. Point out that the beacons are in different places on every machine, so copying a neighbour's route or memorising coordinates won't work.
"Your own node" means no teleop, no ros2 topic pub and no teleport: mission_control checks who publishes on cmd_vel and watches for teleports.
-->

---

<!-- header: Mission 5 · Concept -->

# Why mission 4's trick won't work here

- In mission 4 your node only **sent** messages. It drove with its eyes closed and counted seconds.
- On **sand** the rover only gets about 60% of the speed you ask for, and craters slow it down too.
- A plan that says "drive 5 s at 1 m/s" comes up short every time it crosses a sand patch.

The node has to **look** where the rover really is.

<!--
About 2 minutes.
Ask: what did square.py know about where the rover really was? Nothing. It counted time, and it still ended 0.3 m off on flat ground. With sand it would miss every beacon after the first patch.
-->

---

<!-- header: Mission 5 · Concept -->

# Publishers talk, subscribers listen

- This time the node also **receives** messages, through a **subscriber**
- Every time a message arrives, ROS calls your **callback**

```python
self.create_subscription(Type, 'topic', callback, 10)
```

One node can be both a publisher and a subscriber.

<!--
About 2 minutes.
The 10 is the queue size, the same as for the publisher in mission 4.
Stress that you never call the callback yourself. You hand the function to ROS, and ROS calls it with the message. People coming from plain Python often expect to call it in a loop.
-->

---

<!-- header: Mission 5 · Concept -->

# Closed loop

The node does this over and over:

1. **look** at the position
2. **work out** a command
3. **steer**
4. look at the new position and start again

That's a **closed loop**, also called feedback. Almost every real robot works this way.

Sand doesn't fool it: the rover is slower there, so the distance shrinks more slowly, and the node simply keeps steering until it arrives.

<!--
About 2 minutes.
A good everyday example: steering a bike. You don't plan every handlebar movement in advance, you look and correct all the time.
square.py was open loop: it carried on with its plan whatever happened. We come back to that in Check yourself.
-->

---

<!-- header: Mission 5 · Concept -->

# What we're building

![w:1100](../images/missions/m05-1.png)

- Two topics come in: the rover's odometry and the beacons
- The callbacks only **remember** the latest data
- A timer (`control_loop`) decides what to do with it and publishes `cmd_vel`

<!--
About 2 minutes. Draw this on the board before anyone types code: what goes in, what comes out.
Yellow is the node we write today. Note the rates: odometry arrives 50 times per second, the loop decides 20 times per second. Step 4 explains why the work is split this way.
mission_control's /mission/goals feeds both our node and the simulator, which draws the beacons. One topic, two subscribers.
-->

---

<!-- header: Mission 5 · Step 1 of 4 -->

# Step 1: Listen first

<style scoped>pre { font-size: 18px; line-height: 1.35; padding: 14px 24px; }</style>

mission_control announces where the beacons are on a topic:

```bash
ros2 topic echo --once /mission/goals
```

```text
header:
  ...
  frame_id: map
poses:
- position:
    x: 3.78
    y: 15.91
    z: 0.6        # ← the simulator uses z as the beacon's drawing radius, ignore it
  orientation: ...
- position:
    ...
```

<!--
About 2 minutes. Run it live in a second terminal. Everyone's numbers will be different because the beacons are random.
--once prints one message and exits, which is handy for a topic that keeps repeating.
-->

---

<!-- header: Mission 5 · Step 1 of 4 -->

# Reading the beacons

- The type is `geometry_msgs/msg/PoseArray`
- `poses` is a list of positions
- The first one, `poses[0]`, is always **the next beacon**
- Reach it and it disappears from the list
- `z` is the beacon's drawing radius here. Ignore it.

So the node only ever has to aim at `poses[0]`.

<!--
About 1 minute.
This is a nice design point: mission_control keeps the list up to date, so our node doesn't have to remember which beacons it has already reached.
If someone asks where the type name comes from: ros2 topic info /mission/goals, as in mission 1.
-->

---

<!-- header: Mission 5 · Step 1 of 4 -->

# Where am I? Odometry

<style scoped>pre { font-size: 15px; line-height: 1.3; padding: 12px 22px; margin: 8px 0; } section { padding-top: 56px; } h1 { margin-bottom: 8px; } p { margin: 6px 0; }</style>

The rover's own position comes from its **odometry**:

```bash
ros2 topic echo --once /rover1/odom
```

```text
header:
  ...
  frame_id: map
child_frame_id: rover1/base_link
pose:
  pose:
    position:
      x: 3.0
      y: 3.0
      z: 0.0
    orientation:
      x: 0.0
      y: 0.0
      z: 0.0
      w: 1.0
  covariance: ...
twist:
  ...
```

<!--
About 2 minutes. Run it live with the rover still on the lander.
Learners should see the rover at (3, 3). The twist part (how fast it's moving) is there too, but we don't need it today.
-->

---

<!-- header: Mission 5 · Step 1 of 4 -->

# Reading the odometry

- The type is `nav_msgs/msg/Odometry`, the standard message real robots use for "where am I and how fast am I going"
- `pose.pose.position` is where the rover is
- `pose.pose.orientation` is which way it faces, but it isn't an angle: it has four numbers, x, y, z and w

That's a **quaternion**. Step 2 turns it into an angle.

<!--
About 2 minutes.
Note the double pose: Odometry has a pose with a covariance (how sure the robot is), and the pose itself sits inside that. So it's msg.pose.pose.position. A very common typo is msg.pose.position.
Don't explain quaternions yet; just name them. Step 2 does the rest.
-->

---

<!-- header: Mission 5 · Step 1 of 4 -->

# go_to_goal.py, first version (part 1 of 3)

<style scoped>pre { font-size: 18px; }</style>

Create `src/my_rover/my_rover/go_to_goal.py`:

```python
# my_rover/my_rover/go_to_goal.py  (first version: just listen)
import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from geometry_msgs.msg import PoseArray
from nav_msgs.msg import Odometry


class GoToGoal(Node):
    def __init__(self):
        super().__init__('go_to_goal')
        # subscriber: when a message arrives on /rover1/odom, call self.odom_callback
        self.create_subscription(Odometry, '/rover1/odom', self.odom_callback, 10)
        self.create_subscription(PoseArray, '/mission/goals', self.goals_callback, 10)
```

<!--
About 3 minutes, typing included.
Two subscriptions, each with its own message type and its own callback. Note there are no brackets after self.odom_callback: we pass the function, we don't call it.
Common mistake: importing Odometry from the wrong package. It lives in nav_msgs.msg (which is why mission 4 listed nav_msgs as a dependency).
-->

---

<!-- header: Mission 5 · Step 1 of 4 -->

# go_to_goal.py, first version (part 2 of 3)

<style scoped>pre { font-size: 16px; }</style>

```python
    def odom_callback(self, msg: Odometry):
        # odom arrives 50 times/s -> throttle the log to once per second or it floods the screen
        p = msg.pose.pose.position
        q = msg.pose.pose.orientation
        self.get_logger().info(f'rover at x={p.x:.2f} y={p.y:.2f}, orientation z={q.z:.2f} w={q.w:.2f}',
                               throttle_duration_sec=1.0)

    def goals_callback(self, msg: PoseArray):
        if msg.poses:
            goal = msg.poses[0].position
            self.get_logger().info(f'next beacon ({goal.x:.2f}, {goal.y:.2f}), {len(msg.poses)} left',
                                   throttle_duration_sec=1.0)
```

- `msg` is the message that just arrived
- `throttle_duration_sec=1.0` prints at most once per second
- `if msg.poses:` skips the empty list after the last beacon

<!--
About 3 minutes.
Show what happens without the throttle if there's time: 50 lines per second scrolling past. That's the reason for it.
The callbacks only log for now. In Step 4 they will store the data instead.
-->

---

<!-- header: Mission 5 · Step 1 of 4 -->

# go_to_goal.py, first version (part 3 of 3)

```python
def main():
    rclpy.init()
    node = GoToGoal()
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

<!--
About 1 minute.
The same main() as in mission 4, with GoToGoal instead of the Square class.
rclpy.spin is what waits for messages and calls the callbacks. Without spin, nothing would ever arrive.
Fast typists can copy main() from square.py and change the class name.
-->

---

<!-- header: Mission 5 · Step 1 of 4 -->

# Register and rebuild

Add it to `setup.py` after the existing line. Mind the comma:

```python
            'square = my_rover.square:main',
            'go_to_goal = my_rover.go_to_goal:main',
```

You changed `setup.py`, so rebuild:

```bash
cd ~/mars_rover
colcon build --symlink-install --packages-select my_rover
source install/setup.bash
ros2 run my_rover go_to_goal
```

<!--
About 3 minutes.
The missing comma after the square line is the classic mistake. Python then glues the two strings together and neither entry point works.
With --symlink-install, later edits to go_to_goal.py don't need a rebuild. Edits to setup.py always do.
-->

---

<!-- header: Mission 5 · Step 1 of 4 -->

# You should see

```text
[INFO] [go_to_goal]: rover at x=3.00 y=3.00, orientation z=0.00 w=1.00
[INFO] [go_to_goal]: next beacon (3.78, 15.91), 5 left
```

The node can see the rover and the next beacon now.

The rover doesn't move yet. That's expected: nothing is published.

<!--
About 1 minute.
Everyone's beacon numbers will differ. The rover line should match exactly if they haven't moved it.
Keep the file: the next steps grow the same node.
-->

---

<!-- header: Mission 5 · Checkpoint -->

# Stuck?

| Symptom | Fix |
|---|---|
| `No executable found` | missing line in `setup.py` / forgot to rebuild after editing `setup.py` / forgot `source install/setup.bash` |
| `Package 'my_rover' not found` | forgot `source install/setup.bash` (in the terminal where you `ros2 run`) |
| 1 star + "teleop / ros2 topic pub detected" | teleop or `ros2 topic pub` is still running in another terminal; close them all and retry |

**Done?** Everyone should see both log lines before moving on.

<!--
These are rows from mission 4's troubleshooting table, and they're the same problems here.
Walk around now. The third row matters later: if a teleop from earlier is still open, the "own node" objective fails.
-->

---

<!-- header: Mission 5 · Step 2 of 4 -->

# Step 2: From quaternion to yaw

- A quaternion describes any rotation in 3D: a drone can roll, pitch and yaw all at once
- ROS uses quaternions everywhere, so the same messages work for drones, arms and submarines as well as rovers
- The rover only ever turns about the vertical z axis

The angle it faces on the map is called **yaw**: 0 faces +x (right on the map), and it grows counter-clockwise, in radians.

<!--
About 3 minutes.
Why not just three angles? Three separate angles get into trouble when you combine them; quaternions don't. You don't need the theory today, only the flat-ground case on the next slide.
Yaw is the same convention as angular.z in mission 2: positive is counter-clockwise (to the left).
-->

---

<!-- header: Mission 5 · Step 2 of 4 -->

# A turn about z only

For a turn about z, x and y stay 0, and the other two numbers are

z = sin(yaw / 2) and w = cos(yaw / 2)

| Rover faces | yaw | z | w |
|---|---|---|---|
| right (+x) | 0 | 0.00 | 1.00 |
| up (+y) | π/2 (90°) | 0.71 | 0.71 |
| left (−x) | π (180°) | 1.00 | 0.00 |
| down (−y) | −π/2 (−90°) | −0.71 | 0.71 |

<!--
About 3 minutes.
Check the first row against what Step 1 printed: on the lander the rover faces right, and the log said z=0.00 w=1.00.
Ask someone to drive the rover a quarter turn left with ros2 topic pub (mission 2) and watch z and w head towards 0.71.
-->

---

<!-- header: Mission 5 · Step 2 of 4 -->

# Getting the yaw back

The standard formula gets the yaw back out of any quaternion:

<style scoped>pre { font-size: 17px; }</style>

```python
def yaw_from_quaternion(q) -> float:
    """The rover only turns about z, so this is all of the quaternion we need."""
    return math.atan2(2.0 * (q.w * q.z + q.x * q.y), 1.0 - 2.0 * (q.y * q.y + q.z * q.z))
```

Copy it as it is. You'll find the same function in almost every ROS project that drives on the ground.

<!--
About 2 minutes.
Don't derive it. Check one case instead: with x = y = 0 it becomes atan2(2wz, 1 - 2z²). For the "up" row (z = w = 0.71) that's atan2(1, 0) = π/2. It works.
It needs `import math`, which the full file in Step 4 has.
-->

---

<!-- header: Mission 5 · Step 3 of 4 -->

# Step 3: A little maths

```text
                               B  beacon (goal_x, goal_y)
                             / |
                 distance  /   |
                         /     |  dy = goal_y - y
                       /       |
                     /  a      |
     rover (x, y)  R ------------+
                      dx = goal_x - x

     a     = angle we should face  = atan2(dy, dx)
     yaw   = angle we face now     (from /rover1/odom)
     error = a - yaw               (how far off we are)
```

<!--
About 3 minutes. Draw this on the board as you talk. It's the most useful drawing of the day.
Three numbers matter: how far away the beacon is, which way we should face, and which way we face now. The difference between the last two is the heading error.
-->

---

<!-- header: Mission 5 · Step 3 of 4 -->

# Three formulas

- distance = `math.hypot(dx, dy)` (Pythagoras)
- angle to face = `math.atan2(dy, dx)` (in radians)
- heading error = angle to face − yaw

<!--
About 2 minutes.
hypot is just sqrt(dx*dx + dy*dy).
Why atan2 and not atan? atan(dy / dx) can't tell left from right: (dx, dy) and (−dx, −dy) give the same value, and it divides by zero when dx = 0. atan2 looks at the signs of both and returns the full angle, from −π to π.
Radians: π is 180°, π/2 is 90°. The yaw from Step 2 is also in radians, so the units match.
-->

---

<!-- header: Mission 5 · Step 3 of 4 -->

# Worked example

With the numbers from Step 1: rover at (3.00, 3.00), yaw = 0 (z = 0.00, w = 1.00), beacon at (3.78, 15.91).

| | Calculation | Result |
|---|---|---|
| dx | 3.78 − 3.00 | 0.78 |
| dy | 15.91 − 3.00 | 12.91 |
| distance | hypot(0.78, 12.91) | 12.93 m |
| angle to face | atan2(12.91, 0.78) | 1.51 rad (87°) |
| heading error | 1.51 − 0 | 1.51 rad |

The beacon is almost straight up, so the rover has to turn left almost 90°.

<!--
About 3 minutes.
Ask the class to predict before you reveal the numbers: the beacon is far above and a little to the right of the rover, so the angle is a bit less than 90°.
A positive error means turn left (counter-clockwise), negative means turn right. Same convention as angular.z in mission 2.
-->

---

<!-- header: Mission 5 · Step 3 of 4 -->

# Angle wrapping

> Careful: if you should face 170° but face −170°, the error comes out as 340° and the rover spins almost a full turn when −20° would do.

Fix it with the standard trick, which always squeezes an angle into −π..π:

```python
            error = math.atan2(math.sin(error), math.cos(error))
```

| error before | sin, cos | error after |
|---|---|---|
| 340° (5.93 rad) | same as for −20° | −20° (−0.35 rad) |

<!--
About 3 minutes.
Draw a circle: 170° and −170° are only 20° apart, across the "back" of the circle where the angle jumps from π to −π.
Why the trick works: sin and cos don't change when you add or subtract a full turn, and atan2 always answers in −π..π. So it returns the same direction, the short way round.
Without this line the rover sometimes does a pirouette before driving to a beacon. If someone sees that later, this is the bug.
-->

---

<!-- header: Mission 5 · Step 4 of 4 -->

# Step 4: Decide with a P controller

A **proportional controller**: the further off you are, the harder you correct.

| Rule | In code |
|---|---|
| pointing further off → turn harder | `angular.z = K_ANGULAR × error` |
| further away → drive faster, up to a top speed | `linear.x = min(K_LINEAR × distance, MAX_SPEED)` |
| still pointing way off → don't drive yet | turn first |

A P controller sets command = K × error. You'll find it all over the world.

<!--
About 3 minutes.
K is a gain: a number you choose. Bigger K reacts harder.
The min() caps the speed far away; near the beacon the distance gets small, so the rover slows down by itself.
"Turn first" stops the rover from driving off in a wide arc when the beacon is behind it.
-->

---

<!-- header: Mission 5 · Step 4 of 4 -->

# P controller with numbers

Gains from the code: `K_ANGULAR = 2.0`, `K_LINEAR = 1.0`, `MAX_SPEED = 0.7`

| Moment | error | distance | angular.z | linear.x |
|---|---|---|---|---|
| start (worked example) | 1.51 | 12.93 | 3.02 (the rover does 2.0) | 0 (turn first) |
| facing the beacon | 0.05 | 12.80 | 0.10 | 0.7 (capped) |
| almost there | 0.02 | 0.50 | 0.04 | 0.50 |

Rows 2 and 3 are example values. As the error shrinks, the command shrinks with it.

<!--
About 2 minutes.
The rows after the first are illustrations, not from a real run. The point is the pattern: big error, big command; small error, small command.
The rover's top speeds are 1.0 m/s and 2.0 rad/s; asking for more does nothing, so the 3.02 becomes a 2.0 rad/s turn.
"Turn first" in the code means: drive only when abs(error) < 0.5 rad, roughly 30°.
-->

---

<!-- header: Mission 5 · Step 4 of 4 -->

# Callbacks remember, a timer decides

The structure matters as much as the rule.

- `odom_callback` and `goals_callback` only **store** the latest message
- a timer runs `control_loop` 20 times per second and decides with whatever is latest

Why? `spin()` runs one callback at a time. Keep callbacks short and quick, so the next message and the next timer tick aren't held up.

<!--
About 2 minutes.
Odometry arrives 50 times per second. Doing all the work there would mean computing more often than needed, and any slow code would block everything else.
Hold back the details: the first "Check yourself" question at the end is about exactly this.
-->

---

<!-- header: Mission 5 · Step 4 of 4 -->

# go_to_goal.py (part 1 of 4): imports and constants

<style scoped>pre { font-size: 18px; }</style>

Change `go_to_goal.py` to:

```python
# my_rover/my_rover/go_to_goal.py
import math

import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from geometry_msgs.msg import PoseArray, Twist
from nav_msgs.msg import Odometry

MAX_SPEED = 0.7   # top speed (m/s); the rover can do 1.0
K_LINEAR = 1.0    # further away -> faster
K_ANGULAR = 2.0   # pointing further off -> turn harder
```

<!--
About 2 minutes.
New since the first version: import math, Twist and the three constants. yaw_from_quaternion from Step 2 follows on the next slide.
Constants at the top in capitals are where you'll tune for 3 stars later, so nobody has to dig through the code.
-->

---

<!-- header: Mission 5 · Step 4 of 4 -->

# go_to_goal.py (part 2 of 4): helper and `__init__`

<style scoped>pre { font-size: 16px; } li { font-size: 24px; }</style>

```python
def yaw_from_quaternion(q) -> float:
    """The rover only turns about z, so this is all of the quaternion we need."""
    return math.atan2(2.0 * (q.w * q.z + q.x * q.y), 1.0 - 2.0 * (q.y * q.y + q.z * q.z))


class GoToGoal(Node):
    def __init__(self):
        super().__init__('go_to_goal')
        self.pose = None   # latest (x, y, yaw), None = not received yet
        self.goals = []    # remaining beacons, the first one is the next target
        self.create_subscription(Odometry, '/rover1/odom', self.odom_callback, 10)
        self.create_subscription(PoseArray, '/mission/goals', self.goals_callback, 10)
        self.publisher = self.create_publisher(Twist, '/rover1/cmd_vel', 10)
        self.create_timer(0.05, self.control_loop)  # decide 20 times per second
```

- Two subscribers, one publisher, one timer: the system map in code
- `self.pose` and `self.goals` are the node's memory

<!--
About 2 minutes.
yaw_from_quaternion is the function from Step 2, unchanged. It sits outside the class.
Point back at the map: each line in __init__ is one arrow.
self.pose starts as None because the first odometry message hasn't arrived when __init__ runs. The control loop has to check for that.
0.05 s = 20 times per second.
-->

---

<!-- header: Mission 5 · Step 4 of 4 -->

# go_to_goal.py (part 3 of 4): callbacks

<style scoped>pre { font-size: 16px; }</style>

```python
    def odom_callback(self, msg: Odometry):
        p = msg.pose.pose
        self.pose = (p.position.x, p.position.y, yaw_from_quaternion(p.orientation))  # just remember it

    def goals_callback(self, msg: PoseArray):
        self.goals = [(p.position.x, p.position.y) for p in msg.poses]
```

- Each callback just stores and returns
- `self.pose` becomes a plain `(x, y, yaw)`: the quaternion is turned into yaw on the way in
- `goals` becomes a plain list of `(x, y)` pairs, next beacon first
- No logging any more: the rover moving is the output now

<!--
About 2 minutes.
If the list comprehension is new to someone: it builds a list of (x, y) by going through every pose in msg.poses.
When the last beacon is reached, msg.poses is empty, so self.goals becomes [] and the loop stops driving.
-->

---

<!-- header: Mission 5 · Step 4 of 4 -->

# go_to_goal.py (part 4 of 4): control loop

<style scoped>pre { font-size: 17px; }</style>

```python
    def control_loop(self):
        cmd = Twist()  # start from zero velocity
        if self.pose is not None and self.goals:
            x, y, yaw = self.pose
            goal_x, goal_y = self.goals[0]
            dx = goal_x - x
            dy = goal_y - y
            distance = math.hypot(dx, dy)
            # angle we should face minus angle we face = heading error (wrapped to -pi..pi)
            error = math.atan2(dy, dx) - yaw
            error = math.atan2(math.sin(error), math.cos(error))

            cmd.angular.z = K_ANGULAR * error
            if abs(error) < 0.5:  # only drive once we roughly face the beacon
                cmd.linear.x = min(K_LINEAR * distance, MAX_SPEED)
        self.publisher.publish(cmd)
```

<!--
About 3 minutes.
Read it top to bottom and match each line to the maths slides: dx, dy, distance, error, wrapping, then the two P rules.
It always publishes, even a zero Twist. With no pose or no goals, the rover gets told to stand still.
Common mistakes: forgetting the wrapping line (pirouettes), or putting linear.x outside the if (the rover drives off in wide arcs).
-->

---

<!-- header: Mission 5 · Step 4 of 4 -->

# Run it

```bash
ros2 run my_rover go_to_goal
```

**You should see:** the rover steers to each beacon by itself, slows down on the sand and carries on.

When the beacons run out, `self.goals` is empty, the node publishes a zero Twist and the rover parks.

The panel shows *Mission complete* and your stars.

`main()` stays the same. The full file is in `missions/05-waypoints.md`, Step 4.

<!--
About 5 minutes.
No rebuild needed: setup.py didn't change and --symlink-install picks up the new file. Just stop the old node with Ctrl+C and run again.
To retry for stars, relaunch the mission in terminal 1, then run the node again.
-->

---

<!-- header: Mission 5 · Hint -->

# Hint: want 3 stars?

These values take about 1.7 seconds per metre of route, which is 2 stars. Tune `MAX_SPEED`, `K_LINEAR` and `K_ANGULAR`:

- The rover's top speed is 1.0 m/s and 2.0 rad/s. Asking for more does nothing.
- `K_ANGULAR` too high and the rover wobbles (overshoot); too low and the turns are sluggish.
- The rover can't stop instantly (it brakes at 1 m/s²). `K_LINEAR` decides how early it slows down for a beacon.

Change one number at a time and time each run.

<!--
Show only after people have tried.
Your 3-star reference to demo, if you have the solutions package: ros2 run rover_solutions go_to_goal. Let people try tuning first.
For a fair race, relaunch with the same seed, for example mission:=5 seed:=42: the beacons and the sand will be in exactly the same places.
-->

---

<!-- header: Mission 5 · System map -->

# What happened behind the scenes

![w:1100](../images/missions/m05-1.png)

- **subscriber**: ROS calls `callback(msg)` for every message
- Callbacks store the data, a timer decides
- `nav_msgs/Odometry` gives the position and a quaternion; `yaw_from_quaternion` turns it into the one angle you need
- Measure, compute the error, send a command, measure again: a closed loop

<!--
About 2 minutes.
Same map as at the start, now with the code behind every box. Ask someone to point at the line of code for each arrow.
-->

---

<!-- header: Mission 5 · Check yourself -->

# Check yourself

1. What happens if you put `time.sleep(5)` inside `odom_callback`?

2. The rover crosses a sand patch at 60% speed. What does go_to_goal do about it? What would square.py from mission 4 do?

<!--
Let people discuss in pairs first.
1. spin() runs one callback at a time. While it sleeps for 5 s the timer doesn't run and no other message is read, so no cmd_vel goes out. After 1 s the rover stops (the 1-second rule), and it moves in jerks from then on. Never wait long inside a callback. That's why mission 4 used a timer instead of while + sleep.
2. go_to_goal does nothing special. It keeps reading the real position, so it keeps driving until the distance to the beacon is small, however long that takes. A closed loop corrects itself. square.py would drive for the planned number of seconds and stop short, then turn at the wrong spot. Every leg after that would miss too.
-->

---

<!-- _class: checklist -->
<!-- header: Mission 5 · Checklist -->

# Before you move on, can you...

<style scoped>li { font-size: 24px; }</style>

- write a subscriber whose callback only stores the data?
- explain why the decisions happen in a timer and not in the callback?
- get x, y and the yaw out of a `nav_msgs/Odometry` message?
- compute the distance and heading error to a point with `hypot` and `atan2`, wrapped into −π..π?
- write a P controller and say what each gain changes?
- explain why sand ruins an open-loop plan but not a closed loop?

<!--
The same list is in CHECKLIST.md for learners to tick off. Anyone unsure about atan2: give them a point on the board and have them compute dx, dy and the angle by hand.
-->

---

<!-- _class: roadmap -->
<!-- header: Where we are -->

# Next: Mission 6, Sample Hunter

| | # | Mission | You learn |
|---|---|---|---|
| ✓ | 0 | Landing | workspace, build, launch, teleop, remapping |
| ✓ | 1 | Telemetry | nodes, topics, messages |
| ✓ | 2 | Manual Drive | publishing `Twist`, speeds and angles |
| ✓ | 3 | Mission Control | services: request and response |
| ✓ | 4 | Survey Square | a package and a Python publisher |
| ✓ | 5 | Waypoints | subscribers, `Odometry`, closed-loop control |
| **▶** | **6** | **Sample Hunter** | **camera and laser, service clients in code** |
| | 7 | Rover Fleet | namespaces, parameters, launch files |
| | 8 | Boss: Power Crisis | all of the above, state machines, battery |

<!--
Extras for fast finishers (from the guide): watch the position change as you drive with ros2 topic echo /rover1/odom --field pose.pose.position, and race a friend with mission:=5 seed:=42 (the beacons and the sand will be in exactly the same places).
The next mission reuses this control loop to hunt for samples, so keep go_to_goal.py.
-->
