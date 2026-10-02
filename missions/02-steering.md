# Mission 2: Steering Wheel

The keyboard is broken, and teleop is off-limits this time (the quest master will notice if you use it). All you have left is sending velocity commands by hand with `ros2 topic pub`, so do the maths and touch all the flags.

![Mission 2: the turtle reached flag 1 and turned towards flag 2](../docs/images/mission-2.png)

**Objectives**
- [ ] Touch the flags in order 1 → 2 → 3
- [ ] Drive one full circle

**Stars:** ≤ 4 min = ⭐⭐⭐ · ≤ 8 min = ⭐⭐ · using teleop = ⭐ only

```bash
# Terminal 1
ros2 launch turtle_quest mission.launch.py mission:=2
```

---

## Twist: how robots describe velocity

When you pressed the arrow keys in mission 0, teleop sent messages to `/turtle1/cmd_vel`. Here's what it sent:

```bash
ros2 topic info /turtle1/cmd_vel          # Type: geometry_msgs/msg/Twist
ros2 interface show geometry_msgs/msg/Twist
```

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

`Twist` works for any robot, 3-D drones included, but a turtle on the ground only uses two fields:

| Field | Meaning | Unit | Positive | Negative |
|---|---|---|---|---|
| `linear.x` | forward speed | metres/second | forward | backward |
| `angular.z` | turning speed | radians/second | turn left ↺ | turn right ↻ |

A **radian** is the angle unit ROS uses everywhere. One full turn is 2π ≈ 6.2832 radians.

| degrees | 45° | 90° | 180° | 360° |
|---|---|---|---|---|
| radians | 0.7854 | 1.5708 | 3.1416 | 6.2832 |

### The 1-second rule

The turtle keeps following the last command for 1 more second, then stops by itself. The original turtlesim does the same, so a crashed controller can't leave the robot running off forever.

That means a single `--once` message gives exactly 1 second of motion. Distance is speed × 1 s, so to move 3 metres you send `linear.x: 3.0`. The angle turned is turning speed × 1 s, so to turn 90° you send `angular.z: 1.5708`.

---

## Step 1: Take it for a spin

```bash
ros2 topic pub --once /turtle1/cmd_vel geometry_msgs/msg/Twist "{linear: {x: 1.0}}"
```

The turtle moves 1 metre forward, and x in the panel grows by about 1.00. Any field you leave out is 0.

Now turn:

```bash
ros2 topic pub --once /turtle1/cmd_vel geometry_msgs/msg/Twist "{angular: {z: 1.5708}}"
```

That's 90° left (th = 90°). Send `-1.5708` to turn back.

To save typing, press the up arrow to recall the last command and edit the number. If tab completion is enabled in your terminal, you can also type `ros2 topic pub --once /turtle1/cmd_vel geometry_msgs/msg/Twist ` and press `Tab` twice to get an empty template.

## Step 2: Plan the route to the flags

If you moved the turtle in step 1, close and relaunch the mission first so it starts at (5.44, 5.44) facing right (0°).

| Flag | Position |
|---|---|
| 1 | (8.5, 5.44) |
| 2 | (8.5, 8.5) |
| 3 | (2.5, 8.5) |

Sketch the route on paper and work out which commands to send, in order. Anywhere inside a flag's circle counts.

<details>
<summary>Hint for flag 1</summary>

Flag 1 is straight ahead, 8.5 − 5.44 = 3.06 m away, and the turtle already faces right. Just go forward.

</details>

<details>
<summary>Full route</summary>

```bash
P="ros2 topic pub --once /turtle1/cmd_vel geometry_msgs/msg/Twist"
$P "{linear: {x: 3.06}}"        # to flag 1
$P "{angular: {z: 1.5708}}"     # turn left 90° (now facing up)
$P "{linear: {x: 3.06}}"        # to flag 2 (8.5 - 5.44 = 3.06)
$P "{angular: {z: 1.5708}}"     # turn left another 90° (now facing left)
$P "{linear: {x: 6.0}}"         # to flag 3 (8.5 - 2.5 = 6.0)
```

