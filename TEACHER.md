# Instructor guide

For anyone running Turtle Quest in a classroom or a workshop.

## The idea behind the course

Learners do first and get the theory second. Every mission starts with a concrete goal, and the concept sections show up when they're needed. `quest_master` ticks objectives the moment they're met, so nobody has to ask "is this right?" They also build on their own code. Mission 5's controller comes back in 6, 7, 8 and 12, mission 10's IK in 11 and 12, and learners feel why readable code matters.

Every mission has a system map; [ARCHITECTURE.md](ARCHITECTURE.md) connects them. The best habit you can build is drawing the map on the board before coding: what goes in, what comes out?

Stars are optional. Finishing always earns at least 1 star; stars 2-3 are for those who want to tune and strategise.

## Suggested schedule

| Session | Missions | Time | Notes |
|---|---|---|---|
| Day 1 morning | 0 Boot Camp | 30-60 min | mostly installation; preparing machines beforehand saves a lot |
| | 1 Spy Turtle | 30-45 min | |
| Day 1 afternoon | 2 Steering Wheel | 30-45 min | have learners compute on paper before typing |
| | 3 Service Hotline | 30-45 min | finish with the first half of ARCHITECTURE.md (big picture, the four ways nodes talk) |
| Day 2 morning | 4 My First Node | 60 min | where people get stuck most: `setup.py`, forgetting to build/source |
| | 5 Turtle Eyes | 45-60 min | drawing atan2 on the board helps a lot |
| Day 2 afternoon | 6 Pizza Hunter | 60 min | |
| | 7 Turtle Team | 45-60 min | |
| Day 3 (or homework) | 8 Boss | 60-90 min | pairs work well; afterwards, ARCHITECTURE.md's design patterns |
| Day 4 morning | 9 Arm Day | 30-45 min | let them play; intuition for joint space pays off in 10 |
| | 10 Long Reach | 60-90 min | derive the law-of-cosines IK together on the board |
| Day 4 afternoon | 11 Pick & Place | 60 min | |
| Day 5 (or project) | 12 Boss | 90+ min | works well as a team project or competition; the "split it up" design challenge makes a good follow-up project |

Part 2 (missions 9-12) works as a follow-up course for learners who already know ROS 2 basics.

## Isolate each learner's network

ROS 2 discovers other nodes on the network automatically. If every machine in the room is on the same Wi-Fi,
learners will see (and drive) each other's turtles, and the quest master's scoring gets mixed up.

Give each learner a unique number (0-101) in `~/.bashrc`:

```bash
echo "export ROS_DOMAIN_ID=<learner number>" >> ~/.bashrc
```

or, if nobody needs to talk across machines, `export ROS_LOCALHOST_ONLY=1`.

To show that ROS 2 works across machines, do the opposite: give two computers the same `ROS_DOMAIN_ID` and run `pizza_hunter` on one to drive the turtle on the other. It always gets a reaction.

## How the quest master checks things

`quest_master` (in `src/turtle_quest/`) only uses ROS 2 interfaces, the same ones the learners use:

| Checks | From |
|---|---|
| position, touching flags, distance, teleports | subscribing to `/<turtle>/pose` |
| pizzas eaten / parcels delivered | `/<turtle>/pizza_count`, `/parcel_count` |
| what the turtle said | `/<turtle>/say` |
| gripper tips, what they hold | `/<turtle>/<side>_arm/tip`, `/<turtle>/<side>_gripper/holding` |
| where every pizza / parcel / crate is | the simulator's referee topic `/judge/objects` |
| has buddy been spawned | does `/buddy/pose` exist in the graph |
| own node vs. teleop | node names publishing `cmd_vel` / `joint_command` (`get_publishers_info_by_topic`); `teleop_*` and `_ros2cli_*` count as driving by hand |
| peeking at the referee | any node other than quest_master subscribed to `/judge/objects` |
| namespaces used | `get_node_names_and_namespaces()` |
| parameter changed live | subscribing to `/parameter_events` |

The cheat detection is a deterrent, not security. A determined learner can dodge it, for example by renaming their node. If you catch one, praise them: they clearly understand the ROS graph.

Timing: missions 0-3 and 9 start the clock at launch. The coding missions start it when the turtle (or an arm) first moves, so typing `ros2 run` doesn't cost stars.

## Running a contest in class

- Use a `seed` so everyone gets exactly the same world (flags, pizzas, parcels, crates, the secret code):
  ```bash
  ros2 launch turtle_quest mission.launch.py mission:=6 seed:=2026
  ```
- Each learner's best results are in `~/.turtle_quest/progress.json`. Show them with `ros2 run turtle_quest progress` (reset with `--reset`).
- Contests that have worked well: missions 6, 8 or 12 with a shared seed, fastest time wins. Or mission 7 with two learners each controlling one turtle and competing for pizzas.

## Solutions

Reference solutions for every coding mission live in a separate package, `quest_solutions`. It is not published in this repository,
so learners can't peek; instructors can ask the maintainer for it. Put it in `solutions/quest_solutions/` (the `solutions/` folder is
gitignored, so it can't be committed by accident) and rebuild. colcon picks it up with everything else.
It's handy for showing learners what the goal looks like:

```bash
ros2 run quest_solutions square              # mission 4
ros2 run quest_solutions go_to_goal          # mission 5
ros2 run quest_solutions pizza_hunter        # mission 6
ros2 launch quest_solutions team.launch.py   # mission 7 (+ ros2 param set yourself)
ros2 run quest_solutions delivery            # mission 8
ros2 run quest_solutions arm_reach           # mission 10
ros2 run quest_solutions pick_place          # mission 11
ros2 run quest_solutions crate_mover         # mission 12
```

The solutions are tuned for 3 stars. The code in the mission guides defaults to 2 stars (missions 4-8), which leaves learners room to improve it.
The guides for missions 8 and 12 deliberately stop at hints and tell learners to ask you for a demo.

## Tuning the difficulty

| What | Where |
|---|---|
| star thresholds | `star_times` of each mission in `src/turtle_quest/turtle_quest/missions.py` |
| scanner / eating / pickup range | launch arguments of `turtlesim_plus.launch.py` (`scanner_radius`, `eat_radius`, `pickup_radius`, ...) |
| turtle stops without new commands | turtlesim_plus parameter `cmd_vel_timeout` (default 1.0 s, 0 = never) |
| arm joint speed | turtlesim_plus parameter `arm_joint_speed` (default 2.0 rad/s) |
| arm geometry, grasp distances, crate rules | constants at the top of `src/turtlesim_plus/turtlesim_plus/arms.py` |
| hide the grid (harder) | `mission.launch.py ... show_grid:=false` |

## Writing a new mission

A mission is a class in `src/turtle_quest/turtle_quest/missions.py`. Example: mission 13 "Corner Tour", playable right away with mission 5's `go_to_goal`:

```python
class Corners(Mission):
    number = 13
    title = 'Corner Tour'
    story = ['Touch the flags in all 4 corners.', 'go_to_goal from mission 5 will do!']
    star_times = (30, 60)
    coding = True  # must use your own node + the clock starts when the turtle moves

    def setup(self):  # build the scene: called once at the start (the world is already cleared)
        self.t = self.qm.watch('turtle1')
        self.run = GoalRun([(1.0, 1.0), (9.88, 1.0), (9.88, 9.88), (1.0, 9.88)], radius=0.6)
        self.flags = Objective('Touch the flags in order', total=4)
        self.own = self.own_node_objective()
        self.objectives = [self.flags, self.own]

    def update(self):  # called 10 times per second: update the objectives
        self.run.update(pos(self.t))
        self.flags.progress(self.run.reached)
        self.own.check(bool(self.qm.own_publishers))

    def goals(self):  # flags to draw on the map
        return self.run.remaining()

    def hints(self):  # blue lines in the side panel
        return ['ros2 run my_turtle go_to_goal']
```

Then add `Corners` to the `MISSIONS` tuple at the end of the file and run `ros2 launch turtle_quest mission.launch.py mission:=13`.
Set `arms = True` on the class and `mission.launch.py` starts the simulator with arms for it.

What `self.qm` (the `QuestMaster`) gives you:

| | |
|---|---|
| `watch(name)` | start tracking a turtle; returns a `TurtleWatch` with `.pose`, `.pizza`, `.parcel`, `.carrying`, `.said`, `.distance`, `.teleported`, `.tips`, `.holding` |
| `spawn_pizza(x, y)`, `spawn_parcel(x, y)`, `spawn_crate(x, y)`, `spawn_turtle(name, x, y, theta)`, `teleport(name, x, y, theta)` | build the scene |
| `objects` | every pizza/parcel/crate from `/judge/objects` (`.name`, `.type`, `.x`, `.y`, `.held_by`) |
| `rng`, `random_point(margin, avoid, min_gap)` | randomness (always use `rng` so `seed` works) |
| `say(name, text)` | make a turtle talk |
| `own_publishers`, `manual_publishers`, `changed_param_nodes`, `judge_peekers` | facts from the ROS graph for checking |
| `topic_exists(topic)`, `node_namespaces()`, `elapsed()` | |

And in `missions.py`: `Objective(text, total=None)` with `.check(cond)` / `.progress(n)` (ticks stay ticked), `GoalRun(points, radius)` for ordered flags
(`update()` takes any positions that may touch them, e.g. `pos(watch)` or `*watch.tips.values()`), `items()` to publish object positions on `/mission/items`,
and the rule flags `coding` / `forbid_teleop` / `forbid_teleport` / `forbid_driving`.

## Common classroom problems

| Symptom | Cause / fix |
|---|---|
| `Package ... not found` / `No executable found` | forgot `source install/setup.bash`, or forgot to build after editing `setup.py` |
| the turtle moves by itself / weird stars | `ROS_DOMAIN_ID` clashes with a neighbour, or an old node is still running in another terminal (`ros2 node list`) |
| `error: option --editable not recognized` while building | pip setuptools too new (≥ 80): `pip3 install "setuptools<80"` |
| the arms don't appear | missions 9-12 enable them automatically; in free play use `turtlesim_plus.launch.py arms:=true` |
| the window stutters on slow machines / VMs | still playable (physics follows real time); closing other programs helps |

## License

The code in this repo is GPL-3.0, following the original turtlesim_plus. You may share and modify it, but derivatives must also be open source under GPL-3.0.
