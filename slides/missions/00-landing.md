---
marp: true
title: "Mission 0: Landing"
description: Step-by-step teaching slides for Mars Rover Academy mission 0
paginate: true
size: 16:9
footer: Mars Rover Academy · Mission 0
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

# Mission 0: Landing

rover1 has just touched down on Mars. Install the software, start it up and drive the rover off the lander to the beacon.

**You will learn:** workspace · package · colcon · source · launch · teleop · remapping

<!--
Suggested time: 30 to 60 minutes. Most of it is installation, so prepare the machines beforehand if you can (ROS 2, python3-pygame, teleop_twist_keyboard, the repo cloned and built).
Goal of the session: everyone has a working workspace and has driven rover1 off the lander once.
Say: this is a 20 × 20 metre patch of Mars, and for the whole of Part 1 it's our test ground.
-->

---

<!-- _class: roadmap -->
<!-- header: Where we are -->

# Part 1 roadmap

| | # | Mission | You learn |
|---|---|---|---|
| **▶** | **0** | **Landing** | **workspace, build, launch, teleop, remapping** |
| | 1 | Telemetry | nodes, topics, messages |
| | 2 | Manual Drive | publishing `Twist`, speeds and angles |
| | 3 | Mission Control | services: request and response |
| | 4 | Survey Square | a package and a Python publisher |
| | 5 | Waypoints | subscribers, `Odometry`, closed-loop control |
| | 6 | Sample Hunter | camera and laser, service clients in code |
| | 7 | Rover Fleet | namespaces, parameters, launch files |
| | 8 | Boss: Power Crisis | all of the above, state machines, battery |

<!--
About 1 minute. Show this at the start of every session so people see the whole path. Today is the first row.
Missions 0 to 3 happen in the terminal only; from mission 4 on, people write their own Python nodes.
-->

---

<!-- header: Mission 0 · Goal -->

# Today's goal

![bg right:42% contain](../../docs/images/mars/mission-0.png)

**Objectives**
1. Make the rover move
2. Drive to beacon 1

**Stars:** ≤ 60 s = ⭐⭐⭐ · ≤ 2.5 min = ⭐⭐ · slower = ⭐

The panel on the right of the window ticks the objectives by itself.

<!--
About 2 minutes. Point at the screenshot: rover1 on the grey lander in the bottom-left corner, beacon 1 (the numbered marker with a circle) at (9, 7), the panel on the right.
Nobody has to ask "is this right?": mission control checks it and ticks the boxes.
The clock starts when the mission is launched. Stars are a bit of fun, not a grade.
-->

---

<!-- header: Mission 0 · Step 1 of 4 -->

# Step 1: Install what you need

ROS 2 on Ubuntu: **Jazzy (Ubuntu 24.04) or newer** is recommended, Humble (22.04) works too.

<style scoped>pre { font-size: 18px; }</style>

```bash
source /opt/ros/jazzy/setup.bash
sudo apt install python3-pygame python3-numpy ros-$ROS_DISTRO-teleop-twist-keyboard
```

- `pygame` draws the simulator window, `numpy` does the sensor maths
- `teleop_twist_keyboard` lets you drive with the keyboard, the same tool people use on real robots

On another distro, write its name instead of `jazzy`.

<!--
About 5 minutes if ROS 2 is already installed. If it isn't, follow docs.ros.org/en/jazzy/Installation/Ubuntu-Install-Debs.html first. That takes 10 to 20 minutes per machine, so it's much better done before class.
Learners should see apt finish without errors.
Usual mistake: running the apt line in a terminal where ROS 2 isn't sourced, so $ROS_DISTRO is empty and apt can't find "ros--teleop-twist-keyboard".
-->

---

<!-- header: Mission 0 · Step 2 of 4 -->

# Step 2: Build the workspace

<style scoped>pre { font-size: 18px; }</style>

```bash
git clone <url of this repo> ~/mars_rover
cd ~/mars_rover
source /opt/ros/jazzy/setup.bash       # (1) wake up ROS 2 in this terminal
colcon build --symlink-install         # (2) build every package in src/
source install/setup.bash              # (3) tell this terminal about the packages you just built
```

**You should see:** a `Summary:` line at the end with every package finished and none failed.

<!--
About 5 minutes. Walk through the three numbered lines slowly; the next slide explains the words.
Replace <url of this repo> with the real URL (write it on the board).
Usual mistakes: running colcon build somewhere other than ~/mars_rover, and forgetting line (3). If colcon build fails with "option --editable not recognized", see the "Stuck?" slide.
-->

