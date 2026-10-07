# Instructor guide

For anyone running Mars Rover Academy in a classroom or a workshop.

## The idea behind the course

Learners do first and get the theory second. Every mission starts with a concrete goal, and the concept sections show up when they're needed. `mission_control` ticks objectives the moment they're met, so nobody has to ask "is this right?" They also build on their own code. Mission 5's controller comes back in 6, 7, 8, 11 and 12, mission 10's inverse kinematics in 11 and 12, and learners feel why readable code matters.

The simulator uses the message types of real robots (`Odometry`, `LaserScan`, `BatteryState`, `JointState`, tf2, an action server), so what learners write here carries over to a real rover with little change. Mission 5 is where that first shows: the pose comes as a quaternion, not an angle.

Every mission has a system map; [ARCHITECTURE.md](ARCHITECTURE.md) connects them, and [CONCEPTS.md](CONCEPTS.md) maps every part of ROS 2 to the missions (handy for checking what a session covers, and for pointing fast learners at the next step). The best habit you can build is drawing the map on the board before coding: what goes in, what comes out?

Stars are optional. Finishing always earns at least 1 star; stars 2-3 are for those who want to tune and strategise.

## Suggested schedule

[slides/mars-rover-course.md](slides/mars-rover-course.md) teaches the whole course from one deck: for every mission an overview, a picture of the system, how to run it and a checklist. To open the first session, [slides/ros2-in-one-hour.md](slides/ros2-in-one-hour.md) is a one-hour introduction with live demos. For missions 0 to 8 there is also a step-by-step deck each in [slides/missions/](slides/missions/), ending with the same checklist learners tick off in [CHECKLIST.md](CHECKLIST.md). All decks are Marp; see [slides/README.md](slides/README.md).

| Session | Missions | Time | Notes |
|---|---|---|---|
| Day 1 morning | 0 Landing | 30-60 min | mostly installation; preparing machines beforehand saves a lot |
| | 1 Telemetry | 30-45 min | |
| Day 1 afternoon | 2 Manual Drive | 30-45 min | have learners work out the commands on paper before typing |
| | 3 Mission Control | 30-45 min | finish with the first half of ARCHITECTURE.md (big picture, the four ways nodes talk) |
| Day 2 morning | 4 Survey Square | 60 min | where people get stuck most: `setup.py`, forgetting to build/source |
| | 5 Waypoints | 45-60 min | draw the atan2 triangle and the quaternion → yaw formula on the board |
| Day 2 afternoon | 6 Sample Hunter | 60 min | |
| | 7 Rover Fleet | 45-60 min | |
| Day 3 (or homework) | 8 Boss: Power Crisis | 60-90 min | pairs work well; afterwards, ARCHITECTURE.md's design patterns |
| Day 4 morning | 9 Arm Check | 30-45 min | let them play; intuition for joint space pays off in 10 |
| | 10 Frames | 60-90 min | do one frame change by hand on the board before showing tf2; derive the law of cosines together |
| Day 4 afternoon | 11 Drill & Stow | 60-90 min | run the drill once from the terminal without cancelling: watching the bit break makes feedback and cancel stick |
| Day 5 (or project) | 12 Boss: Meteorite Recovery | 90+ min | works well as a team project or competition; the "split it up" design challenge makes a good follow-up |

Part 2 (missions 9-12) works as a follow-up course for learners who already know ROS 2 basics.

## Isolate each learner's network

ROS 2 discovers other nodes on the network automatically. If every machine in the room is on the same Wi-Fi,
learners will see (and drive) each other's rovers, and mission control's scoring gets mixed up.

Give each learner a unique number (0-101) in `~/.bashrc`:

```bash
echo "export ROS_DOMAIN_ID=<learner number>" >> ~/.bashrc
```

or, if nobody needs to talk across machines, keep ROS on each laptop: `export ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST` (on Humble: `export ROS_LOCALHOST_ONLY=1`).

To show that ROS 2 works across machines, do the opposite: give two computers the same `ROS_DOMAIN_ID` and run `sample_hunter` on one to drive the rover on the other. It always gets a reaction.

## How mission control checks things

`mission_control` (in `src/mission_control/`) watches the rovers through the same topics the learners use. Only the ground truth of the world comes from a private referee topic.

