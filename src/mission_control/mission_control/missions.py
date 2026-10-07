"""Mission definitions for Mars Rover Academy.

Each mission builds its world in setup(), re-evaluates its objectives in update()
(called at 10 Hz by mission_control) and describes what to draw: beacons, hints
and warnings. Everything it knows comes from RoverWatch objects (the rovers' public
topics) and from the simulator's referee topic.
"""

import math
from typing import Dict, List, Optional, Tuple

from std_msgs.msg import String

WORLD = 20.0
LANDER = (3.0, 3.0)        # mars_sim.world.LANDER
LANDER_RADIUS = 1.5
# arm geometry, see mars_sim/world.py
SHOULDER = {'left': (0.4, 0.25), 'right': (0.4, -0.25)}
L1, L2 = 0.6, 0.5


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


class BeaconRun:
    """An ordered list of beacons that have to be reached one after another."""

    def __init__(self, points: List[Tuple[float, float]], radius: float = 0.6):
        self.points = points
        self.radius = radius
        self.reached = 0

    def update(self, *positions):
        """positions: (x, y) points that may reach the beacon (rover centres, gripper tips ...)"""
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


class Mission:
    number = -1
    title = ''
    story: List[str] = []
    star_times = (60.0, 120.0)  # finish within [0] -> 3 stars, within [1] -> 2 stars, else 1
    main_rover = 'rover1'
    sim_params: Dict[str, object] = {}  # mars_sim parameters this mission needs (set by mission.launch.py)
    coding = False           # must be driven by the learner's own node (no teleop / ros2 topic pub)
                             # -- also starts the clock on the first move, not at launch, so
                             #    typing `ros2 run ...` in another terminal doesn't cost stars
    forbid_teleop = False    # ros2 topic pub is fine but the keyboard teleop is not
    forbid_teleport = False
    forbid_driving = False   # the rover has to stay parked (arm-only missions)

    def __init__(self, mc):
        self.mc = mc
        self.objectives: List[Objective] = []
        self.said_seen = 0
        self.teleport_baseline: Dict[str, int] = {}
        self.parked_at: Optional[Tuple[float, float]] = None

    # -- override these
    def setup(self):
        pass

    def update(self):
        pass

    def goals(self):
        """Beacons to draw: [(x, y, radius)]"""
        return []

    def items(self):
        """Objects the orbiter reports on /mission/items: [(x, y)]"""
        return []

    def hints(self) -> List[str]:
        return []

    # -- shared behaviour
    def scenery(self, rocks=(), sand=(), craters=(), landmarks=()):
        """rocks/sand/craters: (x, y) or (x, y, radius); landmarks: (name, x, y)"""
        for kind, items in (('sand', sand), ('crater', craters), ('rock', rocks)):
            for item in items:
                self.mc.place(kind, *item)
        for name, x, y in landmarks:
            self.mc.place('landmark', x, y, id=name)

    def random_points(self, n: int, avoid=(), gap: float = 2.0, margin: float = 1.5,
                      route=(), route_gap: float = 0.0) -> List[Tuple[float, float]]:
        """n random points inside the map, at least gap apart, away from the lander and avoid,
        and at least route_gap from every leg of route (a closed loop of points)."""
        taken = [LANDER] + list(avoid)
        legs = list(zip(route, list(route[1:]) + list(route[:1])))
        points = []
        for _ in range(n):
            for _ in range(500):
                p = (round(self.mc.rng.uniform(margin, WORLD - margin), 2), round(self.mc.rng.uniform(margin, WORLD - margin), 2))
                if (all(math.hypot(p[0] - a[0], p[1] - a[1]) >= gap for a in taken)
                        and all(segment_distance(p, a, b) >= route_gap for a, b in legs)):
                    points.append(p)
                    taken.append(p)
                    break   # no free spot left: return fewer points rather than a bad one
        return points

    def new_messages(self, watch) -> List[str]:
        """What the rover sent on its radio since the last call."""
        fresh = watch.said[self.said_seen:]
        self.said_seen = len(watch.said)
        return fresh

    def teleported(self) -> bool:
        if self.mc.since_start() < 1.5:   # setup() may teleport rovers itself
            self.teleport_baseline = {n: w.teleports() for n, w in self.mc.rovers.items()}
            return False
        return any(w.teleports() > self.teleport_baseline.get(n, 0) for n, w in self.mc.rovers.items())

    def cheats(self) -> List[str]:
        found = []
        manual = self.mc.manual_publishers
        if self.coding and manual:
            found.append('teleop / ros2 topic pub detected')
        elif self.forbid_teleop and any(n.startswith('teleop') for n in manual):
            found.append('no teleop in this mission!')
        if self.forbid_teleport and self.teleported():
            found.append('teleport detected')
        if self.forbid_driving and self.moved_away():
            found.append('the rover must stay parked')
        if self.mc.judge_peekers:
            found.append('peeking at /judge/state')
        return found

    def moved_away(self) -> bool:
        w = self.mc.rovers.get(self.main_rover)
        if w is None or w.pos is None or self.mc.since_start() < 2.0:   # setup() may still be moving it
            self.parked_at = None
            return False
        if self.parked_at is None:
            self.parked_at = w.pos
        return math.hypot(w.x - self.parked_at[0], w.y - self.parked_at[1]) > 0.3

    def warnings(self) -> List[str]:
        found = self.cheats()
        return found + ['-> 1 star at most'] if found else []

    def star_cap(self) -> int:
        return 1 if self.cheats() else 3

    def stars(self, t: float) -> int:
        return 3 if t <= self.star_times[0] else 2 if t <= self.star_times[1] else 1

    def failure(self) -> Optional[str]:
        """Why the mission can't be finished any more, or None."""
        for w in self.mc.rovers.values():
            if w.battery is not None and w.battery <= 0.0:
                return f'{w.name} ran out of battery.'
            if w.drill_broken():
                return f'{w.name} broke its drill bit: it got hotter than 80 C.'
        return None

    def own_node_objective(self, what: str = 'Drive the rover') -> Objective:
        return Objective(f'{what} with your own node')

    def own_node_driving(self) -> bool:
        return bool(self.mc.own_publishers)


