---
marp: true
title: "Mission 2: Manual Drive"
description: Step-by-step teaching slides for Mars Rover Academy mission 2
paginate: true
size: 16:9
footer: Mars Rover Academy · Mission 2
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

# Mission 2: Manual Drive

The keyboard link is down and teleop is off-limits. Send velocity commands by hand with `ros2 topic pub`, do the maths and reach all the beacons.

<style scoped>code { white-space: nowrap; }</style>

**You will learn:** `Twist` · `cmd_vel` · speeds and radians · top speed and the watchdog · `--once`, `--rate` and `--times`

<!--
Suggested time: 30 to 45 minutes. Have learners compute on paper before typing.
Goal of the session: everyone can drive a robot by publishing Twist messages and can predict where a command takes it, within the rover's limits.
-->

---

<!-- _class: roadmap -->
<!-- header: Where we are -->

# Part 1 roadmap

| | # | Mission | You learn |
|---|---|---|---|
| ✓ | 0 | Landing | workspace, build, launch, teleop, remapping |
| ✓ | 1 | Telemetry | nodes, topics, messages |
| **▶** | **2** | **Manual Drive** | **publishing `Twist`, speeds and angles** |
| | 3 | Mission Control | services: request and response |
| | 4 | Survey Square | a package and a Python publisher |
| | 5 | Waypoints | subscribers, `Odometry`, closed-loop control |
| | 6 | Sample Hunter | camera and laser, service clients in code |
| | 7 | Rover Fleet | namespaces, parameters, launch files |
| | 8 | Boss: Power Crisis | all of the above, state machines, battery |

<!--
About 1 minute. Last time we only listened and used the radio. Today we use the same ros2 topic pub to make the rover drive.
-->

---

<!-- header: Mission 2 · Goal -->

# Today's goal

![bg right:42% contain](../../docs/images/mars/mission-2.png)

**Objectives**
1. Reach the beacons in order 1 → 2 → 3
2. Drive one full circle around the crater

**Stars:** ≤ 4 min = ⭐⭐⭐ · ≤ 8 min = ⭐⭐ · using teleop = ⭐ only

No teleop this time: mission control will notice if you use it.

<!--
About 2 minutes. Point at the screenshot: the rover's tracks run from the lander through the three beacons and once around the crater.
Teleop still finishes the mission, but only for 1 star. How mission control notices is on the system map at the end.
-->

---

<!-- header: Mission 2 · Goal -->

# Launch the mission

```bash
# Terminal 1
ros2 launch mission_control mission.launch.py mission:=2
```

Leave this terminal running and send commands from a **new** one.

<!--
In missions 0 to 3 the clock starts at launch. If people care about stars, go through the concept slides first and let them launch when they have their route on paper.
Usual mistake: a teleop from earlier missions still running in another terminal. That alone costs the stars, even if nobody presses a key. Close it.
-->

---

<!-- header: Mission 2 · Concept -->

# Twist: how robots describe velocity

When you pressed keys in mission 0, teleop sent messages to `/rover1/cmd_vel`. Here's what it sent:

```bash
ros2 topic info /rover1/cmd_vel          # Type: geometry_msgs/msg/Twist
ros2 interface show geometry_msgs/msg/Twist
```

<!--
About 2 minutes. These are the two commands from mission 1: topic info gives the type, interface show gives its fields. Run them live; the output is on the next slide.
-->

---

<!-- header: Mission 2 · Concept -->

# What's inside a Twist?

```text
# This expresses velocity in free space broken into its linear and angular parts.

Vector3  linear
	float64 x
	float64 y
	float64 z
Vector3  angular
	float64 x
	float64 y
	float64 z
```

`Twist` works for any robot, 3-D drones included, but a rover on the ground only uses two fields.

<!--
About 2 minutes. Two vectors of three numbers: linear velocity along x, y, z and angular velocity around x, y, z. A drone needs all six. A rover can only drive forward or backward and turn, so it needs two.
-->

---

<!-- header: Mission 2 · Concept -->

# The two fields a rover uses

<style scoped>table { margin: 8px auto 28px; font-size: 24px; }</style>

| Field | Meaning | Unit | Positive | Negative |
|---|---|---|---|---|
| `linear.x` | forward speed | metres/second | forward | backward |
| `angular.z` | turning speed | radians/second | turn left ↺ | turn right ↻ |