| Checks | From |
|---|---|
| position, reaching beacons, distance driven | subscribing to `/<rover>/odom` |
| battery, bumps, samples on board | `/<rover>/battery`, `/<rover>/bumps`, `/<rover>/samples_onboard` |
| what was sent on the radio | `/<rover>/radio` |
| photos taken | `/earth/downlink` (the simulator posts every photo there) |
| samples and meteorites delivered | `/lander/samples`, `/lander/meteorites` |
| arm moving, what the grippers hold | `/<rover>/joint_states`, `/<rover>/<side>_gripper/holding` |
| gripper positions, teleports, broken drill, every object in the world | the simulator's referee topic `/judge/state` (JSON in a `String`) |
| has scout been spawned | does `/scout/odom` exist in the graph |
| own node vs. teleop | node names publishing `cmd_vel` / `arm/joint_command` (`get_publishers_info_by_topic`); `teleop_*`, `_ros2cli_*` and `rosbag2_*` (replaying a recording) count as driving by hand |
| peeking at the referee | any node other than mission_control subscribed to `/judge/state` |
| namespaces used | the namespaces of the nodes publishing `cmd_vel` |
| parameter changed live | subscribing to `/parameter_events` |

The cheat detection is a deterrent, not security. A determined learner can dodge it, for example by renaming their node. If you catch one, praise them: they clearly understand the ROS graph.

Timing: missions 0-3 and 9 start the clock at launch. The coding missions start it when the rover (or an arm) first moves, so typing `ros2 run` doesn't cost stars. Mission 5's star times scale with the length of that run's random route.

Missions can fail: when a rover's battery reaches 0 (that only really happens in missions 8 and 12) or when the drill bit overheats (missions 11 and 12). The panel says why; learners close the window and launch again.

## Running a contest in class

- Use a `seed` so everyone gets exactly the same world (beacons, rocks, samples, meteorites, the code from Earth):
  ```bash
  ros2 launch mission_control mission.launch.py mission:=6 seed:=2026
  ```
- Each learner's best results are in `~/.mars_rover_academy/progress.json`. Show them with `ros2 run mission_control progress` (reset with `--reset`).
- Contests that work well: missions 6, 8 or 12 with a shared seed, fastest time wins. Or mission 7 with two learners each controlling one rover and competing for samples.

## Solutions

Reference solutions for every coding mission live in a separate package, `rover_solutions`. It is not published in this repository,
so learners can't peek; instructors can ask the maintainer for it. Put it in `solutions/rover_solutions/` (the `solutions/` folder is
gitignored, so it can't be committed by accident) and rebuild. colcon picks it up with everything else.
It's handy for showing learners what the goal looks like:

```bash
ros2 run rover_solutions square                                    # mission 4
ros2 run rover_solutions go_to_goal                                # mission 5
ros2 run rover_solutions sample_hunter --ros-args -r __ns:=/rover1 # mission 6
ros2 launch rover_solutions fleet.launch.py                        # mission 7 (+ ros2 param set yourself)
ros2 run rover_solutions power_crisis                              # mission 8
ros2 run rover_solutions arm_reach                                 # mission 10
ros2 run rover_solutions drill_and_stow                            # mission 11
ros2 run rover_solutions meteorite_mover                           # mission 12
```

The solutions get 3 stars. The code in the mission guides is simpler and usually gets 2, which leaves learners room to improve it (the boss skeletons, filled in as the hints say, just reach 3).
The guides for missions 8 and 12 give a skeleton with TODOs and tell learners to ask you for a demo.

`solutions/tests/missions.sh` runs every mission headless with these solutions and prints the result, and
`solutions/tests/docker.sh` does the same in a clean `ros:jazzy-ros-base` container. Run one of them after changing a mission or the simulator.

## Tuning the difficulty

| What | Where |
|---|---|
| star thresholds, world layout, objectives | the mission classes in `src/mission_control/mission_control/missions.py` |
| simulator settings for one mission | `sim_params` on the mission class (passed to `mars_sim` by `mission.launch.py`) |
| rover stops without new commands | `mars_sim` parameter `cmd_vel_timeout` (default 1.0 s) |
| how much sand slows the rover | `sand_slip` (default 0.6 = 60 % of the commanded speed) |
| battery | `battery_start` (0-1) and `battery_drain` (a multiplier) |
| arms on/off, zoom | `arms`, `view_zoom`, `view_center_x`, `view_center_y` |
| hide the grid or the sensor drawings (harder) | `mission.launch.py ... show_grid:=false`, `mars_sim` parameter `show_sensors` |
| rover speed and acceleration, sensor ranges, arm geometry, grasp distances, drill heating, meteorite rules | constants at the top of `src/mars_sim/mars_sim/world.py` |

## Writing a new mission

A mission is a class in `src/mission_control/mission_control/missions.py`. Example: mission 13 "Corner Tour", playable right away with mission 5's `go_to_goal`:

```python
class Corners(Mission):
    number = 13
    title = 'Corner Tour'
    story = ['Visit the four corners of the map.', 'go_to_goal from mission 5 will do!']
    star_times = (60, 120)
    coding = True           # must use your own node + the clock starts when the rover moves
    forbid_teleport = True

    def setup(self):        # build the world: called once at the start (the world is already cleared)
        self.r = self.mc.watch('rover1')
        self.scenery(rocks=[(10.0, 10.0, 1.0)], sand=[(10.0, 3.0, 2.0)])
        self.run = BeaconRun([(17.0, 3.0), (17.0, 17.0), (3.0, 17.0), (3.0, 3.0)], radius=0.6)
        self.beacons = Objective('Reach the beacons in order', total=4)
        self.own = self.own_node_objective()
        self.objectives = [self.beacons, self.own]

    def update(self):       # called 10 times per second: update the objectives
        self.run.update(self.r.pos)
        self.beacons.progress(self.run.reached)
        self.own.check(self.own_node_driving())

    def goals(self):        # beacons to draw on the map (and to publish on /mission/goals)
        return self.run.remaining()

    def hints(self):        # blue lines in the side panel
        return ['ros2 run my_rover go_to_goal']
```

Then add `Corners` to the `MISSIONS` tuple at the end of the file, rebuild, and run `ros2 launch mission_control mission.launch.py mission:=13`.

What `self.mc` (the `MissionControl` node) gives you:

| | |
|---|---|
| `watch(name)` | start tracking a rover; returns a `RoverWatch` with `.pos`, `.x`, `.y`, `.yaw`, `.v`, `.w`, `.distance`, `.battery`, `.bumps`, `.onboard`, `.said`, `.holding`, `.tip(side)`, `.teleports()`, `.odom_rate()`, `.distance_to(x, y)` |
| `place(kind, x, y, radius=0, id='')` | put an object into the world: `rock`, `sand`, `crater`, `landmark`, `sample`, `drill_site`, `core`, `meteorite` |
| `spawn_rover(name, x, y, yaw)`, `teleport(name, x, y, yaw)`, `radio(name, text)` | |
| `judge` | the latest `/judge/state` (every object, every rover's ground truth) |
| `photos`, `lander_samples`, `lander_meteorites` | what reached Earth and the lander |
| `rng` | randomness: always use it, so `seed` works |
| `own_publishers`, `manual_publishers`, `changed_param_nodes`, `judge_peekers` | facts from the ROS graph for checking |
| `topic_exists(topic)`, `node_namespaces()`, `elapsed()`, `since_start()` | |

And in `missions.py`: `Objective(text, total=None)` with `.check(cond)` / `.progress(n)` (ticks stay ticked), `BeaconRun(points, radius)` for ordered beacons
(`update()` takes any positions that may reach them, e.g. `self.r.pos` or `self.r.tip('left')`), `scenery(...)` and `random_points(...)` to build the world,
`items()` to publish object positions on `/mission/items`, `failure()` to end a mission early, `sim_params` for the simulator,
and the rule flags `coding` / `forbid_teleop` / `forbid_teleport` / `forbid_driving`.

## Common classroom problems

| Symptom | Cause / fix |
|---|---|
| `Package ... not found` / `No executable found` | forgot `source install/setup.bash`, or forgot to build after editing `setup.py` |
| `error: option --editable not recognized` while building | a pip-installed setuptools is too new (≥ 80): `pip3 install --user "setuptools<80"`, plus `--break-system-packages` on Ubuntu 24.04 |
| `ros2 topic pub` says `unrecognized arguments` | an option (`--once`, `--rate`, `--times`) ended up between the type and the data; put the options right after `pub` |
| the rover moves by itself / weird stars | `ROS_DOMAIN_ID` clashes with a neighbour, or an old node is still running in another terminal (`ros2 node list`) |
| the rover ignores commands | the mission failed (battery at 0), or nobody is publishing: a single message only lasts 1 s |
| a traceback appears when pressing Ctrl+C on `ros2 launch` | harmless: the terminal and launch both send the stop signal, and the second one arrives while the node is already shutting down |
| `tf2_ros ... Lookup would require extrapolation` / `frame does not exist` | the node asked before the first transforms arrived; catch `TransformException` and try again on the next tick |
| the window stutters on slow machines / VMs | still playable (physics follows real time); closing other programs helps |

## License

Apache-2.0, see [LICENSE](LICENSE). You may use, change and share the course, including in commercial training.
