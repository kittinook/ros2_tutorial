"""Mission definitions for Turtle Quest.

Each mission sets up the world in setup(), re-evaluates its objectives in update()
(called at 10 Hz by quest_master) and describes what to draw: goal flags, HUD hints
and warnings. Everything it knows about the world comes from TurtleWatch objects
(the turtles' public topics) and from the simulator's /judge/objects topic.
"""

import math
from typing import List, Optional, Tuple

from std_msgs.msg import String

WORLD = 10.88
DROPOFF = (WORLD - 1.5, WORLD - 1.5)  # turtlesim_plus.world.DROPOFF_ZONE_POSE
DROPOFF_RADIUS = 1.2
CENTER = (WORLD / 2, WORLD / 2)
# arm geometry, see turtlesim_plus/arms.py
ARM_BASE = {'left': 0.3, 'right': -0.3}
ARM_L1, ARM_L2 = 0.8, 0.7


class Objective:
    def __init__(self, text: str, total: Optional[int] = None):
        self.text = text
        self.total = total
        self.count = 0
        self.done = False

    def label(self) -> str:
        return f'{self.text} ({self.count}/{self.total})' if self.total else self.text

    def check(self, condition: bool):
        if condition:  # objectives are sticky: once done they stay done
            self.done = True

    def progress(self, count: int):
        self.count = max(self.count, min(count, self.total))
        self.check(self.count >= self.total)


class GoalRun:
    """An ordered list of flags that have to be touched one after another."""

    def __init__(self, points: List[Tuple[float, float]], radius: float = 0.5):
        self.points = points
        self.radius = radius
        self.reached = 0

    def update(self, *positions):
        """positions: (x, y) points that may touch the flag (turtle, gripper tips ...)"""
        while self.reached < len(self.points):
            gx, gy = self.points[self.reached]
            if not any(p is not None and math.hypot(p[0] - gx, p[1] - gy) <= self.radius for p in positions):
                break
            self.reached += 1

    @property
    def done(self) -> bool:
        return self.reached >= len(self.points)

    def remaining(self):
        return [(x, y, self.radius) for x, y in self.points[self.reached:]]


def pos(watch) -> Optional[Tuple[float, float]]:
    return None if watch.pose is None else (watch.pose.x, watch.pose.y)


def local_to_world(local, origin=CENTER, theta=0.0):
    c, s = math.cos(theta), math.sin(theta)
    return origin[0] + c * local[0] - s * local[1], origin[1] + s * local[0] + c * local[1]


class Mission:
    number = -1
    title = ''
    story: List[str] = []
    star_times = (60.0, 120.0)  # finish within [0] -> 3 stars, within [1] -> 2 stars, else 1
    main_turtle = 'turtle1'
    arms = False             # the simulator must be started with arms:=true (mission.launch.py does it)
    coding = False           # must be driven by the learner's own node (no teleop / ros2 topic pub)
                             # -- also starts the clock on the first move, not at launch, so
                             #    typing `ros2 run ...` in another terminal doesn't cost stars
    forbid_teleop = False    # CLI publishing is fine but the keyboard teleop is not
    forbid_teleport = False
    forbid_driving = False   # the turtle has to stay parked (arm-only missions)

    def __init__(self, qm):
        self.qm = qm
        self.objectives: List[Objective] = []
        self.said_seen = 0
        self.parked_at = None

    # -- override these
    def setup(self):
        pass

    def update(self):
        pass

    def goals(self):
        """Flags to draw: [(x, y, radius)]"""
        return []

    def items(self):
        """Objects the 'overhead camera' reports on /mission/items: [(x, y)]"""
        return []

    def hints(self) -> List[str]:
        return []

    # -- shared behaviour
    def new_sayings(self, watch) -> List[str]:
        """Messages the turtle said since the last call."""
        fresh = watch.said[self.said_seen:]
        self.said_seen = len(watch.said)
        return fresh

    def cheats(self) -> List[str]:
        found = []
        manual = self.qm.manual_publishers
        if self.coding and manual:
            found.append('teleop / ros2 topic pub detected')
        elif self.forbid_teleop and any(n.startswith('teleop') for n in manual):
            found.append('no teleop in this mission!')
        if self.forbid_teleport and any(w.teleported for w in self.qm.turtles.values()):
            found.append('teleport detected')
        if self.forbid_driving and self.moved_away():
            found.append('the turtle must stay parked')
        if self.qm.judge_peekers:
            found.append('peeking at /judge/objects')
        return found

    def moved_away(self) -> bool:
        w = self.qm.turtles.get(self.main_turtle)
        if w is None or w.pose is None or self.qm.elapsed() < 1.5:
            return False
        if self.parked_at is None:
            self.parked_at = (w.pose.x, w.pose.y)
        return math.hypot(w.pose.x - self.parked_at[0], w.pose.y - self.parked_at[1]) > 0.3

    def warnings(self) -> List[str]:
        found = self.cheats()
        return found + ['-> 1 star at most'] if found else []

    def star_cap(self) -> int:
        return 1 if self.cheats() else 3

    def stars(self, t: float) -> int:
        return 3 if t <= self.star_times[0] else 2 if t <= self.star_times[1] else 1

    def own_node_objective(self, what: str = 'Drive the turtle') -> Objective:
        return Objective(f'{what} with your own node')

    def grace_period(self):
        # setup() may teleport turtles; don't count that as cheating or as distance
        if self.qm.elapsed() < 1.5:
            for w in self.qm.turtles.values():
                w.teleported = False
                w.distance = 0.0
            self.parked_at = None