A **radian** is the angle unit ROS uses everywhere. One full turn is 2π ≈ 6.2832 radians.

| degrees | 45° | 90° | 180° | 360° |
|---|---|---|---|---|
| radians | 0.7854 | 1.5708 | 3.1416 | 6.2832 |

<!--
About 3 minutes. Usual mistake: thinking positive angular.z turns right. Positive is counter-clockwise, to the left, like angles in maths class.
The conversion: radians = degrees × π / 180. The panel shows yaw in degrees to make it easier to read, but everything you send is in radians. Leave the table up while people plan their route.
-->

---

<!-- header: Mission 2 · Concept -->

# The rover's limits

rover1 is a real vehicle, not a cursor.

- **Top speed:** 1.0 m/s forward and 2.0 rad/s turning. Ask for more and it simply drives at its top speed.
- **No instant changes:** it speeds up and slows down gradually, the way a heavy vehicle does.

Speeding up and slowing down take the same time, so what the rover loses at the start it makes up while rolling to a stop. The distance still comes out as speed × the seconds you commanded.

<!--
About 2 minutes. The top speed is the new thing compared to a simple simulator: it changes the maths for anything longer than 1 m or bigger than about 115°.
If someone asks why the distance still works out: draw the speed over time as a trapezium on the board. The ramp at the start is a triangle missing, the ramp at the end is the same triangle added.
-->

---

<!-- header: Mission 2 · Concept -->

# The 1-second rule

The rover keeps following the last command for 1 more second, then stops by itself. Real robots have the same safety feature, called a **watchdog**: if the program sending commands crashes, the robot doesn't drive off forever.

So a single `--once` message gives exactly 1 second of commanded motion:

- `linear.x: 1.0` once moves 1 metre.
- `angular.z: 1.5708` once turns 90°.

<!--
About 2 minutes. This rule makes today's maths easy: within the top speed, the number you send is the distance or the angle.
Ask the room: what do you send to turn 45° right? (angular.z: -0.7854.) To drive 1 m backwards? (linear.x: -1.0.)
-->

---

<!-- header: Mission 2 · Concept -->

# More than 1 metre

Because of the top speed, you can't move 5 metres with one message. Send five, one per second:

<style scoped>pre { font-size: 18px; }</style>

```bash
ros2 topic pub --rate 1 --times 5 /rover1/cmd_vel geometry_msgs/msg/Twist "{linear: {x: 1.0}}"
```

`--rate 1` means one message per second and `--times 5` means stop after five. That's 5 seconds at 1 m/s, so 5 metres.

> Careful: the options (`--once`, `--rate`, `--times`) go right after `pub`, before the topic name. If one lands between the type and the data, you get `error: unrecognized arguments`.

<!--
About 2 minutes. Don't run it yet; step 2 uses exactly this.
Usual mistakes: --times at the end of the line (the error in the box), and sending linear.x 5.0 once and expecting 5 m. That's question 1 of "Check yourself".
-->

---

<!-- header: Mission 2 · Step 1 of 3 -->

# Step 1: Take it for a spin

<style scoped>pre { font-size: 19px; }</style>

```bash
ros2 topic pub --once /rover1/cmd_vel geometry_msgs/msg/Twist "{linear: {x: 1.0}}"
```

The rover moves 1 metre forward, and x in the panel grows by 1.00. Any field you leave out is 0.

<!--
About 2 minutes. Learners should see x go from 3.00 to 4.00 in the panel.
Usual mistakes: writing {x: 1.0} without the linear: around it, or a typo in geometry_msgs/msg/Twist. ROS prints an error for both.
-->

---

<!-- header: Mission 2 · Step 1 of 3 -->

# Now turn

<style scoped>pre { font-size: 19px; }</style>

```bash
ros2 topic pub --once /rover1/cmd_vel geometry_msgs/msg/Twist "{angular: {z: 1.5708}}"
```

That's 90° left (yaw = 90°). Send `-1.5708` to turn back.

> The rover is still rolling for a moment after the command ends. Wait until `v` and `w` in the panel are back to 0.00 before you send the next command, or the two moves blend together.

Press the up arrow to recall the last command and edit the number.