Send them one at a time and wait for the turtle to stop before the next.

</details>

## Step 3: Drive a circle

If you drive and turn at the same time, the turtle drives a circle with radius `linear.x / angular.z`.

The 1-second rule gets in the way here: one `--once` lasts 1 second, which isn't a full circle. So keep sending with `--rate`:

```bash
ros2 topic pub --rate 1 /turtle1/cmd_vel geometry_msgs/msg/Twist "{linear: {x: 2.0}, angular: {z: 1.0}}"
```

`--rate 1` sends the message once per second until you press `Ctrl+C`.

A full circle is 2π radians, so at 1 rad/s it takes about 6.3 seconds. Then press `Ctrl+C`.

> Careful: a circle with a 2 m radius needs room. If the turtle hits the edge of the world it slides along it instead of circling. Check which way the turtle is facing first: if it turns left, which side of it will the circle be on?

That completes the mission. The panel shows *Mission complete* and your stars.

---

## System map

```mermaid
flowchart LR
    classDef ros fill:#c8e6c9,stroke:#2e7d32,color:#1b1b1b
    classDef mine fill:#fff59d,stroke:#f57f17,stroke-width:3px,color:#1b1b1b
    classDef topic fill:#bbdefb,stroke:#1565c0,color:#1b1b1b
    classDef srv fill:#ffe0b2,stroke:#e65100,color:#1b1b1b
    classDef act fill:#e1bee7,stroke:#6a1b9a,color:#1b1b1b
    classDef param fill:#eeeeee,stroke:#616161,color:#1b1b1b
    classDef off fill:#f5f5f5,stroke:#9e9e9e,stroke-dasharray:4 3,color:#757575
    PUB(["ros2 topic pub<br/>(you)"]):::mine --> CMD["/turtle1/cmd_vel<br/>Twist"]:::topic
    TEL(["teleop_turtle<br/>(not allowed this time)"]):::off -.-x CMD
    CMD --> SIM(["turtlesim_plus"]):::ros --> POSE["/turtle1/pose<br/>Pose"]:::topic --> QM(["quest_master"]):::ros
    QM ---|"checks WHO<br/>publishes here"| CMD
```

> 🟩 existing node · 🟨 you · 🟦 topic · 🟧 service · 🟪 action · ⬜ parameter — [how to read the maps](../ARCHITECTURE.md#how-to-read-the-maps)

A topic can have several publishers. `turtlesim_plus` obeys whatever arrives on `/turtle1/cmd_vel` and can't tell who sent it. So quest_master doesn't read the messages to catch teleop. It asks the ROS graph who publishes there, which is exactly what `ros2 topic info -v` shows.

The grey dashed box is teleop: fine in mission 0, forbidden here.

## Summary

Driving a mobile robot means publishing `geometry_msgs/msg/Twist` to `cmd_vel`. Real robots like TurtleBot work exactly the same way. `linear.x` is forward speed in m/s and `angular.z` is turning left in rad/s.

`--once` sends one message, `--rate N` sends N per second until you stop it, and `--times N` sends N messages and exits.

## Check yourself

<details>
<summary>1. You send <code>{linear: {x: 2.0}, angular: {z: 3.1416}}</code> once. Where does the turtle end up?</summary>

It drives half a circle (π = 180° in 1 s) with radius 2/3.1416 ≈ 0.64 m.
It ends up 2 × 0.64 ≈ 1.27 m to the turtle's left, facing the opposite way.

</details>

<details>
<summary>2. How does the quest master know you're using teleop?</summary>

Run `ros2 topic info -v /turtle1/cmd_vel` while teleop is running and you'll see a publisher named `teleop_turtle`.
quest_master asks ROS 2 the same question every 0.1 s. (`ros2 topic pub` shows up as `_ros2cli_...`.)

</details>

## Extras

- Draw a figure 8: one circle left, then one circle right (negative `angular.z`).
- Change the pen colour before drawing. The next mission shows how.

---

**Previous:** [Mission 1](01-spy.md) · **Next:** [Mission 3: Service Hotline](03-hotline.md)