# ====================================================================== Part 1: the turtle

class BootCamp(Mission):
    number = 0
    title = 'Boot Camp'
    story = ['Welcome to Turtle Quest!', 'Take the turtle for a spin.']
    star_times = (30, 90)

    def setup(self):
        self.t = self.qm.watch('turtle1')
        self.run = GoalRun([(8.5, 8.5)], 0.6)
        self.move = Objective('Make the turtle move')
        self.flag = Objective('Drive to flag 1')
        self.objectives = [self.move, self.flag]

    def update(self):
        self.grace_period()
        self.move.check(self.t.distance >= 0.5)
        self.run.update(pos(self.t))
        self.flag.check(self.run.done)

    def goals(self):
        return self.run.remaining()

    def hints(self):
        return ['ros2 run turtlesim turtle_teleop_key', 'use the arrow keys in that terminal']


class Spy(Mission):
    number = 1
    title = 'Spy Turtle'
    story = ['A secret code is hidden in a topic.', 'Find it with ros2 topic ...']
    star_times = (180, 420)
    WORDS = ['PIZZA', 'TURTLE', 'HUMBLE', 'TOPIC', 'NODE', 'SHELL', 'OTTO']

    def setup(self):
        self.t = self.qm.watch('turtle1')
        self.code = f'{self.qm.rng.choice(self.WORDS)}-{self.qm.rng.randint(100, 999)}'
        self.secret_pub = self.qm.create_publisher(String, '/mission/secret_code', 10)
        self.qm.create_timer(1.0, lambda: self.secret_pub.publish(String(data=self.code)))
        self.hello = Objective('Make turtle1 say anything')
        self.secret = Objective('Make turtle1 say the secret code')
        self.rate = Objective('Make turtle1 say how many times per second /turtle1/pose is published')
        self.objectives = [self.hello, self.secret, self.rate]

    def update(self):
        for text in self.new_sayings(self.t):
            text = text.strip()
            self.hello.check(True)
            self.secret.check(self.code in text.upper())
            try:
                value = float(text.lower().replace('hz', ''))
            except ValueError:
                continue
            measured = self.t.pose_rate()
            self.rate.check(measured > 0 and abs(value - measured) <= 0.25 * measured)

    def hints(self):
        if not self.hello.done:
            return ['saying = publishing to /turtle1/say', 'ros2 topic info /turtle1/say']
        if not self.secret.done:
            return ['ros2 topic list', 'ros2 topic echo <topic>']
        return ['ros2 topic hz /turtle1/pose']