<!--
About 3 minutes. Show the up-arrow trick live; it saves a lot of typing today.
If tab completion is enabled, typing the command up to the type and pressing Tab twice gives an empty template.
The panel shows yaw in degrees, but the command takes radians.
-->

---

<!-- header: Mission 2 · Step 2 of 3 -->

# Step 2: Plan the route to the beacons

If you moved the rover in step 1, close and relaunch the mission first so it starts on the lander at (3, 3) facing right (0°).

| Beacon | Position |
|---|---|
| 1 | (8, 3) |
| 2 | (8, 8) |
| 3 | (4, 8) |

Sketch the route on paper and work out which commands to send, in order. Anywhere inside a beacon's circle counts.

<!--
About 5 minutes of planning. Have everyone compute on paper before typing. Drawing the grid with the lander and the three beacons on the board helps.
Relaunching resets the clock too, which is fine: stars are optional.
Usual mistakes: forgetting that the rover has to turn between beacons, turning the wrong way (left is positive), and sending a whole distance in one message.
-->

---

<!-- header: Mission 2 · Step 2 of 3 -->

# Hint for beacon 1

Beacon 1 is straight ahead, 8 − 3 = 5 m away, and the rover already faces right. Five messages at 1 m/s, one per second.

<!--
Show only after people have tried.
If they get beacon 1, ask: which way does the rover face now, and which way is beacon 2?
-->

---

<!-- header: Mission 2 · Step 2 of 3 -->

# Solution: full route

<style scoped>pre { font-size: 18px; padding: 20px 16px; }</style>

```bash
T="/rover1/cmd_vel geometry_msgs/msg/Twist"
ros2 topic pub --rate 1 --times 5 $T "{linear: {x: 1.0}}"   # to beacon 1 (8 - 3 = 5 m)
ros2 topic pub --once $T "{angular: {z: 1.5708}}"           # turn left 90° (now facing up)
ros2 topic pub --rate 1 --times 5 $T "{linear: {x: 1.0}}"   # to beacon 2 (8 - 3 = 5 m)
ros2 topic pub --once $T "{angular: {z: 1.5708}}"           # turn left another 90° (now facing left)
ros2 topic pub --rate 1 --times 4 $T "{linear: {x: 1.0}}"   # to beacon 3 (8 - 4 = 4 m)
```

`T` holds the topic and the type so you don't have to type them every time. Send the commands one at a time and wait for the rover to stop before the next.

<!--
Show only after people have tried.
T is a shell variable, so $T stands for its text. It only lives in that terminal.
Usual mistake: pasting all lines at once. Each new command replaces the previous one, so the rover skips moves. Wait for v and w to reach 0.00.
-->

---

<!-- header: Mission 2 · Step 3 of 3 -->

# Step 3: Drive a circle around the crater

If you drive and turn at the same time, the rover drives a circle:

**radius** = `linear.x / angular.z`

One `--once` lasts 1 second, which isn't a full circle. So keep sending with `--rate` and leave out `--times`:

<style scoped>pre { font-size: 17px; padding: 20px 16px; } p code { white-space: nowrap; }</style>

```bash
ros2 topic pub --rate 1 /rover1/cmd_vel geometry_msgs/msg/Twist "{linear: {x: 1.0}, angular: {z: 0.5}}"
```

That runs until you press `Ctrl+C`.

<!--
About 2 minutes. Ask first: with linear.x 1.0 and angular.z 0.5, how big is the circle? (Radius 1.0 / 0.5 = 2 m.)
Don't run it yet; the next slide says where to start and when to stop.
-->

---

<!-- header: Mission 2 · Step 3 of 3 -->

# When to stop

A full circle is 2π radians, so at 0.5 rad/s it takes about 12.6 seconds. Then press `Ctrl+C`.

The crater is at (4, 6), 2 m south of beacon 3. Before you start, check which way the rover is facing: if it turns left, which side of it will the circle be on?

> Keep going without stopping: if the rover stands still, the count starts over.

That completes the mission. The panel shows *Mission complete* and your stars.

<!--
About 3 minutes. Answer to the question: turning left, the circle is on the rover's left. At beacon 3 the rover faces left (west), so its left is south: the circle goes around the crater, 2 m away, exactly as needed.
Usual mistakes: running the circle somewhere else (it has to go around the crater), and pressing Ctrl+C early then starting again from a standstill, which resets the count.
-->

---