---

<!-- header: Mission 0 · Step 2 of 4 -->

# Four words you just used

| Word | Meaning |
|---|---|
| **package** | a box of code plus a `package.xml` with its name and dependencies |
| **workspace** | the folder that collects packages under `src/` |
| **colcon build** | builds every package into `build/`, `install/` and `log/` |
| **source** | plugs the new commands and packages into *this* terminal |

> You have to `source` again in **every new terminal**. Forgetting it is the most common cause of "Package not found". To do it once and forget about it:

```bash
echo "source /opt/ros/jazzy/setup.bash" >> ~/.bashrc
echo "source ~/mars_rover/install/setup.bash" >> ~/.bashrc
```

<!--
About 3 minutes. src/ holds three packages: mars_sim (the simulator), mars_interfaces (the rover's own message and service types) and mission_control (the referee).
Recommend the .bashrc lines to everyone; it prevents half of the questions you'd otherwise get.
Usual mistake: adding the lines but not opening a new terminal, so nothing changes yet.
-->

---

<!-- header: Mission 0 · Step 3 of 4 -->

# Step 3: Launch the mission

```bash
ros2 launch mission_control mission.launch.py mission:=0
```

<style scoped>table { font-size: 21px; } th, td { padding: 6px 14px; }</style>

| What you see | What it is |
|---|---|
| grid, numbers on the edges | x and y in metres, (0, 0) bottom-left, the map is 20 × 20 m |
| grey pad marked LANDER | the lander at (3, 3), 3 m across; later the rover charges and drops off samples here |
| the rover and its name | `rover1` on the lander at (3, 3), facing right (+x, east, yaw = 0°) |
| numbered marker with a circle | a beacon; anywhere inside its circle counts |
| panel on the right | objectives, hints, time, and each rover's x, y, yaw, v, w and battery |

<!--
About 3 minutes. Leave this terminal running for the rest of the mission.
Learners should see the Mars Rover Academy window with rover1 on the lander.
If the window doesn't open: is pygame installed, and did you source install/setup.bash in this terminal?
-->

---

<!-- header: Mission 0 · Step 3 of 4 -->

# What's on the map

| What you see | What it is |
|---|---|
| pale cone in front of the rover | what the camera sees (6 m, 60° wide), used from mission 3 on |
| red dots on rocks | where the laser scanner hits something, used in mission 6 |
| dark rocks | can't drive through: the rover stops and counts a bump |
| pale ground with ripples | sand: the wheels slip, which matters from mission 5 |
| round pit | a crater: you can drive through it, slowly |

<!--
About 2 minutes. Point at each one in the live window rather than reading the table.
None of these matter for today's objectives, but people will ask. The extras at the end let fast finishers try the rocks, sand and crater.
-->

---

<!-- header: Mission 0 · Step 4 of 4 -->

# Step 4: Drive

Open a **new** terminal and leave the first one running:

<style scoped>pre { font-size: 17px; }</style>

```bash
source ~/mars_rover/install/setup.bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -r cmd_vel:=/rover1/cmd_vel
```

Click into this terminal so it has keyboard focus.

<!--
About 2 minutes. The second line is long: copy it from the mission guide instead of typing it. The hint in the window's panel shows it too.
Learners should see teleop print its key layout and the current speed.
The classic problem: people click the simulator window and press keys there. Teleop reads the keyboard from its own terminal, so that terminal needs focus.
-->

---

<!-- header: Mission 0 · Step 4 of 4 -->

# Keys

| Key | Does |
|---|---|
| `i` | forward (hold it down to keep going) |
| `,` | backward |
| `j` / `l` | turn left / right |
| `k` | stop |
| `q` / `z` | faster / slower |

Beacon 1 is at (9, 7): up and to the right of the lander. Turn a little to the left, drive, and correct as you go. **Touch the beacon** and the panel shows *Mission complete* with your stars.

<!--
About 5 minutes of driving.
Learners should see the first objective tick as soon as the rover has moved half a metre, then Mission complete at the beacon.
Usual mistakes: pressing the arrow keys (this teleop uses i, j, l, k), and holding j or l too long so the rover spins past the beacon.
-->

---

<!-- header: Mission 0 · Step 4 of 4 -->

# What was that `-r cmd_vel:=...` part?

- Teleop sends its driving commands to a topic called `cmd_vel`.
- The simulator listens on `/rover1/cmd_vel`: every rover gets its own set of names, and there can be more than one rover.
- `--ros-args -r` **remaps** a name when the program starts: "where you would have used `cmd_vel`, use `/rover1/cmd_vel`".

You change the wiring without touching teleop's code. Without it, teleop talks to `/cmd_vel`, nobody is listening there, and the rover doesn't move.

<!--
About 3 minutes. This is the one new ROS idea today, so give it time.
If someone in the room forgot the -r part, use their screen as the live example: teleop happily prints its speed and nothing moves.
Remapping comes back in mission 7, where the launch file does it for a whole fleet.
-->

---

<!-- header: Mission 0 · Checkpoint -->

# Stuck?

<style scoped>table { font-size: 20px; margin-bottom: 20px; } th, td { padding: 5px 12px; } td code { white-space: nowrap; }</style>

| Symptom | Fix |
|---|---|
| `Package 'mission_control' not found` | `source install/setup.bash` in this terminal |
| `No module named 'pygame'` | `sudo apt install python3-pygame` |
| `teleop_twist_keyboard` not found | `sudo apt install ros-$ROS_DISTRO-teleop-twist-keyboard` |
| keys do nothing | click into the teleop terminal first |
| teleop prints the speed, the rover doesn't move | the `--ros-args -r cmd_vel:=/rover1/cmd_vel` part is missing or misspelled |
| `option --editable not recognized` | `pip3 install --user "setuptools<80"` (+ `--break-system-packages` on 24.04), or build without `--symlink-install` |

**Done?** Everyone should have seen *Mission complete* before moving on.

<!--
Walk around the room at this point. Pair people who finished with people who are stuck.
The last row: a setuptools installed with pip is too new for colcon's --symlink-install. It only shows up on machines where someone pip-installed things before.
-->

---

<!-- header: Mission 0 · System map -->

# What happened behind the scenes

![w:1100](../images/missions/m00-1.png)

- Each program is a **node**: teleop, the simulator, mission control
- They never call each other. They send messages over named **topics**
- Teleop doesn't know who listens; it just puts commands on `/rover1/cmd_vel`

<!--
About 3 minutes. Green = a node that already exists, yellow = you, blue = a topic. These colours are the same in every mission.
mission_control doesn't look at the screen either: it reads the rover's position on /rover1/odom, sends the objectives back to the window on /mission/hud and the beacon on /mission/goals.
Next mission we listen in on these topics ourselves.
-->

---

<!-- header: Mission 0 · Check yourself -->

# Check yourself

1. You start teleop without the `--ros-args -r cmd_vel:=/rover1/cmd_vel` part. What happens?

2. Which three nodes were running while you drove?

<!--
Let people answer before you show anything.
1. Teleop starts and prints its speed, but it publishes on /cmd_vel. Nobody listens there, so the rover doesn't move.
2. teleop_twist_keyboard, mars_sim and mission_control. Mission 1 starts with ros2 node list, which shows the last two.
-->

---

<!-- _class: checklist -->
<!-- header: Mission 0 · Checklist -->

# Before you move on, can you...

- build the workspace with `colcon build`?
- explain why every new terminal needs `source`?
- launch a mission and say what each part of the window shows?
- drive the rover with teleop and explain what `-r cmd_vel:=/rover1/cmd_vel` does?
- name the three nodes that were running?

<!--
The same list is in CHECKLIST.md for learners to tick off. Anyone who can't answer the second question: show them a new terminal without source and let them see the error.
-->

---

<!-- _class: roadmap -->
<!-- header: Where we are -->

# Next: Mission 1, Telemetry

| | # | Mission | You learn |
|---|---|---|---|
| ✓ | 0 | Landing | workspace, build, launch, teleop, remapping |
| **▶** | **1** | **Telemetry** | **nodes, topics, messages** |
| | 2 | Manual Drive | publishing `Twist`, speeds and angles |
| | 3 | Mission Control | services: request and response |
| | 4 | Survey Square | a package and a Python publisher |
| | 5 | Waypoints | subscribers, `Odometry`, closed-loop control |
| | 6 | Sample Hunter | camera and laser, service clients in code |
| | 7 | Rover Fleet | namespaces, parameters, launch files |
| | 8 | Boss: Power Crisis | all of the above, state machines, battery |

<!--
Extras for fast finishers (no stars):
- Drive into a rock and watch the rover stop. Back off with ,
- Drive through the sand and the crater and compare v in the panel with what teleop says it sends.
- Hide the grid: ros2 launch mission_control mission.launch.py mission:=0 show_grid:=false
- Get the same random world as a friend: both add seed:=42 (any number) to the launch command.
- See all your stars so far: ros2 run mission_control progress
-->
