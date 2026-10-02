# turtlesim_plus (Turtle Quest fork)

A ROS 2 (Humble) reimplementation of `turtlesim` in `pygame`, extended with **interactive
food and delivery mechanics**: turtles scan for nearby entities with a cone-shaped sensor,
eat spawned pizzas, and carry parcels to a drop-off zone. In this fork turtles can also grow
**two arms with grippers** to pick up objects and carry heavy crates. Multiple turtles are supported
natively — each is a self-contained composition of ROS 2 plugins
(command/scanner/eat/delivery).

Originally written by **Pi Thanacha Choopojcharoen** —
[tchoopojcharoen/turtlesim_plus](https://github.com/tchoopojcharoen/turtlesim_plus)
(forked from commit `8c7996a`). This copy is adapted as the simulator for the
[Turtle Quest](../../README.md) beginner course; the behaviour-tree companion package
(`turtlesim_plus_bt`) is not included.

![The turtlesim_plus window: a dual-arm turtle carries a crate, with the info panel on the right](../../docs/images/mission-12.png)

## Changes in this fork

Teaching additions:

- **Dual-arm turtles** (`arms` parameter): each turtle gets a left and a right planar 2-link arm
  (shoulder + elbow) with a gripper — see [Arms](#arms) below. Plus **crates**: heavy objects that only
  move when both grippers of one turtle hold them.
- **`/judge/objects`** (`turtlesim_plus_interfaces/msg/WorldObjectArray`) — every pizza, parcel and crate
  with its position and holder, for referees such as Turtle Quest's `quest_master`.

- **`/[name]/say`** (`std_msgs/msg/String`) — shows a speech bubble above the turtle for 5 s.
- **Info panel** to the right of the world (window is now 780×500): live x / y / θ, pizza and
  parcel counts of every turtle, plus any text published on **`/hud`** (`std_msgs/msg/String`,
  with a tiny line-prefix markup: `# ` title, `[x] ` / `[ ] ` checklist, `! ` warning,
  `* ` highlight, `$ N` star rating).
- **Goal flags** drawn from **`/mission/goals`** (`geometry_msgs/msg/PoseArray`; `position.z`
  is the flag radius, the first pose is highlighted as "next").
- **Coordinate grid** with axis labels (`show_grid` parameter) and a **name label** under each turtle.
- **`/clear_objects`** (`std_srvs/srv/Empty`) — removes every pizza and parcel.
- The **drop-off zone is visible** (labelled circle), and a carried parcel is drawn on the turtle's back.
- Fonts that also cover Thai are preferred when installed (Waree / Loma / Garuda …), so `say` works in Thai too.

Behaviour changes:

- **`cmd_vel` timeout** (`cmd_vel_timeout`, default 1.0 s, 0 = off): like stock turtlesim, a
  turtle stops when no new command arrived for that long.
- **Real-time physics**: each step integrates the actual elapsed time (capped at 0.1 s) instead of
  a fixed `time_step`, so motion stays in real time even when ticks are late under CPU load.
  `time_step` is now the nominal tick period.
- **`/[name]/scan` is published every tick**, with an empty list when nothing is in the cone
  (upstream only published on detections).
- **`/[name]/pose`** reports the commanded `linear_velocity` / `angular_velocity` (upstream: always 0).
- Sensor cones are drawn underneath pizzas/parcels so they never hide them; the pickup cone is an outline.
- Rendering is capped at 60 fps with cached grid/text surfaces.
- Fixes: removing a turtle now also destroys its `detect_pizza` action server (re-spawning the same
  name used to fail); node scripts are executable so `colcon build --symlink-install` works.

## Nodes / Scripts

- **`turtlesim_plus_node.py`** — the simulator itself. Owns the `pygame` window and every
  ROS 2 service/topic/action described below; spawns `turtle1` automatically on startup.
- **`pizza_on_click.py`** — subscribes to `/mouse_position` (published by the simulator on
  every left-click in the world area) and calls `/spawn_pizza` at that world position.

## Build & launch

```bash
sudo apt install python3-pygame python3-numpy fonts-tlwg-waree
colcon build --symlink-install --packages-select turtlesim_plus turtlesim_plus_interfaces
source install/setup.bash
ros2 launch turtlesim_plus turtlesim_plus.launch.py      # simulator + pizza_on_click
```

Every node parameter below is also a launch argument, e.g.
`ros2 launch turtlesim_plus turtlesim_plus.launch.py scanner_radius:=6.0 show_grid:=false`.

## Parameters

Read once at startup; they apply to every turtle spawned afterwards.

| Parameter | Default | Meaning |
|---|---|---|
| `time_step` | `0.01` | Nominal simulator tick period (s) |
| `scanner_radius` | `4.0` | `/scan` sensor radius (world units) |
| `scanner_angle_range` | `π/3` (60°) | `/scan` sensor cone, centred on the heading |
| `eat_radius` | `2.0` | `/eat` detection radius |
| `eat_angle_range` | `π/3` (60°) | `/eat` detection cone |
| `pickup_radius` | `2.0` | `/pickup` detection radius |
| `pickup_angle_range` | `π/3` (60°) | `/pickup` detection cone |
| `show_grid` | `true` | Draw the coordinate grid |
| `cmd_vel_timeout` | `1.0` | Stop a turtle after this many seconds without `cmd_vel` (0 = never) |
| `arms` | `false` | Give every turtle two arms with grippers |
| `arm_joint_speed` | `2.0` | Maximum joint speed (rad/s) |

## Services / Topics

**Global**

| Name | Type | Notes |
|---|---|---|
| `/spawn_turtle` | `turtlesim/srv/Spawn` | `x`/`y`/`theta` of `NaN` → centre `(5.44, 5.44, 0)`. A name collision appends `_1`, `_2`, … and returns the actual name |
| `/remove_turtle` | `turtlesim/srv/Kill` | By name |
| `/spawn_pizza` / `/spawn_parcel` | `turtlesim_plus_interfaces/srv/GivePosition` | `x`/`y` of `NaN` → uniform-random position |
| `/clear` | `std_srvs/srv/Empty` | Erases every turtle's pen trail |
| `/spawn_crate` | `turtlesim_plus_interfaces/srv/GivePosition` | A heavy crate (needs two grippers); `NaN` → random |
| `/clear_objects` | `std_srvs/srv/Empty` | Removes every pizza, parcel and crate |
| `/judge/objects` | `turtlesim_plus_interfaces/msg/WorldObjectArray` (pub, 10 Hz) | All objects: `name`, `type`, `x`, `y`, `held_by` |
| `/hud` | `std_msgs/msg/String` (sub) | Text for the info panel (markup above) |
| `/mission/goals` | `geometry_msgs/msg/PoseArray` (sub) | Goal flags to draw; `position.z` = radius (0 → 0.5) |
| `/mouse_position` | `geometry_msgs/msg/Point` (pub) | World coordinate of the last left-click |

**Per turtle** (`/[name]/...`)

| Name | Type | Direction | Notes |
|---|---|---|---|
| `cmd_vel` | `geometry_msgs/msg/Twist` | sub | `linear.x` forward speed, `angular.z` turn rate; times out after `cmd_vel_timeout` |
| `say` | `std_msgs/msg/String` | sub | Speech bubble for 5 s |
| `pose` | `turtlesim/msg/Pose` | pub | Every tick; velocities are the current command |
| `scan` | `turtlesim_plus_interfaces/msg/ScannerDataArray` | pub | Every tick; `type` is `Pizza`/`Parcel`/`Turtle`, `angle` relative to heading (+ left), `distance` |
| `pizza_count` / `parcel_count` | `std_msgs/msg/Int64` | pub | Every tick |
| `carrying_parcel` | `std_msgs/msg/Bool` | pub | Whether a parcel is currently held |
| `eat` / `stop` / `pickup` / `dropoff` | `std_srvs/srv/Empty` | service | No-op if nothing is in range; `dropoff` also requires being inside the drop-off zone (centre `(9.38, 9.38)`, radius 1.2) |
| `set_pen` | `turtlesim/srv/SetPen` | service | Pen is on by default (white, width 3). On the CLI quote the key: `'off': 1` — bare `off` is YAML for `false` |
| `teleport_absolute` / `teleport_relative` | `turtlesim/srv/TeleportAbsolute` / `TeleportRelative` | service | Starts a new pen stroke rather than drawing across the jump |
| `detect_pizza` | `turtlesim_plus_interfaces/action/GetData` | action | One-shot: succeeds with the current scan's pizzas, aborts if the scan is empty |

## Arms

Enabled with `arms:=true`. Geometry in the turtle frame (x forward, y left): shoulders at (0, ±0.3),
upper arm 0.8, forearm 0.7; `q1` (shoulder) is measured from the heading, `q2` (elbow) relative to the
upper arm; limits ±π and ±2.7 rad. Joints are position-controlled at up to `arm_joint_speed`.

| Name (`/[name]/...`) | Type | Direction | Notes |
|---|---|---|---|
| `joint_command` | `sensor_msgs/msg/JointState` | sub | Target positions by name (`left_shoulder`, `left_elbow`, `right_shoulder`, `right_elbow`); unnamed joints keep their target |
| `joint_states` | `sensor_msgs/msg/JointState` | pub | Every tick: positions and velocities |
| `left_arm/tip`, `right_arm/tip` | `geometry_msgs/msg/Point` | pub | Gripper position in world coordinates |
| `left_gripper`, `right_gripper` | `std_srvs/srv/SetBool` | service | `true` grabs the nearest free pizza/parcel within 0.4 m (crate: within 0.65 m of its centre), `false` releases; `message` explains the outcome |
| `left_gripper/holding`, `right_gripper/holding` | `std_msgs/msg/String` | pub | `''`, `Pizza`, `Parcel` or `Crate` |

Held pizzas/parcels follow the gripper tip. A crate held by one gripper stays put; held by both grippers of
the same turtle it sits at the midpoint of the tips, and it slips (both grippers open) if the tips are more
than 1.5 apart. Crates are also visible to the scanner (`type: Crate`).

## Architecture

```text
Simulator (entity.py)
├── Engine     -- steps every PhysicsEntity with the real elapsed dt
├── GUI        -- pygame window; background renderers (grid, sensor cones) ->
│                 entities in registered order -> overlay renderers (flags, panel)
└── entity_list

TurtlePlugin (ros2_plugins.py)  -- one per spawned turtle, composes:
├── TurtleCommandROS2Plugin   -- cmd_vel (+timeout), say, pose, stop/set_pen/teleport_*
├── TurtleScannerROS2Plugin   -- scan topic + detect_pizza action
├── TurtleEatROS2Plugin       -- eat service, pizza_count
├── TurtleDeliveryROS2Plugin  -- pickup/dropoff services, parcel_count, carrying_parcel
└── TurtleArmsROS2Plugin      -- (arms:=true) joint_command/joint_states, grippers, tips

arms.py   -- arm kinematics, grasping rules, Crate entity (no ROS in here)

ui.py     -- fonts, grid, speech bubbles, goal flags, info panel
world.py  -- world <-> screen mapping (WORLD_SIZE = 10.88, SCREEN_SIZE = 500, PANEL_WIDTH = 280)
```

Kinematics use an exact matrix-exponential integration of constant `(v, ω)` over each step, so
straight lines and arcs are exact for any step length.

## Known limitations

- No inter-entity collision; turtles and objects may overlap.
- Pen trails have no size cap — call `/clear` in long sessions.
- No automated test suite; behaviour is verified by driving the simulator through its ROS interface
  (the Turtle Quest missions and reference solutions exercise most of it).

## License

GPL-3.0-only — see [`LICENSE`](LICENSE).