class Steering(Mission):
    number = 2
    title = 'Steering Wheel'
    story = ['The keyboard is broken!', 'Drive with ros2 topic pub only.']
    star_times = (240, 480)
    forbid_teleop = True

    def setup(self):
        self.t = self.qm.watch('turtle1')
        self.run = GoalRun([(8.5, CENTER[1]), (8.5, 8.5), (2.5, 8.5)], 0.6)
        self.flags = Objective('Touch the flags in order', total=3)
        self.circle = Objective('Drive one full circle')
        self.objectives = [self.flags, self.circle]
        self.turned = 0.0
        self.last_theta = None
        self.last_arc_time = 0.0

    def update(self):
        self.grace_period()
        self.run.update(pos(self.t))
        self.flags.progress(self.run.reached)
        pose = self.t.pose
        if pose is None:
            return
        # a circle = moving forward while turning through 360 degrees; short pauses
        # (e.g. between `--rate 1` messages) are forgiven, a real stop resets it
        now = self.qm.elapsed()
        if pose.linear_velocity > 0.05 and abs(pose.angular_velocity) > 0.05:
            if self.last_theta is not None:
                self.turned += math.atan2(math.sin(pose.theta - self.last_theta),
                                          math.cos(pose.theta - self.last_theta))
            self.last_arc_time = now
        elif now - self.last_arc_time > 1.5:
            self.turned = 0.0
        self.last_theta = pose.theta
        self.circle.check(abs(self.turned) >= 2 * math.pi)

    def goals(self):
        return self.run.remaining()

    def hints(self):
        return ['ros2 topic pub ... /turtle1/cmd_vel geometry_msgs/msg/Twist',
                'linear.x = forward, angular.z = turn left', '--once = one shot, --rate 1 = keep going']


class Hotline(Mission):
    number = 3
    title = 'Service Hotline'
    PIZZAS = [(1.5, 9.0), (9.0, 1.5), (1.5, 1.5)]
    story = ['Three pizzas, far away... call a service!',
             'At: ' + '  '.join(f'({x}, {y})' for x, y in PIZZAS)]
    star_times = (240, 480)

    def setup(self):
        self.t = self.qm.watch('turtle1')
        for x, y in self.PIZZAS:
            self.qm.spawn_pizza(x, y)
        self.buddy = Objective('Spawn a new turtle named buddy')
        self.eat = Objective('turtle1 eats pizzas', total=3)
        self.objectives = [self.buddy, self.eat]
        self.next_graph_check = 0.0

    def update(self):
        if not self.buddy.done and self.qm.elapsed() >= self.next_graph_check:
            self.next_graph_check = self.qm.elapsed() + 1.0
            self.buddy.check(self.qm.topic_exists('/buddy/pose'))
        self.eat.progress(self.t.pizza)

    def hints(self):
        return ['ros2 service list', 'ros2 service type <service>', 'ros2 interface show <type>',
                'warp: /turtle1/teleport_absolute', 'eat: /turtle1/eat']


class FirstNode(Mission):
    number = 4
    title = 'My First Node'
    story = ['Write a Python node that draws a square.', 'Flags 1 -> 2 -> 3 -> 4, in order.']
    star_times = (16, 30)
    coding = True

    def setup(self):
        self.t = self.qm.watch('turtle1')
        self.qm.teleport('turtle1', 3.0, 3.0, 0.0)
        self.qm.clear_trails()
        self.run = GoalRun([(7.0, 3.0), (7.0, 7.0), (3.0, 7.0), (3.0, 3.0)], 0.5)
        self.flags = Objective('Draw a square through the flags', total=4)
        self.own = self.own_node_objective()
        self.objectives = [self.flags, self.own]

    def update(self):
        self.grace_period()
        if self.qm.elapsed() < 1.5:
            return  # the setup teleport may still be in flight
        self.run.update(pos(self.t))
        self.flags.progress(self.run.reached)
        self.own.check(bool(self.qm.own_publishers))

    def goals(self):
        return self.run.remaining()

    def hints(self):
        return ['start: (3, 3) facing right', 'sides are 4 m long', 'ros2 run my_turtle square']


