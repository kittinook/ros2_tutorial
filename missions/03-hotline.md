# Mission 3: Service Hotline

Three pizzas sit in three far corners of the map, and driving to each one is a slog. The simulator offers services you can call to spawn turtles, teleport and eat, and with those the job takes a handful of commands.

![Mission 3: buddy has been spawned, turtle1 teleported to the top-left pizza and ate it](../docs/images/mission-3.png)

**Objectives**
- [ ] Spawn a new turtle named `buddy`
- [ ] turtle1 eats all 3 pizzas, at (1.5, 9.0), (9.0, 1.5) and (1.5, 1.5)

**Stars:** ≤ 4 min = ⭐⭐⭐ · ≤ 8 min = ⭐⭐

```bash
# Terminal 1
ros2 launch turtle_quest mission.launch.py mission:=3
```

---

## Services: ask and wait for the answer

A topic is like radio or a group chat. Messages flow and nobody replies. Sometimes you need an answer, though: "please spawn a turtle, and tell me its name." For that ROS 2 has the **service**.

```mermaid
sequenceDiagram
    participant You as you (client)
    participant Sim as turtlesim_plus (server)
    You->>Sim: request: {x: 2, y: 5, name: buddy}
    Note right of Sim: spawning...
    Sim-->>You: response: {name: buddy}
```

| | topic | service |
|---|---|---|
| shape | one-way, continuous | one question → one answer |
| get a reply? | no | yes |
| good for | data that keeps flowing (position, sensors, velocity) | one-off jobs (spawn, reset, eat) |
| examples here | `/turtle1/pose`, `/turtle1/cmd_vel` | `/spawn_turtle`, `/turtle1/eat` |

---

## Step 1: Open the phone book

```bash
ros2 service list
```

There are a lot. Some belong to the world (`/spawn_turtle`, `/spawn_pizza`, `/clear` ...) and others to each turtle (`/turtle1/eat`, `/turtle1/teleport_absolute` ...).

The ones ending in `/describe_parameters`, `/get_parameters` ... exist on every node. They're for parameters, which come up in mission 7, so skip them for now.

## Step 2: Spawn a friend

Before calling a service, find out which type (the form it uses):

```bash
ros2 service type /spawn_turtle
# turtlesim/srv/Spawn

ros2 interface show turtlesim/srv/Spawn
```

```text
float32 x
float32 y
float32 theta
string name # Optional.  A unique name will be created and returned if this is empty
---
string name
```

The `---` line splits the form in two. Above it is what you send (the **request**); below it is what you get back (the **response**).

Call it:

```bash
ros2 service call /spawn_turtle turtlesim/srv/Spawn "{x: 2.0, y: 5.0, theta: 0.0, name: 'buddy'}"
```

```text
requester: making request: turtlesim.srv.Spawn_Request(x=2.0, y=5.0, theta=0.0, name='buddy')

response:
turtlesim.srv.Spawn_Response(name='buddy')
```

A new turtle appears, and it gets the same full set of topics and services as turtle1:

```bash
ros2 topic list | grep buddy
ros2 topic pub --once /buddy/say std_msgs/msg/String "{data: 'Hi turtle1!'}"
```

## Step 3: Teleport to the pizzas

You could drive there, or you could teleport:

```bash
ros2 interface show turtlesim/srv/TeleportAbsolute
```

```text
float32 x
float32 y
float32 theta
---
```

The response is empty. This service returns nothing; the call coming back just means it's done.

Then there's the eat service, `/turtle1/eat`. Its type is `std_srvs/srv/Empty`, so you send nothing at all. The turtle eats a pizza that's inside its green cone (in front, within 2 m). With no pizza in the cone, nothing happens.

Work out how to eat all three yourself.

<details>
<summary>Solution</summary>

```bash
ros2 service call /turtle1/teleport_absolute turtlesim/srv/TeleportAbsolute "{x: 1.5, y: 9.0, theta: 0.0}"
ros2 service call /turtle1/eat std_srvs/srv/Empty

ros2 service call /turtle1/teleport_absolute turtlesim/srv/TeleportAbsolute "{x: 9.0, y: 1.5, theta: 0.0}"
ros2 service call /turtle1/eat std_srvs/srv/Empty

ros2 service call /turtle1/teleport_absolute turtlesim/srv/TeleportAbsolute "{x: 1.5, y: 1.5, theta: 0.0}"
ros2 service call /turtle1/eat std_srvs/srv/Empty
```

