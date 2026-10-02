# Mission 12 (boss): Heavy Lifting

Two heavy crates have to go to DROP-OFF, and they're too heavy for one arm. The turtle has to drive up, grip a crate with both grippers at once, drive it to the zone and set it down. Driving and manipulating at the same time is called **mobile manipulation**, and it's the final exam.

![Mission 12: the turtle carries a crate with both arms towards DROP-OFF](../docs/images/mission-12.png)

**Objectives**
- [ ] Deliver 2 crates (set down inside DROP-OFF)
- [ ] Drive the turtle with your own node (no teleporting)

**Stars:** ≤ 25 s = ⭐⭐⭐ · ≤ 60 s = ⭐⭐ · the clock starts when the turtle or an arm starts moving

```bash
# Terminal 1
ros2 launch turtle_quest mission.launch.py mission:=12
```

---

## Crate rules

| Rule | Detail |
|---|---|
| size | 0.8 × 0.8 m |
| gripping | a gripper "touches" the crate when its tip is within 0.65 m of the crate's centre; closing it then succeeds |
| too heavy | held by one gripper the crate doesn't move (the service tells you: *too heavy for one arm*) |
| lifted | held by both grippers of the same turtle, the crate sits exactly halfway between the two tips and moves with them |
| slipping | if the two tips get more than 1.5 m apart, the crate slips and both grippers open |
| delivered | crate centre inside DROP-OFF (centre (9.38, 9.38), radius 1.2) and no gripper holding it |

## What you have to work with

| Name | Kind | Type | Used for |
|---|---|---|---|
| `/mission/items` | topic (in) | `geometry_msgs/msg/PoseArray` | world positions of the crates not delivered yet |
| `/turtle1/pose` | topic (in) | `turtlesim/msg/Pose` | the turtle |
| `/turtle1/left_arm/tip`, `/turtle1/right_arm/tip` | topic (in) | `geometry_msgs/msg/Point` | where the grippers are; a lifted crate sits at their midpoint |
| `/turtle1/cmd_vel` | topic (out) | `geometry_msgs/msg/Twist` | drive |
| `/turtle1/joint_command` | topic (out) | `sensor_msgs/msg/JointState` | arm posture |
| `/turtle1/left_gripper`, `/turtle1/right_gripper` | service | `std_srvs/srv/SetBool` | grip / let go |

### System map

```mermaid
flowchart LR
    classDef ros fill:#c8e6c9,stroke:#2e7d32,color:#1b1b1b
    classDef mine fill:#fff59d,stroke:#f57f17,stroke-width:3px,color:#1b1b1b
    classDef topic fill:#bbdefb,stroke:#1565c0,color:#1b1b1b
    classDef srv fill:#ffe0b2,stroke:#e65100,color:#1b1b1b
    classDef act fill:#e1bee7,stroke:#6a1b9a,color:#1b1b1b
    classDef param fill:#eeeeee,stroke:#616161,color:#1b1b1b
    classDef off fill:#f5f5f5,stroke:#9e9e9e,stroke-dasharray:4 3,color:#757575
    QM(["quest_master"]):::ros --> ITEMS["/mission/items<br/>PoseArray: crates"]:::topic
    SIM(["turtlesim_plus"]):::ros --> POSE["/turtle1/pose"]:::topic
    SIM --> TIPS["/turtle1/left_arm/tip<br/>/turtle1/right_arm/tip"]:::topic
    subgraph ME["crate_mover (your node)"]
        SM["state machine<br/>approach → grip → carry → backoff"]
        DRIVE["driving<br/>(mission 5)"]
        FORK["forklift posture<br/>(IK, mission 10)"]
        GRIPS["grippers<br/>(mission 11)"]
        SM --> DRIVE & FORK & GRIPS
    end
    ITEMS & POSE & TIPS --> SM
    DRIVE --> CMD["/turtle1/cmd_vel"]:::topic --> SIM
    FORK --> JC["/turtle1/joint_command"]:::topic --> SIM
    GRIPS -. call .-> GR{{"/turtle1/left_gripper<br/>/turtle1/right_gripper"}}:::srv -.- SIM
    style ME fill:#fffde7,stroke:#f57f17,stroke-width:3px,color:#1b1b1b
```

