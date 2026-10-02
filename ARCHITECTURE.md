# How ROS 2 fits together

The missions teach one building block at a time. This page shows how they fit together:
what a ROS 2 system looks like from above, the four ways nodes talk, how to choose between them,
and the patterns that turn a handful of nodes into a robot.

Read it once after [mission 3](missions/03-hotline.md), when you know topics and services, and come back after missions 7 and 12.
It makes more sense each time.

---

## The big picture: a robot is a graph

A ROS 2 system is a set of nodes (programs, each doing one job) connected by named channels.
No node calls another node's functions; they only agree on channel names and message types.
Here is Turtle Quest during mission 8:

```mermaid
flowchart LR
    classDef ros fill:#c8e6c9,stroke:#2e7d32,color:#1b1b1b
    classDef mine fill:#fff59d,stroke:#f57f17,stroke-width:3px,color:#1b1b1b
    classDef topic fill:#bbdefb,stroke:#1565c0,color:#1b1b1b
    classDef srv fill:#ffe0b2,stroke:#e65100,color:#1b1b1b
    classDef param fill:#eeeeee,stroke:#616161,color:#1b1b1b
    SIM(["turtlesim_plus<br/>the world + the robot"]):::ros
    ME(["delivery<br/>YOUR node: the brain"]):::mine
    QM(["quest_master<br/>the referee"]):::ros
    SIM --> POSE["/turtle1/pose"]:::topic
    SIM --> SCAN["/turtle1/scan"]:::topic
    SIM --> CARRY["/turtle1/carrying_parcel"]:::topic
    POSE & SCAN & CARRY --> ME
    ME --> CMD["/turtle1/cmd_vel"]:::topic --> SIM
    ME -. call .-> PICK{{"/turtle1/pickup<br/>/turtle1/dropoff"}}:::srv -.- SIM
    POSE --> QM
    SIM --> COUNT["/turtle1/parcel_count"]:::topic --> QM
    QM --> HUD["/hud"]:::topic --> SIM
```

Every arrow goes through a named channel. `delivery` has no idea `quest_master` exists, and doesn't need to.

One topic can have many readers. `/turtle1/pose` feeds both your node and the referee; add a third reader (`ros2 topic echo`) and nothing else changes.

You can swap any box and the rest keeps working. Replace `turtlesim_plus` with a real robot that offers the same topics and services, and `delivery` drives it unchanged. That's why ROS 2 is built this way.

You can draw this graph live, at any time, with `rqt_graph` (`sudo apt install ros-humble-rqt-graph`).

## How to read the maps

Every mission has a system map drawn in this style:

```mermaid
flowchart LR
    classDef ros fill:#c8e6c9,stroke:#2e7d32,color:#1b1b1b
    classDef mine fill:#fff59d,stroke:#f57f17,stroke-width:3px,color:#1b1b1b
    classDef topic fill:#bbdefb,stroke:#1565c0,color:#1b1b1b
    classDef srv fill:#ffe0b2,stroke:#e65100,color:#1b1b1b
    classDef act fill:#e1bee7,stroke:#6a1b9a,color:#1b1b1b
    classDef param fill:#eeeeee,stroke:#616161,color:#1b1b1b

    P(["publisher node"]):::mine --> T["/topic<br/>MessageType"]:::topic --> Sub(["subscriber node"]):::ros
    C(["client node"]):::mine -. "request ⇄ response" .-> S{{"/service<br/>ServiceType"}}:::srv -.- Srv(["server node"]):::ros
    AC(["action client"]):::mine == "goal → feedback → result" ==> A[["/action<br/>ActionType"]]:::act === AS(["action server"]):::ros
    K[("parameter = value")]:::param -.- N(["node that owns it"]):::ros
```

| Shape | Colour | Meaning |
|---|---|---|
| rounded pill | 🟩 green | a node that already exists (simulator, quest master, teleop) |
| rounded pill, thick border | 🟨 yellow | you: your own node, or a `ros2 ...` command you type (the CLI runs a temporary node) |
| rectangle, solid arrows | 🟦 blue | a topic; arrows show which way the data flows |
| hexagon, dotted lines | 🟧 orange | a service; the dotted arrow comes from the client, the plain dotted line goes to the server that offers it |
| box with side bars, thick lines | 🟪 purple | an action |
| cylinder | ⬜ grey | a parameter stored inside a node |

---

## The four ways nodes talk

### 1. Topics: a stream of messages