Teleporting right on top of a pizza always works, whichever way you face.

</details>

Once the last pizza is gone, the panel shows *Mission complete* and your stars.

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
    YOU(["ros2 service call<br/>(you, the client)"]):::mine
    SIM(["turtlesim_plus<br/>(the server)"]):::ros
    YOU -. call .-> SPAWN{{"/spawn_turtle<br/>Spawn"}}:::srv -.- SIM
    YOU -. call .-> TP{{"/turtle1/teleport_absolute<br/>TeleportAbsolute"}}:::srv -.- SIM
    YOU -. call .-> EAT{{"/turtle1/eat<br/>Empty"}}:::srv -.- SIM
    SIM -- "spawning buddy creates<br/>a whole new set" --> BUDDY
    subgraph BUDDY["new: everything under /buddy"]
        BP["/buddy/pose"]:::topic
        BE{{"/buddy/eat"}}:::srv
    end
    SIM --> PC["/turtle1/pizza_count<br/>Int64"]:::topic --> QM(["quest_master"]):::ros
    BP --> QM
```

> 🟩 existing node · 🟨 you · 🟦 topic · 🟧 service · 🟪 action · ⬜ parameter — [how to read the maps](../ARCHITECTURE.md#how-to-read-the-maps)

One node, `turtlesim_plus`, is the **server** for many services, and you were the **client** of each call. Every call is a round trip: the request goes out, the response comes back, and that's the end of it. Unlike a topic, nothing keeps flowing afterwards.

A service can also change the graph. `/spawn_turtle` created a whole new set of topics and services under `/buddy/`, and quest_master noticed `/buddy/pose` appear.

Services and topics work together. You ate with a service (`/turtle1/eat`), and the result was announced on a topic (`/turtle1/pizza_count`) that quest_master listens to.

Now that you know topics and services, it's a good time to read [ARCHITECTURE.md](../ARCHITECTURE.md) for the bigger picture of how ROS 2 systems fit together.

## Commands you now know

| Command | What it does |
|---|---|
| `ros2 service list` | which services exist (`-t` = with types) |
| `ros2 service type <service>` | the form a service uses |
| `ros2 interface show <type>` | show the form (above `---` = request, below = response) |
| `ros2 service call <service> <type> "<yaml>"` | call the service |

## Check yourself

<details>
<summary>1. What happens if you call <code>/spawn_turtle</code> with name: 'buddy' again?</summary>

Try it. Names must be unique, so the simulator picks `buddy_1` and tells you in the response. That's why services answer back: with a topic you'd never find out.

</details>

<details>
<summary>2. Should "turn the turtle" be a topic or a service? And "reset the map"?</summary>

Turning is a continuous stream of velocities, so it's a topic (`cmd_vel`).
Resetting is a one-off job where you want to know it's done, so it's a service (e.g. `/clear`).

</details>

## Extras: turtle artist

```bash
# red pen, width 5
ros2 service call /turtle1/set_pen turtlesim/srv/SetPen "{r: 255, g: 0, b: 0, width: 5, 'off': 0}"
# lift the pen (move without drawing)
ros2 service call /turtle1/set_pen turtlesim/srv/SetPen "{r: 255, g: 255, b: 255, width: 3, 'off': 1}"
# erase all lines
ros2 service call /clear std_srvs/srv/Empty
# spawn another pizza / remove a turtle
ros2 service call /spawn_pizza turtlesim_plus_interfaces/srv/GivePosition "{x: 5.0, y: 3.0}"
ros2 service call /remove_turtle turtlesim/srv/Kill "{name: 'buddy'}"
```

> Careful: `'off'` needs quotes because in YAML the word `off` (like `yes` and `no`) means the boolean `false`, not a field name.

Combine this with mission 2 to switch colours and draw rainbow circles.

---

**Previous:** [Mission 2](02-steering.md) · **Next:** [Mission 4: My First Node](04-first-node.md)