class Eyes(Mission):
    number = 5
    title = 'Turtle Eyes'
    story = ['The flags move every time!', 'Read them from /mission/goals.']
    star_times = (20, 40)
    coding = True

    def setup(self):
        self.t = self.qm.watch('turtle1')
        points = []
        last = CENTER
        for _ in range(5):
            p = self.qm.random_point(1.0, avoid=[last, CENTER] + points, min_gap=2.5)
            points.append(p)
            last = p
        self.run = GoalRun(points, 0.5)
        self.flags = Objective('Touch the flags in order', total=5)
        self.own = self.own_node_objective()
        self.objectives = [self.flags, self.own]

    def update(self):
        self.grace_period()
        self.run.update(pos(self.t))
        self.flags.progress(self.run.reached)
        self.own.check(bool(self.qm.own_publishers))

    def goals(self):
        return self.run.remaining()

    def hints(self):
        return ['subscribe /turtle1/pose + /mission/goals', 'ros2 run my_turtle go_to_goal']


class PizzaHunter(Mission):
    number = 6
    title = 'Pizza Hunter'
    story = ['No coordinates this time! Use the scanner.', 'Found one? Call /turtle1/eat.']
    star_times = (15, 40)
    coding = True
    forbid_teleport = True

    def setup(self):
        self.t = self.qm.watch('turtle1')
        spots = []
        for _ in range(5):
            spots.append(self.qm.random_point(0.8, avoid=[CENTER] + spots, min_gap=1.5))
            self.qm.spawn_pizza(*spots[-1])
        self.eat = Objective('Eat pizzas', total=5)
        self.own = self.own_node_objective()
        self.objectives = [self.eat, self.own]

    def update(self):
        self.grace_period()
        self.eat.progress(self.t.pizza)
        self.own.check(bool(self.qm.own_publishers))

    def hints(self):
        return ['ros2 topic echo /turtle1/scan', 'ros2 run my_turtle pizza_hunter']


class Team(Mission):
    number = 7
    title = 'Turtle Team'
    story = ['Same node, two turtles, one launch file!', 'turtle1 + turtle2 hunt together.']
    star_times = (40, 90)
    coding = True
    forbid_teleport = True
    TARGET = 10
    ON_MAP = 6

    def setup(self):
        self.t1 = self.qm.watch('turtle1')
        self.qm.spawn_turtle('turtle2', 2.0, 2.0, 0.0)
        self.t2 = self.qm.watch('turtle2')
        self.spawned = 0
        self.restock()
        self.ns = Objective('Run nodes in /turtle1 and /turtle2')
        self.param = Objective('Change a parameter while running')
        self.each = Objective('Each turtle eats >= 3')
        self.total = Objective('Pizzas eaten', total=self.TARGET)
        self.objectives = [self.ns, self.param, self.each, self.total]
        self.next_graph_check = 0.0

    def eaten(self) -> int:
        return self.t1.pizza + self.t2.pizza

    def restock(self):
        # keep pizzas on the map until done, so a greedy turtle can't starve its teammate
        while self.spawned - self.eaten() < self.ON_MAP:
            avoid = [CENTER, (2.0, 2.0)]
            self.qm.spawn_pizza(*self.qm.random_point(0.8, avoid=avoid, min_gap=1.5))
            self.spawned += 1

    def update(self):
        self.grace_period()
        if self.qm.elapsed() >= self.next_graph_check:
            self.next_graph_check = self.qm.elapsed() + 1.0
            spaces = self.qm.node_namespaces()
            self.ns.check('/turtle1' in spaces and '/turtle2' in spaces)
        self.param.check(any(n.startswith(('/turtle1/', '/turtle2/')) for n in self.qm.changed_param_nodes))
        self.each.check(self.t1.pizza >= 3 and self.t2.pizza >= 3)
        self.total.progress(self.eaten())
        if not (self.each.done and self.total.done):
            self.restock()

    def hints(self):
        return ['ros2 launch my_turtle team.launch.py', 'ros2 param set /turtle1/pizza_hunter ...']