```mermaid
sequenceDiagram
    participant Sim as turtlesim_plus
    participant You as your node
    participant QM as quest_master
    loop 100 times per second
        Sim-)You: /turtle1/pose {x, y, theta, ...}
        Sim-)QM: /turtle1/pose {x, y, theta, ...}
    end
    loop 20 times per second
        You-)Sim: /turtle1/cmd_vel {linear.x, angular.z}
    end
```

A topic is one-way, fire and forget. The publisher never learns who, if anyone, received the message. Any number of publishers and subscribers can share a topic. Two publishers on one `cmd_vel` fight each other, which is how quest_master spots your teleop running next to your node.

Use topics for data that keeps flowing: sensor readings, positions, velocity commands, joint states.
Missions: 1, 2 (CLI) · 4 (publisher) · 5 (subscriber) · every mission after that.

### 2. Services: one question, one answer

```mermaid
sequenceDiagram
    participant You as your node (client)
    participant Sim as turtlesim_plus (server)
    You->>Sim: /turtle1/eat  request {}
    Note right of Sim: is a pizza in the green cone?<br/>eat it
    Sim-->>You: response {}
    You->>Sim: /turtle1/left_gripper  request {data: true}
    Sim-->>You: response {success: false, message: "nothing within reach"}
```

A service is two-way: the client sends a request and gets exactly one response back. Each service name has one server and any number of clients.

Use services for short jobs where you want to know the outcome, like spawn, reset, eat or grab. Don't use them for anything slow, because the client is left waiting. In code, always use `call_async` and never block inside a callback (mission 6).
Missions: 3 (CLI) · 6, 8, 11, 12 (clients in code).

### 3. Actions: a long job you can watch and cancel

```mermaid
sequenceDiagram
    participant C as client
    participant S as server
    C->>S: goal: "drive to the kitchen"
    S-->>C: accepted
    loop while working
        S--)C: feedback: "3.2 m left"
    end
    opt changed my mind
        C->>S: cancel
    end
    S-->>C: result: "arrived" (or aborted / canceled)
```

An action is a service for long tasks. The client sends a goal, the server accepts it, sends feedback while it works and finally a result, and the client can cancel at any time. Under the hood an action is just 3 services and 2 topics (`send_goal`, `cancel_goal`, `get_result` + `feedback`, `status`). You can list them with `ros2 service list --include-hidden-services` and `ros2 topic list --include-hidden-topics`.

Use actions for navigating somewhere, moving an arm along a path, anything that takes seconds and might need stopping.
Turtle Quest only has the tiny `/turtle1/detect_pizza` (mission 6 extras). Real robots use actions everywhere: Nav2's `navigate_to_pose`, MoveIt's `move_action`.

### 4. Parameters: a node's settings

```mermaid
flowchart LR
    classDef ros fill:#c8e6c9,stroke:#2e7d32,color:#1b1b1b
    classDef mine fill:#fff59d,stroke:#f57f17,stroke-width:3px,color:#1b1b1b
    classDef topic fill:#bbdefb,stroke:#1565c0,color:#1b1b1b
    classDef srv fill:#ffe0b2,stroke:#e65100,color:#1b1b1b
    classDef param fill:#eeeeee,stroke:#616161,color:#1b1b1b

    L(["launch file / ros2 run -p"]):::mine -- "initial value at start-up" --> K[("max_speed = 1.5")]:::param
    CLI(["ros2 param set"]):::mine -. call .-> SET{{"/turtle2/pizza_hunter/set_parameters"}}:::srv -.- N
    K -.- N(["/turtle2/pizza_hunter"]):::mine
    N -- "announces every change" --> EV["/parameter_events"]:::topic --> QM(["quest_master"]):::ros
```

Parameters are named values inside a node (`max_speed`, `scanner_radius`) that can be set at start-up and changed while it runs. Under the hood every node offers services such as `get_parameters` / `set_parameters` (you saw them in `ros2 service list` in mission 3), and changes are announced on the `/parameter_events` topic. That's how quest_master ticks the "change a parameter" objective in mission 7.

Use parameters for configuration and tuning: speeds, gains, ranges, which robot to control.
Missions: 7 (and every `key:=value` you pass to `ros2 launch`).

### Which one do I need?