<!-- header: Mission 2 · System map -->

# What happened behind the scenes

![w:1100](../images/missions/m02-1.png)

- A topic can have several publishers. `mars_sim` obeys whatever arrives on `/rover1/cmd_vel` and can't tell who sent it.
- So mission_control doesn't read the messages to catch teleop. It asks the ROS graph who publishes there, which is exactly what `ros2 topic info -v` shows.

<!--
About 3 minutes. Green = a node that already exists, yellow = you, blue = a topic. The grey dashed box is teleop: fine in mission 0, forbidden here.
This is the -v option from mission 1's table, now with a purpose.
-->

---

<!-- header: Mission 2 · Summary -->

# Summary

Driving a mobile robot means publishing `geometry_msgs/msg/Twist` to `cmd_vel`. Real robots work exactly the same way.

- `linear.x` is forward speed in m/s, `angular.z` is turning left in rad/s
- Real vehicles have a top speed, can't change speed instantly, and stop on their own when the commands stop coming

<style scoped>table { margin-top: 12px; }</style>

| Option | Sends |
|---|---|
| `--once` | one message |
| `--rate N` | N per second until you stop it |
| `--times N` | N messages and exits |

<!--
About 2 minutes. Point out that all three options belong to ros2 topic pub and work for any topic, not just cmd_vel.
Your commands have to fit the rover's limits; from mission 4 on, your own code has to as well.
-->

---

<!-- header: Mission 2 · Check yourself -->

# Check yourself

1. You send `{linear: {x: 5.0}}` once. How far does the rover go?

2. How do you turn 180°?

3. How does mission control know you're using teleop?

<!--
Let people work out the answers on paper first, then try them.
1. 1 metre. The top speed is 1.0 m/s, so it drives at 1.0 m/s for the 1 second the command lasts. To go 5 m, send x: 1.0 five times with --rate 1 --times 5.
2. angular.z: 3.1416 once would need 3.14 rad/s, but the rover turns at most 2.0 rad/s, so you'd only get 2 radians (about 115°). Send 90° twice in a row instead: ros2 topic pub --rate 1 --times 2 /rover1/cmd_vel geometry_msgs/msg/Twist "{angular: {z: 1.5708}}"
3. Run ros2 topic info -v /rover1/cmd_vel while teleop is running and you'll see a publisher named teleop_twist_keyboard. mission_control asks ROS 2 the same question every 0.1 s. (ros2 topic pub shows up as _ros2cli_...)
-->

---

<!-- _class: checklist -->
<!-- header: Mission 2 · Checklist -->

# Before you move on, can you...

<style scoped>li { font-size: 25px !important; }</style>

- say what `linear.x` and `angular.z` in a `Twist` mean, with their units?
- convert an angle in degrees to radians?
- work out how far a command moves the rover, using the 1-second rule and the top speed?
- use `--once`, `--rate` and `--times`, and put them in the right place?
- drive a circle and predict its radius?
- explain how mission control can tell teleop from your commands?

<!--
The same list is in CHECKLIST.md for learners to tick off. If someone is unsure about the third item, give them a quick one: "linear.x 3.0 once, how far?" (1 m, the top speed.)
-->

---

<!-- _class: roadmap -->
<!-- header: Where we are -->

# Next: Mission 3, Mission Control

| | # | Mission | You learn |
|---|---|---|---|
| ✓ | 0 | Landing | workspace, build, launch, teleop, remapping |
| ✓ | 1 | Telemetry | nodes, topics, messages |
| ✓ | 2 | Manual Drive | publishing `Twist`, speeds and angles |
| **▶** | **3** | **Mission Control** | **services: request and response** |
| | 4 | Survey Square | a package and a Python publisher |
| | 5 | Waypoints | subscribers, `Odometry`, closed-loop control |
| | 6 | Sample Hunter | camera and laser, service clients in code |
| | 7 | Rover Fleet | namespaces, parameters, launch files |
| | 8 | Boss: Power Crisis | all of the above, state machines, battery |

<!--
Extras for fast finishers:
- Watch the rover speed up and slow down: run ros2 topic echo /rover1/odom --field twist.twist.linear.x in one terminal and send one --once command from another.
- Draw a figure 8: one circle left, then one circle right (negative angular.z).
- Back up with a negative linear.x. Can you drive a circle backwards?
-->