class Delivery(Mission):
    number = 8
    title = 'Boss: Turtle Express'
    story = ['Find a parcel -> pickup -> carry it', 'to DROP-OFF -> dropoff. Three times.']
    star_times = (24, 60)
    coding = True
    forbid_teleport = True

    def setup(self):
        self.t = self.qm.watch('turtle1')
        spots = []
        for _ in range(3):
            spots.append(self.qm.random_point(1.0, avoid=[CENTER, DROPOFF] + spots, min_gap=2.5))
            self.qm.spawn_parcel(*spots[-1])
        self.deliver = Objective('Parcels delivered', total=3)
        self.own = self.own_node_objective()
        self.objectives = [self.deliver, self.own]

    def update(self):
        self.grace_period()
        self.deliver.progress(self.t.parcel)
        self.own.check(bool(self.qm.own_publishers))

    def hints(self):
        state = 'carrying a parcel' if self.t.carrying else 'not carrying anything'
        return [state, f'DROP-OFF is at ({DROPOFF[0]:.2f}, {DROPOFF[1]:.2f})']


# ====================================================================== Part 2: the arms

def reachable_point(rng, side: str, r_min: float, r_max: float):
    """Random point (turtle frame) the given arm can reach, on its own side of the body."""
    r = rng.uniform(r_min, r_max)
    phi = rng.uniform(-0.2, 1.5) if side == 'left' else rng.uniform(-1.5, 0.2)
    return (r * math.cos(phi), ARM_BASE[side] + r * math.sin(phi))


class ArmDay(Mission):
    number = 9
    title = 'Arm Day'
    story = ['Your turtle grew two arms!', 'Move them with ros2 topic pub (JointState).']
    star_times = (240, 480)
    arms = True
    forbid_driving = True
    FLAG_LEFT = (1.2, 0.9)    # turtle frame
    FLAG_RIGHT = (1.2, -0.9)
    PIZZA = (1.3, 0.0)

    def setup(self):
        self.t = self.qm.watch('turtle1')
        self.left_flag = local_to_world(self.FLAG_LEFT)
        self.right_flag = local_to_world(self.FLAG_RIGHT)
        self.qm.spawn_pizza(*local_to_world(self.PIZZA))
        self.left = Objective('Touch flag 1 with the LEFT gripper')
        self.right = Objective('Touch flag 2 with the RIGHT gripper')
        self.grab = Objective('Grab the pizza with a gripper')
        self.objectives = [self.left, self.right, self.grab]

    def touching(self, side: str, flag) -> bool:
        tip = self.t.tips.get(side)
        return tip is not None and math.hypot(tip[0] - flag[0], tip[1] - flag[1]) <= 0.3

    def update(self):
        self.grace_period()
        self.left.check(self.touching('left', self.left_flag))
        self.right.check(self.touching('right', self.right_flag))
        self.grab.check('Pizza' in self.t.holding.values())

    def goals(self):
        flags = []
        if not self.left.done:
            flags.append((*self.left_flag, 0.3))
        if not self.right.done:
            flags.append((*self.right_flag, 0.3))
        return flags

    def hints(self):
        if not (self.left.done and self.right.done):
            return ['topic: /turtle1/joint_command', 'type: sensor_msgs/msg/JointState',
                    'watch: /turtle1/left_arm/tip']
        return ['service: /turtle1/left_gripper', 'type: std_srvs/srv/SetBool']


class LongReach(Mission):
    number = 10
    title = 'Long Reach'
    story = ['Flags pop up around the turtle.', 'Solve the inverse kinematics to touch them!']
    star_times = (6, 20)
    arms = True
    coding = True
    forbid_driving = True
    COUNT = 6

    def setup(self):
        self.t = self.qm.watch('turtle1')
        points = []
        for i in range(self.COUNT):
            side = 'left' if i % 2 == 0 else 'right'
            if self.qm.rng.random() < 0.3:
                side = 'right' if side == 'left' else 'left'
            for _ in range(100):
                p = local_to_world(reachable_point(self.qm.rng, side, 0.6, 1.4))
                if all(math.hypot(p[0] - q[0], p[1] - q[1]) > 0.5 for q in points):
                    break
            points.append(p)
        self.run = GoalRun(points, 0.25)
        self.flags = Objective('Touch the flags in order', total=self.COUNT)
        self.own = self.own_node_objective('Move the arms')
        self.objectives = [self.flags, self.own]

    def update(self):
        self.grace_period()
        self.run.update(*self.t.tips.values())
        self.flags.progress(self.run.reached)
        self.own.check(bool(self.qm.own_publishers))

    def goals(self):
        return self.run.remaining()

    def hints(self):
        return ['flag -> turtle frame -> shoulder frame -> IK', 'ros2 run my_turtle arm_reach']


