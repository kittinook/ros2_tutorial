# Mission 0: Boot Camp 🔌

> **Briefing:** Welcome to the team! Your first turtle is waiting in an 11 × 11 metre world.
> Job one is easy — assemble the machine, flip the switch, and drive the turtle to the flag 🚩

![Mission 0: the turtle in the middle of the map, flag 1 in the top-right](../docs/images/mission-0.png)

**🎯 Objectives**
- [ ] Make the turtle move
- [ ] Drive to flag 1

**⭐ Stars:** ≤ 30 s = ⭐⭐⭐ · ≤ 90 s = ⭐⭐ · slower = ⭐

---

## Step 1: Install what you need

You need Ubuntu 22.04 + ROS 2 Humble. Then add:

```bash
sudo apt install python3-pygame python3-numpy ros-humble-turtlesim
```

`pygame` draws the turtle window; `turtlesim` provides the keyboard teleop and some message types.

## Step 2: Build the workspace

```bash
git clone <url of this repo> ~/turtle_quest
cd ~/turtle_quest
source /opt/ros/humble/setup.bash      # (1) wake up ROS 2 in this terminal
colcon build --symlink-install         # (2) build every package in src/
source install/setup.bash              # (3) tell this terminal about the packages you just built
```

> 🧠 **Concept card: workspace, package, colcon, source**
>
> - A **package** is a box of code plus a `package.xml` that says its name and what it depends on
>   (`src/` holds three: `turtlesim_plus`, `turtlesim_plus_interfaces`, `turtle_quest`)
> - A **workspace** is a folder that collects packages under `src/`
> - **`colcon build`** builds every package; the results land in `build/`, `install/` and `log/`
> - **`source`** "plugs in" the new commands/packages to your terminal
>   ⚠️ **you must do it again in every new terminal** — the #1 cause of "Package not found"
>
> 💡 Too much typing? Add it to `~/.bashrc` once:
> ```bash
> echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc
> echo "source ~/turtle_quest/install/setup.bash" >> ~/.bashrc
> ```

## Step 3: Launch the mission

```bash
ros2 launch turtle_quest mission.launch.py mission:=0
```

The **TURTLESIM+** window pops up. A quick tour:

| What you see | What it is |
|---|---|
| grey grid + numbers on the edges | x (horizontal) and y (vertical) coordinates in metres; (0, 0) is the bottom-left corner |
| 🐢 the turtle + its name | `turtle1` starts in the middle (5.44, 5.44) facing right (θ = 0°) |
| big red cone | what the **scanner** can see (4 m, 60° wide) — used in mission 6 |
| small green cone | where the turtle can **eat** pizza (2 m) |
| DROP-OFF circle | parcel delivery zone — used in the boss missions |
| panel on the right | mission objectives + time + live status of every turtle (x, y, th, pizzas/parcels) |

## Step 4: Drive!

Open a **new terminal** (keep the first one running):

```bash
source ~/turtle_quest/install/setup.bash
ros2 run turtlesim turtle_teleop_key
```

Click into this terminal so it has keyboard focus, then use the arrow keys:
- ⬆️ ⬇️ forward / backward
- ⬅️ ➡️ turn left / right

Touch flag 🚩 1 → the panel shows **Mission complete!** with your stars, and the turtle cheers 🎉

---

## 🔍 What happened behind the scenes?

You just used a real ROS 2 system without noticing:

```mermaid
flowchart LR
    T["teleop_turtle<br/>(node)"] -- "/turtle1/cmd_vel<br/>(topic)" --> S["turtlesim_plus<br/>(node)"]
    S -- "/turtle1/pose" --> Q["quest_master<br/>(node)"]
    Q -- "/hud" --> S
```

- Each program (teleop, the simulator, the quest master) is a **node**
- They never call each other directly; they send messages over named channels called **topics**
- teleop doesn't even know who's listening — it just shouts velocity commands onto `/turtle1/cmd_vel`
- `quest_master` doesn't peek at the screen either: it listens to the turtle's position on `/turtle1/pose` and sends the objectives back to the window on `/hud`

Next mission we'll eavesdrop on these topics 🕵️

## 🛠️ Troubleshooting

| Symptom | Fix |
|---|---|
| `Package 'turtle_quest' not found` | you forgot `source install/setup.bash` in this terminal |
| `ModuleNotFoundError: No module named 'pygame'` | `sudo apt install python3-pygame` |
| arrow keys do nothing | click into the teleop terminal first (it needs focus, not the turtle window) |
| `colcon build` says `error: option --editable not recognized` | your pip-installed setuptools is too new: `pip3 install "setuptools<80"`, or build without `--symlink-install` |

## 🏆 Side quests (no stars, just fun)

- Click on the map ... nothing happens? Try free-play mode
  `ros2 launch turtlesim_plus turtlesim_plus.launch.py` and click again 🍕
- Hide the grid: `ros2 launch turtle_quest mission.launch.py mission:=0 show_grid:=false`

---

**Next →** [Mission 1: Spy Turtle](01-spy.md)