> 🟩 existing node · 🟨 you · 🟦 topic · 🟧 service · 🟪 action · ⬜ parameter — [how to read the maps](../ARCHITECTURE.md#how-to-read-the-maps)

It's one node with two control loops (driving and arms) and a state machine on top, built almost entirely from parts you wrote in missions 5, 10 and 11.

## The plan

One trick makes this much simpler: keep the arms in one fixed "forklift" posture the whole time, with both grippers 1.0 m in front of the turtle and 0.35 m left and right of the middle. Your IK from mission 10 gives you the angles. Getting the grippers around a crate then just means parking the turtle 1.0 m from it, facing it. You've solved that driving problem before.

```mermaid
stateDiagram-v2
    [*] --> approach
    approach --> grip: 1.0 m from the nearest crate, facing it -> close both grippers
    grip --> carry: both succeeded
    grip --> approach: a gripper missed -> open both
    carry --> backoff: crate (midpoint of the tips) inside DROP-OFF -> open both
    backoff --> approach: reversed for 1 s
```

## Step 1: The skeleton

Create `src/my_turtle/my_turtle/crate_mover.py` and fill in the TODOs:

```python
# my_turtle/my_turtle/crate_mover.py  (skeleton: fill in the TODOs)
import math

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Point, PoseArray, Twist
from sensor_msgs.msg import JointState
from std_srvs.srv import SetBool
from turtlesim.msg import Pose

from my_turtle.arm_reach import inverse_kinematics

DROPOFF = (9.38, 9.38)
REACH = 1.0        # crate centre this far in front of the turtle when gripping
GRIP_Y = 0.35      # grippers this far left/right of the crate centre


class CrateMover(Node):
    def __init__(self):
        super().__init__('crate_mover')
        self.pose = None
        self.crates = []   # from /mission/items
        self.tips = {}     # 'left'/'right' -> (x, y)
        # TODO 1: subscribe to /turtle1/pose, /mission/items and both /turtle1/<side>_arm/tip topics
        # TODO 2: publishers self.cmd_pub (/turtle1/cmd_vel) and self.joint_pub (/turtle1/joint_command)
        # TODO 3: SetBool clients for both grippers
        self.futures = []  # pending gripper requests
        self.state = 'approach'
        self.backoff_until = 0.0
        self.create_timer(0.05, self.loop)

    def now(self) -> float:
        return self.get_clock().now().nanoseconds / 1e9

    def hold_arms_out(self):
        # TODO 4: publish the forklift posture: IK for (REACH, +GRIP_Y) left and (REACH, -GRIP_Y) right
        pass

    def grippers_set(self, close: bool):
        # TODO 5: call both gripper services, keep both futures in self.futures
        pass

    def loop(self):
        if self.pose is None:
            return
        cmd = Twist()
        if self.state == 'approach':
            self.hold_arms_out()
            # TODO 6: drive to REACH metres from the nearest crate, facing it;
            #         when close enough and well aligned: stop, grippers_set(True), state = 'grip'
        elif self.state == 'grip':
            pass  # TODO 7: once both futures are done: both succeeded -> 'carry', else open both -> 'approach'
        elif self.state == 'carry':
            pass  # TODO 8: crate = midpoint of the tips; in DROP-OFF -> open both, 'backoff'; else drive to DROP-OFF
        elif self.state == 'backoff':
            pass  # TODO 9: reverse until backoff_until, then 'approach'
        self.cmd_pub.publish(cmd)


def main():
    rclpy.init()
    node = CrateMover()
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

Add `'crate_mover = my_turtle.crate_mover:main',` to `setup.py`, build, source, and run `ros2 run my_turtle crate_mover`.

Build it in stages. Do TODOs 1-4 first and check that the arms take the forklift posture. Then add 6 and watch the turtle park in front of a crate. Then 5 and 7, and finally 8 and 9.

## Hints (open only when stuck)

<details>
<summary>Hint for TODO 4: the forklift posture</summary>

```python
cmd = JointState()
cmd.name = ['left_shoulder', 'left_elbow', 'right_shoulder', 'right_elbow']
cmd.position = [*inverse_kinematics(REACH, GRIP_Y, 'left'), *inverse_kinematics(REACH, -GRIP_Y, 'right')]
self.joint_pub.publish(cmd)
```

</details>

<details>
<summary>Hint for TODO 6: parking in front of the crate</summary>

It's mission 5's controller, but aim for a distance of `REACH` instead of 0, and allow a little reversing if the turtle gets too close:

```python
x, y = min(self.crates, key=lambda c: math.hypot(c[0] - self.pose.x, c[1] - self.pose.y))
distance = math.hypot(x - self.pose.x, y - self.pose.y)
error = <heading error to (x, y), wrapped>
cmd.angular.z = 4.0 * error
if abs(error) < 0.3:
    cmd.linear.x = max(-0.5, min(2.0, 1.5 * (distance - REACH)))
if abs(distance - REACH) < 0.06 and abs(error) < 0.05:
    ...  # stop and grip
```

</details>

<details>
<summary>Hint for TODOs 7-9: grip, carry, back off</summary>

- grip: `all(f.done() for f in self.futures)` then `all(f.result().success for f in self.futures)`
- carry: the crate is at the midpoint of `self.tips['left']` and `self.tips['right']`. Drive towards `DROPOFF` (the crate travels 1 m ahead of the turtle, so it gets there first) and release when the crate is within about 0.4 m of the zone centre.
- backoff: `cmd.linear.x = -1.0` until `self.now() >= self.backoff_until`

</details>

> Note: there's no full solution file to unlock here, on purpose. The hints above cover every TODO. If you're still stuck, ask your instructor to demo the reference solution, then write your own version.

That's the final boss and the end of Turtle Quest. Check your total:

```bash
ros2 run turtle_quest progress   # out of 39 stars, how many did you get?
```

---

## Design challenge: split it up

`crate_mover` does everything in one node. Real robot software would split it into a behaviour node (just the state machine) on top of reusable skill nodes. Pattern 4 in [ARCHITECTURE.md](../ARCHITECTURE.md#pattern-4-split-big-jobs-into-small-nodes) describes the design. Try it:

1. Write `base_controller`. It subscribes to `/turtle1/pose` and `/turtle1/base_goal` (`geometry_msgs/msg/Point`) and publishes `/turtle1/cmd_vel`. It's your mission 5 controller with a different input.
2. Test it on its own: `ros2 topic pub --once /turtle1/base_goal geometry_msgs/msg/Point "{x: 2.0, y: 2.0}"`
3. Do the same for `arm_controller`: a world point in, IK, `joint_command` out.
4. Shrink `crate_mover` to a pure state machine that publishes goals and calls the grippers, and start all three nodes with one launch file.

Afterwards, was it easier or harder to change things? That trade-off is what software architecture is about.

---

## What you learned in Part 2

| Skill | Missions |
|---|---|
| joint-space control with `sensor_msgs/JointState` | 9 |
| grippers as `std_srvs/SetBool` services | 9, 11, 12 |
| coordinate frames (world → robot → shoulder) | 10, 12 |
| forward and inverse kinematics of a 2-link arm | 9, 10 |
| manipulation state machines that wait for real events | 11 |
| reusing your own Python modules across nodes | 11, 12 |
| mobile manipulation: driving + two-arm coordination | 12 |

## Where next?

- tf2: ROS 2's system for coordinate frames, which you did by hand with `to_turtle_frame`. See the [tf2 tutorials](https://docs.ros.org/en/humble/Tutorials/Intermediate/Tf2/Tf2-Main.html).
- URDF and RViz: describe a real robot's links and joints, and watch `joint_states` move a 3-D model.
- MoveIt 2: IK, motion planning and collision avoidance for real arms.
- ros2_control: how `joint_command`-style interfaces talk to real motors.
- Nav2: the full-size version of missions 5, 6 and 8. It uses `cmd_vel` too.
- C++ nodes: the same concepts in another language. Start with [Writing a simple publisher and subscriber (C++)](https://docs.ros.org/en/humble/Tutorials/Beginner-Client-Libraries/Writing-A-Simple-Cpp-Publisher-And-Subscriber.html).
- Racing your friends: launch with the same `seed:=<number>` and compare times, or design a mission of your own (see [TEACHER.md](../TEACHER.md#writing-a-new-mission)).

---

**Previous:** [Mission 11](11-pick-place.md) · **Home:** [README](../README.md)