class PickPlace(Mission):
    number = 11
    title = 'Pick & Place'
    story = ['Serve the pizzas onto the plate (the ring).', 'Pizza positions: /mission/items']
    star_times = (8, 20)
    arms = True
    coding = True
    forbid_driving = True
    PLATE = (1.25, 0.0)   # turtle frame
    PLATE_RADIUS = 0.45
    COUNT = 3

    def setup(self):
        self.t = self.qm.watch('turtle1')
        self.plate = local_to_world(self.PLATE)
        spots = []
        for i in range(self.COUNT):
            side = 'left' if i % 2 == 0 else 'right'
            for _ in range(100):
                p = local_to_world(reachable_point(self.qm.rng, side, 0.8, 1.4))
                if math.hypot(p[0] - self.plate[0], p[1] - self.plate[1]) > 1.0 and \
                        all(math.hypot(p[0] - q[0], p[1] - q[1]) > 0.7 for q in spots):
                    break
            spots.append(p)
            self.qm.spawn_pizza(*p)
        self.served = Objective('Pizzas on the plate', total=self.COUNT)
        self.own = self.own_node_objective('Move the arms')
        self.objectives = [self.served, self.own]

    def on_plate(self, o) -> bool:
        return not o.held_by and math.hypot(o.x - self.plate[0], o.y - self.plate[1]) <= self.PLATE_RADIUS

    def update(self):
        self.grace_period()
        pizzas = [o for o in self.qm.objects if o.type == 'Pizza']
        self.served.progress(sum(self.on_plate(o) for o in pizzas))
        self.own.check(bool(self.qm.own_publishers))

    def goals(self):
        return [(*self.plate, self.PLATE_RADIUS)]

    def items(self):
        return [(o.x, o.y) for o in self.qm.objects if o.type == 'Pizza' and not self.on_plate(o)]

    def warnings(self):
        extra = ['a pizza was eaten -- restart the mission'] if self.t.pizza > 0 else []
        return super().warnings() + extra

    def hints(self):
        return ['grab: /turtle1/<side>_gripper (SetBool)', 'ros2 run my_turtle pick_place']


class HeavyLifting(Mission):
    number = 12
    title = 'Boss: Heavy Lifting'
    story = ['Crates are too heavy for one arm.', 'Grab with BOTH, carry to DROP-OFF, let go.']
    star_times = (25, 60)
    arms = True
    coding = True
    forbid_teleport = True
    COUNT = 2

    def setup(self):
        self.t = self.qm.watch('turtle1')
        spots = []
        for _ in range(self.COUNT):
            spots.append(self.qm.random_point(1.6, avoid=[CENTER, DROPOFF] + spots, min_gap=2.5))
            self.qm.spawn_crate(*spots[-1])
        self.delivered = set()
        self.deliver = Objective('Crates delivered', total=self.COUNT)
        self.own = self.own_node_objective()
        self.objectives = [self.deliver, self.own]

    def update(self):
        self.grace_period()
        for o in self.qm.objects:
            if o.type == 'Crate' and not o.held_by and \
                    math.hypot(o.x - DROPOFF[0], o.y - DROPOFF[1]) <= DROPOFF_RADIUS:
                self.delivered.add(o.name)
        self.deliver.progress(len(self.delivered))
        self.own.check(bool(self.qm.own_publishers))

    def items(self):
        return [(o.x, o.y) for o in self.qm.objects if o.type == 'Crate' and o.name not in self.delivered]

    def hints(self):
        held = sorted(v for v in self.t.holding.values() if v)
        return [f'holding: {", ".join(held) or "nothing"}', 'crate items: /mission/items',
                f'DROP-OFF is at ({DROPOFF[0]:.2f}, {DROPOFF[1]:.2f})']


MISSIONS = {m.number: m for m in
            (BootCamp, Spy, Steering, Hotline, FirstNode, Eyes, PizzaHunter, Team, Delivery,
             ArmDay, LongReach, PickPlace, HeavyLifting)}