def pos(watch):
    return watch.pos


def segment_distance(p, a, b) -> float:
    """Distance from point p to the line segment a-b."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    length2 = dx * dx + dy * dy
    s = 0.0 if length2 == 0 else max(0.0, min(1.0, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / length2))
    return math.hypot(p[0] - a[0] - s * dx, p[1] - a[1] - s * dy)


# ====================================================================== Part 1: the rover

class Landing(Mission):
    number = 0
    title = 'Landing'
    story = ['Welcome to Mars!', 'Drive rover1 off the lander.']
    star_times = (60, 150)
    BEACON = (9.0, 7.0)

    def setup(self):
        self.r = self.mc.watch('rover1')
        self.scenery(rocks=[(6.0, 9.5), (12.5, 4.0, 0.7), (15.0, 12.0), (8.0, 15.0, 0.8), (17.0, 17.5)],
                     sand=[(13.0, 15.0, 2.5)], craters=[(15.5, 7.5, 1.8)])
        self.run = BeaconRun([self.BEACON], 0.8)
        self.move = Objective('Make the rover move')
        self.beacon = Objective('Drive to beacon 1')
        self.objectives = [self.move, self.beacon]

    def update(self):
        self.move.check(self.r.distance >= 0.5)
        self.run.update(pos(self.r))
        self.beacon.check(self.run.done)

    def goals(self):
        return self.run.remaining()

    def hints(self):
        return ['ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -r cmd_vel:=/rover1/cmd_vel',
                'i = forward, j / l = turn, k = stop']


class Telemetry(Mission):
    number = 1
    title = 'Telemetry'
    story = ['Earth is calling, but nobody told you where.', 'Find the message with ros2 topic ...']
    star_times = (180, 420)
    WORDS = ['PHOBOS', 'DEIMOS', 'OLYMPUS', 'GALE', 'JEZERO', 'THARSIS', 'HELLAS']

    def setup(self):
        self.r = self.mc.watch('rover1')
        self.scenery(rocks=[(8.0, 6.0), (11.0, 13.0, 0.8), (16.0, 5.0)], sand=[(14.0, 15.0, 2.5)],
                     craters=[(7.0, 14.0, 1.8)])
        self.code = f'{self.mc.rng.choice(self.WORDS)}-{self.mc.rng.randint(100, 999)}'
        self.uplink_pub = self.mc.create_publisher(String, '/earth/uplink', 10)
        text = f'Earth to rover1: please confirm code {self.code} on your radio.'
        self.mc.create_timer(1.0, lambda: self.uplink_pub.publish(String(data=text)))
        self.hello = Objective('Send anything on rover1\'s radio')
        self.confirm = Objective('Confirm the code from Earth on the radio')
        self.rate = Objective('Radio how many times per second /rover1/odom is published')
        self.objectives = [self.hello, self.confirm, self.rate]

    def update(self):
        for text in self.new_messages(self.r):
            text = text.strip()
            self.hello.check(True)
            self.confirm.check(self.code in text.upper())
            try:
                value = float(text.lower().replace('hz', ''))
            except ValueError:
                continue
            measured = self.r.odom_rate()
            self.rate.check(measured > 0 and abs(value - measured) <= 0.1 * measured)

    def hints(self):
        if not self.hello.done:
            return ['the radio is the topic /rover1/radio', 'ros2 topic info /rover1/radio']
        if not self.confirm.done:
            return ['ros2 topic list', 'ros2 topic echo <topic>']
        return ['ros2 topic hz /rover1/odom']


class ManualDrive(Mission):
    number = 2
    title = 'Manual Drive'
    story = ['The keyboard link is down!', 'Drive with ros2 topic pub only.']
    star_times = (240, 480)
    forbid_teleop = True
    BEACONS = [(8.0, 3.0), (8.0, 8.0), (4.0, 8.0)]
    CRATER = (4.0, 6.0)

    def setup(self):
        self.r = self.mc.watch('rover1')
        self.scenery(rocks=[(11.0, 5.0), (12.0, 12.0, 0.8), (16.0, 4.0), (7.0, 15.0), (17.0, 16.0, 0.7)],
                     sand=[(15.0, 9.0, 2.5)], craters=[(*self.CRATER, 0.9)])
        self.run = BeaconRun(self.BEACONS, 0.6)
        self.beacons = Objective('Reach the beacons in order', total=3)
        self.circle = Objective('Drive one full circle around the crater')
        self.objectives = [self.beacons, self.circle]
        self.turned = 0.0
        self.last_yaw = None
        self.last_arc_time = 0.0

    def update(self):
        self.run.update(pos(self.r))
        self.beacons.progress(self.run.reached)
        if self.r.pos is None:
            return
        # a circle = moving forward while turning through 360 degrees; short pauses
        # (between `--rate 1` messages) are forgiven, a real stop resets it
        now = self.mc.since_start()
        if self.r.v > 0.05 and abs(self.r.w) > 0.05:
            if self.last_yaw is not None:
                self.turned += math.atan2(math.sin(self.r.yaw - self.last_yaw), math.cos(self.r.yaw - self.last_yaw))
            self.last_arc_time = now
        elif now - self.last_arc_time > 1.5:
            self.turned = 0.0
        self.last_yaw = self.r.yaw
        around = self.r.distance_to(*self.CRATER) < 3.5
        self.circle.check(abs(self.turned) >= 2 * math.pi and around)

    def goals(self):
        return self.run.remaining()

    def hints(self):
        return ['ros2 topic pub ... /rover1/cmd_vel geometry_msgs/msg/Twist',
                'one message keeps the rover going for 1 s',
                '--rate 1 --times 5 = five messages, one per second']


class Services(Mission):
    number = 3
    title = 'Mission Control'
    LANDMARKS = [('Olympus Rock', 16.0, 15.0), ('Twin Peaks', 15.0, 5.0), ('Face Rock', 5.0, 16.0)]
    story = ['Earth wants photos of three landmarks.', 'Services can do things topics can\'t.']
    star_times = (300, 600)

    def setup(self):
        self.r = self.mc.watch('rover1')
        self.scenery(rocks=[(9.0, 9.0, 0.8), (11.0, 3.0), (3.5, 11.0)], sand=[(11.0, 15.0, 2.2)],
                     craters=[(9.0, 13.0, 1.4)], landmarks=self.LANDMARKS)
        self.scout = Objective('Spawn a second rover named scout')
        self.photos = Objective('Photograph the landmarks', total=3)
        self.objectives = [self.scout, self.photos]
        self.next_graph_check = 0.0

    def update(self):
        if not self.scout.done and self.mc.since_start() >= self.next_graph_check:
            self.next_graph_check = self.mc.since_start() + 1.0
            self.scout.check(self.mc.topic_exists('/scout/odom'))
        names = {name for name, _, _ in self.LANDMARKS}
        seen = {m.split('photo of ', 1)[1] for m in self.mc.photos if 'photo of ' in m}
        self.photos.progress(len(seen & names))

    def hints(self):
        return ['ros2 service list', 'ros2 service type <service>', 'ros2 interface show <type>',
                'camera: /rover1/take_photo', 'move: /rover1/teleport']


class SurveySquare(Mission):
    number = 4
    title = 'Survey Square'
    story = ['Write a Python node that drives a square.', 'Beacons 1 -> 2 -> 3 -> 4, in order.']
    star_times = (30, 45)
    coding = True
    forbid_teleport = True

    def setup(self):
        self.r = self.mc.watch('rover1')
        self.scenery(rocks=[(10.5, 5.0), (12.0, 13.0, 0.8), (16.0, 6.0), (6.0, 14.0), (16.5, 16.0, 0.7)],
                     sand=[(14.0, 10.0, 2.5)], craters=[(5.0, 5.0, 0.9)])
        self.run = BeaconRun([(7.0, 3.0), (7.0, 7.0), (3.0, 7.0), (3.0, 3.0)], 0.6)
        self.beacons = Objective('Drive a square through the beacons', total=4)
        self.own = self.own_node_objective()
        self.objectives = [self.beacons, self.own]

    def update(self):
        if self.mc.clock_start is None:
            return   # parked on beacon 4 at the start: only count it after leaving
        self.run.update(pos(self.r))
        self.beacons.progress(self.run.reached)
        self.own.check(self.own_node_driving())

    def goals(self):
        return self.run.remaining()

    def hints(self):
        return ['ros2 pkg create --build-type ament_python my_rover ...',
                'a timer + a publisher on /rover1/cmd_vel', 'ros2 run my_rover square']


# Patrol route of the sample hunter (the mission guides use the same points), and rocks keep clear of it.
PATROL = [(5.0, 5.0), (15.0, 5.0), (15.0, 10.0), (5.0, 10.0), (5.0, 15.0), (15.0, 15.0)]
ROUTE = [LANDER] + PATROL
SAMPLE_MARGIN = 3.0    # samples stay in 3..17, which the camera sweeps from the patrol route


class Waypoints(Mission):
    number = 5
    title = 'Waypoints'
    story = ['Five beacons, somewhere on the map.', 'Watch out: the rover slips on sand.']
    star_times = (55, 90)
    coding = True
    forbid_teleport = True

    def setup(self):
        self.r = self.mc.watch('rover1')
        points = self.random_points(5, gap=4.0)
        sand = []
        for a, b in zip([LANDER] + points[:-1], points):   # sand on most legs, so open loop misses
            if self.mc.rng.random() < 0.8:
                f = self.mc.rng.uniform(0.35, 0.65)
                sand.append((a[0] + f * (b[0] - a[0]), a[1] + f * (b[1] - a[1]), self.mc.rng.uniform(1.4, 2.0)))
        self.scenery(sand=sand, craters=[c + (1.0,) for c in self.random_points(2, avoid=points, gap=3.0)])
        self.run = BeaconRun(points, 0.6)
        # star times scale with the length of this run's route
        length = sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip([LANDER] + points[:-1], points))
        self.star_times = (round(1.3 * length + 8), round(2.0 * length + 20))
        self.mc.get_logger().info(f'Route length {length:.1f} m: 3 stars within {self.star_times[0]} s')
        self.beacons = Objective('Reach the beacons in order', total=5)
        self.own = self.own_node_objective()
        self.objectives = [self.beacons, self.own]

    def update(self):
        self.run.update(pos(self.r))
        self.beacons.progress(self.run.reached)
        self.own.check(self.own_node_driving())

    def goals(self):
        return self.run.remaining()

    def hints(self):
        return ['the beacons: /mission/goals', 'where am I: /rover1/odom', 'turn the quaternion into a yaw first']


class SampleHunter(Mission):
    number = 6
    title = 'Sample Hunter'
    story = ['Blue crystals are scattered around.', 'Find them with the camera, don\'t hit rocks.']
    star_times = (90, 180)
    coding = True
    forbid_teleport = True
    SAMPLES = 6
    GOAL = 5

    def setup(self):
        self.r = self.mc.watch('rover1')
        rocks = self.random_points(9, gap=2.2, route=ROUTE, route_gap=1.8)
        samples = self.random_points(self.SAMPLES, avoid=rocks, gap=2.0, margin=SAMPLE_MARGIN)
        self.scenery(rocks=[r + (self.mc.rng.uniform(0.4, 0.7),) for r in rocks],
                     sand=[s + (1.6,) for s in self.random_points(2, avoid=rocks + samples, gap=2.5)])
        for x, y in samples:
            self.mc.place('sample', x, y)
        self.collect = Objective('Collect samples', total=self.GOAL)
        self.own = self.own_node_objective()
        self.objectives = [self.collect, self.own]

    def update(self):
        self.collect.progress(self.r.onboard)
        self.own.check(self.own_node_driving())

    def warnings(self):
        found = super().warnings()
        if self.r.bumps:
            found.append(f'bumped into something {self.r.bumps}x -> 2 stars at most')
        return found

    def star_cap(self):
        return min(super().star_cap(), 2 if self.r.bumps else 3)

    def hints(self):
        return ['what the camera sees: /rover1/camera/detections', 'what is close: /rover1/scan',
                'pick it up: /rover1/collect (std_srvs/srv/Trigger)']


class RoverFleet(Mission):
    number = 7
    title = 'Rover Fleet'
    story = ['A second rover has landed.', 'Same code, two rovers.']
    star_times = (90, 180)
    coding = True
    forbid_teleport = True
    SAMPLES = 14

    def setup(self):
        self.r1 = self.mc.watch('rover1')
        self.r2 = self.mc.watch('rover2')
        self.mc.spawn_rover('rover2', LANDER[0], LANDER[1] + 1.2, 0.0)
        rocks = self.random_points(8, gap=2.2, route=ROUTE, route_gap=1.8)
        samples = self.random_points(self.SAMPLES, avoid=rocks, gap=1.8, margin=SAMPLE_MARGIN)
        self.scenery(rocks=[r + (self.mc.rng.uniform(0.4, 0.7),) for r in rocks])
        for x, y in samples:
            self.mc.place('sample', x, y)
        self.namespaces = Objective('Run nodes in the /rover1 and /rover2 namespaces')
        self.param = Objective('Change a parameter while the node is running')
        self.each = Objective('Each rover collects at least 3 samples')
        self.total = Objective('Samples collected in total', total=10)
        self.objectives = [self.namespaces, self.param, self.each, self.total]
        self.next_graph_check = 0.0

    def update(self):
        if not self.namespaces.done and self.mc.since_start() >= self.next_graph_check:
            self.next_graph_check = self.mc.since_start() + 1.0
            mine = {p.rsplit('/', 1)[0] for p in self.mc.own_publishers}
            self.namespaces.check({'/rover1', '/rover2'} <= mine)
        self.param.check(any(n.startswith(('/rover1/', '/rover2/')) for n in self.mc.changed_param_nodes))
        self.each.check(self.r1.onboard >= 3 and self.r2.onboard >= 3)
        self.total.progress(self.r1.onboard + self.r2.onboard)

    def hints(self):
        return ['ros2 run my_rover sample_hunter --ros-args -r __ns:=/rover2', 'ros2 param set <node> max_speed 0.6',
                'ros2 launch my_rover fleet.launch.py']


class PowerCrisis(Mission):
    number = 8
    title = 'Boss: Power Crisis'
    story = ['Dust on the solar panels: the battery is low', 'and drains fast. Bring 6 samples home.']
    star_times = (170, 340)
    coding = True
    forbid_teleport = True
    sim_params = {'battery_start': 0.35, 'battery_drain': 4.0}
    SAMPLES = 9
    GOAL = 6

    def setup(self):
        self.r = self.mc.watch('rover1')
        rocks = self.random_points(8, gap=2.2, route=ROUTE, route_gap=1.8)
        far = [p for p in self.random_points(30, avoid=rocks, gap=1.8, margin=SAMPLE_MARGIN) if math.hypot(p[0] - LANDER[0], p[1] - LANDER[1]) > 6.0]
        self.scenery(rocks=[r + (self.mc.rng.uniform(0.4, 0.7),) for r in rocks])
        for x, y in far[:self.SAMPLES]:
            self.mc.place('sample', x, y)
        self.delivered = Objective('Samples delivered to the lander', total=self.GOAL)
        self.own = self.own_node_objective()
        self.objectives = [self.delivered, self.own]

    def update(self):
        self.delivered.progress(self.mc.lander_samples)
        self.own.check(self.own_node_driving())

    def hints(self):
        return ['battery: /rover1/battery (percentage 0-1)', 'charge: park on the lander', 'deliver: /rover1/unload']


# ====================================================================== Part 2: the arms

def rover_to_map(pose, x: float, y: float) -> Tuple[float, float]:
    """A point in the rover frame -> the map frame, for a rover at pose (x, y, yaw)."""
    c, s = math.cos(pose[2]), math.sin(pose[2])
    return round(pose[0] + c * x - s * y, 3), round(pose[1] + s * x + c * y, 3)


ARM_PARAMS = {'arms': True}


class ArmCheck(Mission):
    number = 9
    title = 'Arm Check'
    story = ['The rover unfolds its two arms.', 'Stay parked: only the arms move.']
    star_times = (240, 480)
    forbid_driving = True
    sim_params = {**ARM_PARAMS, 'view_zoom': 4.0, 'view_center_x': 4.3, 'view_center_y': 3.0}
    POSE = (3.0, 3.0, 0.0)              # rover1 starts here, on the lander

    def setup(self):
        self.r = self.mc.watch('rover1')
        self.left_target = rover_to_map(self.POSE, 1.0, 0.75)
        self.right_target = rover_to_map(self.POSE, 1.0, -0.75)
        self.mc.place('sample', *rover_to_map(self.POSE, 1.3, 0.0))
        self.left = Objective('Touch beacon 1 with the LEFT gripper')
        self.right = Objective('Touch beacon 2 with the RIGHT gripper')
        self.grab = Objective('Pick up the sample with a gripper')
        self.objectives = [self.left, self.right, self.grab]

    def touching(self, side: str, target) -> bool:
        tip = self.r.tip(side)
        return tip is not None and math.hypot(tip[0] - target[0], tip[1] - target[1]) <= 0.15

    def update(self):
        self.left.check(self.touching('left', self.left_target))
        self.right.check(self.touching('right', self.right_target))
        self.grab.check(any(h.startswith('sample') for h in self.r.holding.values()))

    def goals(self):
        return [(*self.left_target, 0.15), (*self.right_target, 0.15)]

    def hints(self):
        return ['ros2 topic echo /rover1/joint_states',
                'move: /rover1/arm/joint_command (sensor_msgs/msg/JointState)',
                'where is it: ros2 run tf2_ros tf2_echo map rover1/left_gripper',
                'grab: /rover1/left_gripper (std_srvs/srv/SetBool)']


class Frames(Mission):
    number = 10
    title = 'Frames'
    story = ['Six targets around the rover.', 'tf2 knows where everything is.']
    star_times = (8, 20)
    coding = True
    forbid_driving = True
    forbid_teleport = True
    sim_params = {**ARM_PARAMS, 'view_zoom': 4.0, 'view_center_x': 6.0, 'view_center_y': 6.0}
    TARGETS = 6

    def setup(self):
        self.r = self.mc.watch('rover1')
        self.pose = (6.0, 6.0, round(self.mc.rng.uniform(-math.pi, math.pi), 3))
        self.mc.teleport('rover1', *self.pose)
        points = []
        while len(points) < self.TARGETS:
            side = self.mc.rng.choice(('left', 'right'))
            sign = 1 if side == 'left' else -1
            reach = self.mc.rng.uniform(0.5, 1.0)
            angle = sign * self.mc.rng.uniform(-0.3, 1.5)
            x = SHOULDER[side][0] + reach * math.cos(angle)
            y = SHOULDER[side][1] + reach * math.sin(angle)
            p = rover_to_map(self.pose, x, y)
            if x >= 0.6 and all(math.hypot(p[0] - q[0], p[1] - q[1]) > 0.35 for q in points):
                points.append(p)
        self.run = BeaconRun(points, 0.12)
        self.targets = Objective('Touch the targets in order', total=self.TARGETS)
        self.own = self.own_node_objective('Move the arms')
        self.objectives = [self.targets, self.own]

    def update(self):
        if self.mc.since_start() < 2.0:
            return   # the setup teleport may still be on its way
        self.run.update(self.r.tip('left'), self.r.tip('right'))
        self.targets.progress(self.run.reached)
        self.own.check(self.own_node_driving())

    def goals(self):
        return self.run.remaining()

    def hints(self):
        return ['targets: /mission/goals (map frame)', 'tf_buffer.transform(point, "rover1/left_shoulder")',
                'then inverse kinematics']


class DrillAndStow(Mission):
    number = 11
    title = 'Drill & Stow'
    story = ['Three drill sites. Drill each one,', 'then put the core in the cache.']
    star_times = (120, 240)
    coding = True
    forbid_teleport = True
    sim_params = {**ARM_PARAMS, 'view_zoom': 2.0, 'view_center_x': 7.5, 'view_center_y': 7.5}
    SITES = 3

    def setup(self):
        self.r = self.mc.watch('rover1')
        self.sites = []
        while len(self.sites) < self.SITES:
            p = (round(self.mc.rng.uniform(5.0, 11.5), 2), round(self.mc.rng.uniform(5.0, 11.5), 2))
            if all(math.hypot(p[0] - q[0], p[1] - q[1]) > 2.5 for q in self.sites):
                self.sites.append(p)
        for x, y in self.sites:
            self.mc.place('drill_site', x, y)
        self.scenery(rocks=[(13.5, 4.5), (4.0, 13.5, 0.6)], sand=[(14.0, 13.5, 1.5)])
        self.cores = Objective('Cores stowed in the cache', total=self.SITES)
        self.own = self.own_node_objective()
        self.objectives = [self.cores, self.own]

    def update(self):
        self.cores.progress(self.r.onboard)
        self.own.check(self.own_node_driving())

    def items(self):
        """Drill sites still to drill, as the orbiter sees them."""
        return [(o['x'], o['y']) for o in self.mc.judge.get('objects', []) if o['kind'] == 'drill_site']

    def hints(self):
        return ['drill sites: /mission/items', 'drill: /rover1/drill (mars_interfaces/action/Drill)',
                'too hot? cancel, wait, drill again']


class MeteoriteRecovery(Mission):
    number = 12
    title = 'Boss: Meteorite Recovery'
    story = ['Two meteorites, too heavy for one arm.', 'Carry them to the lander.']
    star_times = (120, 240)
    coding = True
    forbid_teleport = True
    sim_params = {**ARM_PARAMS, 'battery_start': 0.6, 'battery_drain': 3.0}
    METEORITES = 2

    def setup(self):
        self.r = self.mc.watch('rover1')
        self.meteorites = []
        while len(self.meteorites) < self.METEORITES:
            p = (round(self.mc.rng.uniform(4.0, 17.0), 2), round(self.mc.rng.uniform(4.0, 17.0), 2))
            if (math.hypot(p[0] - LANDER[0], p[1] - LANDER[1]) > 7.0
                    and all(math.hypot(p[0] - q[0], p[1] - q[1]) > 4.0 for q in self.meteorites)):
                self.meteorites.append(p)
        for x, y in self.meteorites:
            self.mc.place('meteorite', x, y)
        # keep every straight line lander <-> meteorite free of rocks
        routes = [p for m in self.meteorites for p in (LANDER, m)]
        rocks = self.random_points(8, avoid=self.meteorites, gap=2.5, route=routes, route_gap=2.0)
        self.scenery(rocks=[r + (self.mc.rng.uniform(0.4, 0.7),) for r in rocks])
        self.delivered = Objective('Meteorites set down on the lander', total=self.METEORITES)
        self.own = self.own_node_objective()
        self.objectives = [self.delivered, self.own]

    def update(self):
        self.delivered.progress(self.mc.lander_meteorites)
        self.own.check(self.own_node_driving())

    def items(self):
        """Meteorites not on the lander yet, where they are now."""
        home = set(self.mc.judge.get('meteorites_home', []))
        return [(o['x'], o['y']) for o in self.mc.judge.get('objects', [])
                if o['kind'] == 'meteorite' and o['id'] not in home]

    def hints(self):
        return ['meteorites: /mission/items', 'both grippers or it won\'t move',
                'battery: /rover1/battery']


MISSIONS = {m.number: m for m in (Landing, Telemetry, ManualDrive, Services, SurveySquare,
                                         Waypoints, SampleHunter, RoverFleet, PowerCrisis,
                                         ArmCheck, Frames, DrillAndStow, MeteoriteRecovery)}