```mermaid
flowchart TD
    Q1{"Does the data keep flowing<br/>(sensor, position, velocity)?"} -- yes --> T["topic"]
    Q1 -- no --> Q2{"Is it a setting<br/>you tune or configure?"}
    Q2 -- yes --> P["parameter"]
    Q2 -- no --> Q3{"Does the job take long, or need<br/>progress updates / cancelling?"}
    Q3 -- yes --> A["action"]
    Q3 -- "no: quick, and I want the outcome" --> S["service"]
    classDef topic fill:#bbdefb,stroke:#1565c0,color:#1b1b1b
    classDef srv fill:#ffe0b2,stroke:#e65100,color:#1b1b1b
    classDef act fill:#e1bee7,stroke:#6a1b9a,color:#1b1b1b
    classDef param fill:#eeeeee,stroke:#616161,color:#1b1b1b
    class T topic
    class S srv
    class A act
    class P param
```

| Job | Choice | In Turtle Quest | On a real robot |
|---|---|---|---|
| where am I | topic | `/turtle1/pose` | `/odom`, `/tf` |
| what do I see | topic | `/turtle1/scan` | `/scan` (LiDAR), `/camera/image_raw` |
| move | topic | `/turtle1/cmd_vel` | `/cmd_vel`, exactly the same |
| joint angles | topic | `/turtle1/joint_states` | `/joint_states`, exactly the same |
| grab / release | service | `/turtle1/left_gripper` | gripper services or actions |
| spawn / reset | service | `/spawn_turtle`, `/clear` | `/reset_odometry`, `/clear_costmap` |
| go somewhere far | action | *(you write a node instead)* | Nav2 `/navigate_to_pose` |
| top speed, sensor range | parameter | `max_speed`, `scanner_radius` | `max_vel_x`, `inflation_radius` |

---

## Putting them together: design patterns

The four channels are the parts. These patterns are the usual ways to put them together into a robot.

### Pattern 1: sense, think, act

Almost every robot node has the same shape. Topics come in (sensors), the node decides, and topics and services go out (actuators).

```mermaid
flowchart LR
    classDef ros fill:#c8e6c9,stroke:#2e7d32,color:#1b1b1b
    classDef mine fill:#fff59d,stroke:#f57f17,stroke-width:3px,color:#1b1b1b
    classDef topic fill:#bbdefb,stroke:#1565c0,color:#1b1b1b
    classDef srv fill:#ffe0b2,stroke:#e65100,color:#1b1b1b
    classDef param fill:#eeeeee,stroke:#616161,color:#1b1b1b
    WORLD(["turtlesim_plus<br/>(the world)"]):::ros
    subgraph SENSE["1 SENSE: subscribe"]
        POSE["/turtle1/pose"]:::topic
        SCAN["/turtle1/scan"]:::topic
    end
    THINK(["2 THINK<br/>your node:<br/>state machine + controller"]):::mine
    subgraph ACT["3 ACT: publish / call"]
        CMD["/turtle1/cmd_vel"]:::topic
        EAT{{"/turtle1/eat"}}:::srv
    end
    WORLD --> POSE & SCAN
    POSE & SCAN --> THINK
    THINK --> CMD
    THINK -. call .-> EAT
    CMD -- "the turtle moves → new pose, new scan" --> WORLD
    EAT -.- WORLD
```

The arrow from the world back to SENSE is what makes it a closed loop (mission 5): every action changes what the sensors report next.

### Pattern 2: inside a node, callbacks remember and a timer decides

A node is one process with one executor (`rclpy.spin()`), which runs callbacks one at a time as things arrive:

```mermaid
flowchart LR
    classDef topic fill:#bbdefb,stroke:#1565c0,color:#1b1b1b
    classDef srv fill:#ffe0b2,stroke:#e65100,color:#1b1b1b
    IN1["/turtle1/pose"]:::topic --> EX
    IN2["/turtle1/scan"]:::topic --> EX
    IN3{{"answer from /turtle1/eat"}}:::srv --> EX
    TICK["timer<br/>every 0.05 s"] --> EX
    subgraph NODE["your node (one process)"]
        EX["executor: rclpy.spin()<br/>runs ONE callback at a time"]
        EX --> CB1["pose_callback:<br/>self.pose = msg"]
        EX --> CB2["scan_callback:<br/>self.scan = msg.data"]
        EX --> CB3["eat future:<br/>done() becomes True"]
        EX --> LOOP["control_loop:<br/>read self.pose, self.scan<br/>decide, publish, call_async"]
        CB1 -. "shared state" .-> LOOP
        CB2 -. "shared state" .-> LOOP
        CB3 -. "shared state" .-> LOOP
    end
    LOOP --> OUT["/turtle1/cmd_vel"]:::topic
```

Subscriber callbacks only store the latest data, so they stay short and fast. One timer makes all the decisions at a steady rate, using whatever is latest.

Nothing may wait inside a callback (`sleep`, a blocking service call). While it waits, the executor can't deliver anything else, including the answer you're waiting for, and the node is stuck in a **deadlock** (mission 6). Use `call_async` and check `future.done()` on the next tick.

### Pattern 3: one node, many robots (namespaces + parameters + launch)

Write the node once with relative names, then start it as often as you like:

```mermaid
flowchart TB
    classDef ros fill:#c8e6c9,stroke:#2e7d32,color:#1b1b1b
    classDef mine fill:#fff59d,stroke:#f57f17,stroke-width:3px,color:#1b1b1b
    classDef topic fill:#bbdefb,stroke:#1565c0,color:#1b1b1b
    LAUNCH["team.launch.py<br/>starts the same executable twice"]
    subgraph NS1["namespace /turtle1"]
        direction LR
        S1["/turtle1/scan"]:::topic --> H1(["pizza_hunter<br/>patrol_start = 0"]):::mine --> C1["/turtle1/cmd_vel"]:::topic
    end
    subgraph NS2["namespace /turtle2"]
        direction LR
        S2["/turtle2/scan"]:::topic --> H2(["pizza_hunter<br/>patrol_start = 2"]):::mine --> C2["/turtle2/cmd_vel"]:::topic
    end
    SIM(["turtlesim_plus"]):::ros
    LAUNCH -.-> NS1 & NS2
    NS1 & NS2 <--> SIM
```

Same code, two robots, no copy-paste. Real fleets work the same way (mission 7).

### Pattern 4: split big jobs into small nodes

In mission 12 one node (`crate_mover`) does everything: driving, IK, gripping, deciding. That's fine for a mission,
but real robot software splits a big job into layers, each a node with a small, clear interface:

```mermaid
flowchart TB
    classDef ros fill:#c8e6c9,stroke:#2e7d32,color:#1b1b1b
    classDef mine fill:#fff59d,stroke:#f57f17,stroke-width:3px,color:#1b1b1b
    classDef topic fill:#bbdefb,stroke:#1565c0,color:#1b1b1b
    classDef srv fill:#ffe0b2,stroke:#e65100,color:#1b1b1b
    classDef param fill:#eeeeee,stroke:#616161,color:#1b1b1b
    subgraph BEHAVIOUR["behaviour layer: WHAT to do"]
        BRAIN(["crate_brain<br/>state machine only"]):::mine
    end
    subgraph SKILLS["skill layer: HOW to do it"]
        BASE(["base_controller<br/>drive to a point (mission 5)"]):::mine
        ARM(["arm_controller<br/>world point → IK → joints (mission 10)"]):::mine
    end
    subgraph DRIVER["driver layer: the hardware"]
        SIM(["turtlesim_plus<br/>(or a real robot)"]):::ros
    end
    BRAIN --> GOAL["/turtle1/base_goal<br/>Point"]:::topic --> BASE
    BRAIN --> TGT["/turtle1/left_arm/target<br/>/turtle1/right_arm/target<br/>Point"]:::topic --> ARM
    BRAIN -. call .-> GRIP{{"/turtle1/left_gripper<br/>/turtle1/right_gripper"}}:::srv
    BASE --> CMD["/turtle1/cmd_vel"]:::topic --> SIM
    ARM --> JC["/turtle1/joint_command"]:::topic --> SIM
    GRIP -.- SIM
```

This is a design sketch: the `base_goal` and `*/target` topics don't exist until you write these nodes. To keep it readable, the diagram leaves out that all three also subscribe to `/turtle1/pose`, and that the brain reads `/mission/items` and the gripper tips.

| You gain | You pay |
|---|---|
| reuse: `base_controller` also solves missions 5, 6 and 8 | more files, more launch-file wiring |
| test parts alone: `ros2 topic pub /turtle1/base_goal ...` drives the turtle without the brain | messages add a little delay |
| replace parts: a smarter IK or a real robot, nothing else changes | you must design the interfaces (names + types) carefully |
| teamwork: one person per node | |

A rule of thumb: give a job its own node when you'd want to reuse, test, replace or restart it on its own.
On a real robot, `base_controller` would be an action, since driving takes seconds and you want feedback and cancel. That is exactly Nav2's `navigate_to_pose`.

### Pattern 5: watch the system from outside

`quest_master` is a node like any other. It never reads the simulator's memory or your code, only ROS interfaces.

```mermaid
flowchart LR
    classDef ros fill:#c8e6c9,stroke:#2e7d32,color:#1b1b1b
    classDef topic fill:#bbdefb,stroke:#1565c0,color:#1b1b1b
    classDef srv fill:#ffe0b2,stroke:#e65100,color:#1b1b1b

    SIM(["turtlesim_plus"]):::ros
    QM(["quest_master"]):::ros
    G[("the ROS graph:<br/>who publishes / subscribes what")]
    SIM --> O1["/turtle1/pose<br/>/turtle1/pizza_count<br/>/turtle1/joint_states ..."]:::topic --> QM
    SIM --> J["/judge/objects"]:::topic --> QM
    PE["/parameter_events"]:::topic --> QM
    G -. "get_publishers_info_by_topic()" .-> QM
    QM --> HUD["/hud<br/>/mission/goals<br/>/mission/items"]:::topic --> SIM
    QM -. call .-> SP{{"/spawn_pizza<br/>/spawn_turtle<br/>/clear_objects ..."}}:::srv -.- SIM
```

Monitoring, logging (`ros2 bag record`), dashboards and safety supervisors on real robots are built the same way. They're just more subscribers, so you can add them without touching the robot's code.

---

## Under the hood: how messages actually travel

ROS 2 has no central server. Each node finds the others by itself (discovery) and they talk directly, through a middleware called **DDS**:

```mermaid
flowchart LR
    subgraph P1["process 1: your node"]
        direction TB
        A1["your Python code"] --> B1["rclpy"] --> C1["rcl (C library)"] --> D1["rmw (middleware interface)"] --> E1["DDS (Fast DDS)"]
    end
    subgraph P2["process 2: turtlesim_plus"]
        direction TB
        A2["simulator code"] --> B2["rclpy"] --> C2["rcl"] --> D2["rmw"] --> E2["DDS"]
    end
    P1 <-- "discovery + messages<br/>(UDP / shared memory)" --> P2
```

In practice:

| Fact | Where you meet it |
|---|---|
| nodes in different processes, even different computers, talk the same way | run `pizza_hunter` on one laptop, the simulator on another (TEACHER.md) |
| everyone with the same `ROS_DOMAIN_ID` on the network can see each other | why each learner in a classroom needs their own number |
| a node that starts late still finds the others; there's no start-up order | start your node before or after the mission, both work |
| the `10` in `create_publisher(..., 10)` is a QoS setting: keep the last 10 messages if the reader is slow | every publisher and subscriber you write |
| message types are the contract; both sides must use the same type, or they never connect | `ros2 topic info` shows the type before you publish |

---

## Tools to see the architecture

| Question | Command |
|---|---|
| draw the whole graph | `rqt_graph` |
| which nodes exist | `ros2 node list` |
| everything one node publishes, subscribes, serves | `ros2 node info /turtlesim_plus` |
| who is on this topic | `ros2 topic info -v /turtle1/cmd_vel` |
| what's inside a message / service / action type | `ros2 interface show turtlesim/srv/Spawn` |
| a node's settings | `ros2 param list /turtle2/pizza_hunter` |
| record everything and replay it later | `ros2 bag record -a` · `ros2 bag play <folder>` |

## The building blocks, mission by mission

| Mission | New in the map |
|---|---|
| [0](missions/00-boot-camp.md) | nodes and topics exist (teleop → simulator → quest master) |
| [1](missions/01-spy.md) | you join the graph from the CLI: subscribe (`echo`), publish (`pub`) |
| [2](missions/02-steering.md) | many publishers on one topic (`cmd_vel`) |
| [3](missions/03-hotline.md) | services; a service can create new topics and services (`/spawn_turtle`) |
| [4](missions/04-first-node.md) | your own node: package → executable → node; a timer and a publisher |
| [5](missions/05-eyes.md) | subscribers; the closed loop |
| [6](missions/06-pizza-hunter.md) | service client in code, `call_async`; actions (extras) |
| [7](missions/07-team.md) | namespaces, parameters, launch files: one node, many robots |
| [8](missions/08-boss-delivery.md) | sense, think, act with several topics and services |
| [9](missions/09-arm-day.md) | the standard arm interfaces: `JointState`, `SetBool` |
| [10](missions/10-long-reach.md) | a computation pipeline inside a node (frames → IK) |
| [11](missions/11-pick-place.md) | a feedback loop through `joint_states`; waiting on events, not on time |
| [12](missions/12-boss-heavy-lifting.md) | two control loops in one node, and how you would split them (pattern 4) |
