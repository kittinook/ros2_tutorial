"""The Mars world: terrain, objects and rovers.

Plain Python and numpy, no ROS and no pygame, so the physics can be tested on its own.
Units are metres, seconds and radians. (0, 0) is the bottom-left corner of the map,
+x points right (east), +y points up (north), yaw 0 faces +x and grows counter-clockwise.
"""

import math
import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import numpy as np

WORLD_SIZE = 20.0
LANDER = (3.0, 3.0)
LANDER_RADIUS = 1.5

ROVER_LENGTH = 0.8
ROVER_WIDTH = 0.6
ROVER_RADIUS = 0.42            # collision circle
MAX_LINEAR = 1.0               # m/s
MAX_ANGULAR = 2.0              # rad/s
LINEAR_ACCEL = 1.0             # m/s^2
ANGULAR_ACCEL = 3.0            # rad/s^2

CAMERA_FOV = math.radians(60)
CAMERA_RANGE = 6.0
LASER_OFFSET = 0.3             # laser sits this far in front of the rover's centre
SCAN_ANGLE_MIN = -math.pi / 2
SCAN_ANGLE_MAX = math.pi / 2
SCAN_RAYS = 181
SCAN_RANGE_MIN = 0.15
SCAN_RANGE_MAX = 8.0
SCAN_NOISE = 0.01
SCAN_ANGLES = np.linspace(SCAN_ANGLE_MIN, SCAN_ANGLE_MAX, SCAN_RAYS)  # relative to the rover's heading

COLLECT_RANGE = 1.0
COLLECT_ANGLE = math.radians(30)
PHOTO_RANGE = 3.0
PHOTO_ANGLE = math.radians(30)

CRATER_FACTOR = 0.75           # speed you keep inside a crater

# battery use, as a fraction of a full battery (multiplied by the battery_drain parameter)
DRAIN_IDLE = 0.0002            # per second
DRAIN_DRIVE = 0.002            # per metre
CHARGE_RATE = 0.03             # per second, parked on the lander

# the arms (Part 2): two planar 2-link arms on the front corners, angles in the rover frame,
# 0 = pointing straight ahead, + = counter-clockwise (to the left)
SHOULDER = {'left': (0.4, 0.25), 'right': (0.4, -0.25)}   # in base_link
L1 = 0.6                       # upper arm
L2 = 0.5                       # forearm
JOINTS = ('left_shoulder', 'left_elbow', 'right_shoulder', 'right_elbow')
JOINT_LIMIT = {'shoulder': math.pi, 'elbow': 2.8}
JOINT_SPEED = 2.0              # rad/s
GRAB_RADIUS = 0.3              # how close the gripper must be to a small object's centre
GRAB_MARGIN = 0.15             # ... or to a meteorite's edge
METEORITE_SLIP = 1.2           # grippers further apart than this drop the meteorite
GRASPABLE = ('sample', 'core', 'meteorite')
CACHE = (-0.15, 0.0)           # sample cache on the rover's back, in base_link
CACHE_RADIUS = 0.25
CACHE_CAPACITY = 6

# the drill, under the middle of the rover
DRILL_REACH = 0.35             # a drill site this close to the rover's centre can be drilled
DRILL_SPEED = 0.04             # m/s
DRILL_HEAT = 15.0              # degrees C per second while drilling
DRILL_COOL = 10.0              # degrees C per second while not
DRILL_AMBIENT = 20.0
DRILL_MAX_TEMP = 80.0          # hotter than this and the bit breaks
CORE_OFFSET = (0.9, 0.0)       # where the drill leaves the core, in base_link
CORE_DEPTH = 0.3               # a hole this deep gives a core sample
DRAIN_DRILL = 0.002            # battery per second of drilling

DEFAULT_RADIUS = {
    'rock': 0.5, 'landmark': 0.7, 'sand': 2.0, 'crater': 1.5,
    'sample': 0.15, 'drill_site': 0.3, 'core': 0.12, 'meteorite': 0.35,
}
TERRAIN = ('sand', 'crater')                 # ground you drive over
SOLID = ('rock', 'landmark')                 # blocks the rover, seen by the laser
VISIBLE = ('sample', 'rock', 'landmark', 'drill_site', 'core', 'meteorite')  # seen by the camera
KINDS = tuple(DEFAULT_RADIUS)


def wrap(angle: float) -> float:
    """Angle in -pi..pi."""
    return math.atan2(math.sin(angle), math.cos(angle))


def approach(value: float, target: float, step: float) -> float:
    if value < target:
        return min(value + step, target)
    return max(value - step, target)


def arm_points(r: 'Rover', side: str) -> List[Tuple[float, float]]:
    """Shoulder, elbow and gripper of one arm, in the rover frame (forward kinematics)."""
    q1, q2 = r.joints[f'{side}_shoulder'], r.joints[f'{side}_elbow']
    sx, sy = SHOULDER[side]
    ex, ey = sx + L1 * math.cos(q1), sy + L1 * math.sin(q1)
    return [(sx, sy), (ex, ey), (ex + L2 * math.cos(q1 + q2), ey + L2 * math.sin(q1 + q2))]


@dataclass
class WorldObject:
    kind: str
    id: str
    x: float
    y: float
    radius: float


@dataclass
class Detection:
    kind: str
    id: str
    range: float
    bearing: float


@dataclass
class Rover:
    name: str
    x: float
    y: float
    yaw: float = 0.0
    battery: float = 1.0
    # what the motors are doing (before slip) and what the rover really does (after slip)
    wheel_v: float = 0.0
    wheel_w: float = 0.0
    v: float = 0.0
    w: float = 0.0
    cmd_v: float = 0.0
    cmd_w: float = 0.0
    cmd_time: float = -1e9
    bumps: int = 0
    in_contact: bool = False
    teleports: int = 0
    distance: float = 0.0
    samples_onboard: int = 0
    radio: str = ''
    radio_time: float = -1e9
    track: List[Tuple[float, float, float]] = field(default_factory=list)  # (x, y, yaw) breadcrumbs
    joints: Dict[str, float] = field(default_factory=lambda: {j: 0.0 for j in JOINTS})
    joint_targets: Dict[str, float] = field(default_factory=lambda: {j: 0.0 for j in JOINTS})
    joint_velocity: Dict[str, float] = field(default_factory=lambda: {j: 0.0 for j in JOINTS})
    holding: Dict[str, str] = field(default_factory=lambda: {'left': '', 'right': ''})
    cache: List[str] = field(default_factory=list)
    drilling: bool = False
    drill_temp: float = DRILL_AMBIENT
    drill_broken: bool = False

    @property
    def dead(self) -> bool:
        return self.battery <= 0.0


class World:
    def __init__(self, seed: int = 0):
        self.rng = random.Random(seed)
        self.objects: Dict[str, WorldObject] = {}
        self.rovers: Dict[str, Rover] = {}
        self.delivered = 0
        self.photos: List[Tuple[str, str]] = []   # (rover, landmark), oldest first
        self.terrain_version = 0                   # bumped whenever the ground or the rocks change
        self.cmd_timeout = 1.0
        self.sand_slip = 0.6
        self.battery_drain = 1.0
        self.arms = False
        self.hole_depth: Dict[str, float] = {}        # drill site -> how deep it has been drilled
        self.meteorites_home: List[str] = []         # meteorites set down on the lander
        self.events: List[str] = []                  # things worth logging, collected by the node
        self._counter = 0

    # ------------------------------------------------------------------ building the world
    def add_object(self, kind: str, x: float, y: float, radius: float = 0.0, id: str = '') -> str:
        if kind not in KINDS:
            raise ValueError(f'unknown kind {kind!r}, expected one of {", ".join(KINDS)}')
        if not id:
            self._counter += 1
            id = f'{kind}_{self._counter}'
        while id in self.objects:
            id += "'"
        self.objects[id] = WorldObject(kind, id, float(x), float(y), radius if radius > 0 else DEFAULT_RADIUS[kind])
        if kind in TERRAIN or kind in SOLID:
            self.terrain_version += 1
        return id

    def remove_object(self, id: str):
        obj = self.objects.pop(id, None)
        if obj is not None and (obj.kind in TERRAIN or obj.kind in SOLID):
            self.terrain_version += 1

    def clear(self):
        self.objects.clear()
        self.delivered = 0
        self.hole_depth.clear()
        self.meteorites_home.clear()
        self.photos.clear()
        self._counter = 0
        self.terrain_version += 1
        for rover in self.rovers.values():
            rover.track.clear()
            rover.samples_onboard = 0
            rover.bumps = 0
            rover.teleports = 0
            rover.holding = {'left': '', 'right': ''}
            rover.cache.clear()
            rover.drill_broken = False
            rover.drill_temp = DRILL_AMBIENT
            rover.distance = 0.0

    def spawn_rover(self, name: str, x: float, y: float, yaw: float = 0.0, battery: float = 1.0) -> str:
        base = name or 'rover'
        name, n = base, 1
        while not name or name in self.rovers:
            n += 1
            name = f'{base}{n}' if base == 'rover' else f'{base}_{n}'
        self.rovers[name] = Rover(name, float(x), float(y), wrap(yaw), battery=battery)
        return name

    def teleport(self, name: str, x: float, y: float, yaw: float):
        r = self.rovers[name]
        r.x = min(max(x, ROVER_RADIUS), WORLD_SIZE - ROVER_RADIUS)
        r.y = min(max(y, ROVER_RADIUS), WORLD_SIZE - ROVER_RADIUS)
        r.yaw = wrap(yaw)
        r.wheel_v = r.wheel_w = r.v = r.w = 0.0
        r.cmd_v = r.cmd_w = 0.0
        r.teleports += 1
        r.track.clear()

    def of_kind(self, *kinds: str) -> List[WorldObject]:
        return [o for o in self.objects.values() if o.kind in kinds]

    # ------------------------------------------------------------------ queries
    def on_lander(self, rover: Rover) -> bool:
        return math.hypot(rover.x - LANDER[0], rover.y - LANDER[1]) <= LANDER_RADIUS

    def terrain_factor(self, x: float, y: float) -> float:
        factor = 1.0
        for o in self.of_kind(*TERRAIN):
            if math.hypot(x - o.x, y - o.y) <= o.radius:
                factor = min(factor, self.sand_slip if o.kind == 'sand' else CRATER_FACTOR)
        return factor

    def clearance(self, name: str, x: float, y: float) -> float:
        """Free space between the rover's collision circle at (x, y) and the nearest obstacle."""
        gaps = [x - ROVER_RADIUS, y - ROVER_RADIUS, WORLD_SIZE - ROVER_RADIUS - x, WORLD_SIZE - ROVER_RADIUS - y]
        for o in self.of_kind(*SOLID):
            gaps.append(math.hypot(x - o.x, y - o.y) - o.radius - ROVER_RADIUS)
        for other in self.rovers.values():
            if other.name != name:
                gaps.append(math.hypot(x - other.x, y - other.y) - 2 * ROVER_RADIUS)
        return min(gaps)

    def relative(self, rover: Rover, x: float, y: float) -> Tuple[float, float]:
        """(range, bearing) of a point as seen from the rover."""
        dx, dy = x - rover.x, y - rover.y
        return math.hypot(dx, dy), wrap(math.atan2(dy, dx) - rover.yaw)

    # ------------------------------------------------------------------ physics
    def command(self, name: str, v: float, w: float, now: float):
        r = self.rovers[name]
        r.cmd_v, r.cmd_w, r.cmd_time = float(v), float(w), now

    def step(self, dt: float, now: float):
        for r in self.rovers.values():
            self._step_rover(r, dt, now)

    def _step_rover(self, r: Rover, dt: float, now: float):
        fresh = now - r.cmd_time <= self.cmd_timeout and not r.dead
        target_v = max(-MAX_LINEAR, min(MAX_LINEAR, r.cmd_v)) if fresh else 0.0
        target_w = max(-MAX_ANGULAR, min(MAX_ANGULAR, r.cmd_w)) if fresh else 0.0
        r.wheel_v = approach(r.wheel_v, target_v, LINEAR_ACCEL * dt)
        r.wheel_w = approach(r.wheel_w, target_w, ANGULAR_ACCEL * dt)

        factor = self.terrain_factor(r.x, r.y)
        v, w = r.wheel_v * factor, r.wheel_w * factor
        mid = r.yaw + w * dt / 2
        nx, ny = r.x + v * math.cos(mid) * dt, r.y + v * math.sin(mid) * dt
        r.yaw = wrap(r.yaw + w * dt)
        moved = 0.0
        if abs(v) > 1e-9:
            before, after = self.clearance(r.name, r.x, r.y), self.clearance(r.name, nx, ny)
            if after < 0 and after < before:      # would drive into something: stop
                r.wheel_v = 0.0
                v = 0.0
                if not r.in_contact:
                    r.bumps += 1
                r.in_contact = True
            else:
                moved = math.hypot(nx - r.x, ny - r.y)
                r.x, r.y = nx, ny
                if after > 0.05:                  # clearly free again: the next hit is a new bump
                    r.in_contact = False
        r.v, r.w = v, w
        r.distance += moved
        if not r.track or math.hypot(r.x - r.track[-1][0], r.y - r.track[-1][1]) > 0.08:
            r.track.append((r.x, r.y, r.yaw))
            del r.track[:-3000]

        if self.arms:
            self._step_arms(r, dt)
        self._step_drill(r, dt)

        # battery
        charging = self.on_lander(r) and abs(r.wheel_v) < 0.05
        if charging:
            r.battery = min(1.0, r.battery + CHARGE_RATE * dt)
        elif not r.dead:
            drill = DRAIN_DRILL * dt if r.drilling else 0.0
            r.battery = max(0.0, r.battery - self.battery_drain * (DRAIN_IDLE * dt + DRAIN_DRIVE * moved + drill))

    def charging(self, r: Rover) -> bool:
        return self.on_lander(r) and abs(r.wheel_v) < 0.05 and r.battery < 1.0

    # ------------------------------------------------------------------ frames
    def to_world(self, r: Rover, x: float, y: float) -> Tuple[float, float]:
        """A point in the rover frame (base_link) as a map point."""
        c, s = math.cos(r.yaw), math.sin(r.yaw)
        return r.x + c * x - s * y, r.y + s * x + c * y

    def tip(self, r: Rover, side: str) -> Tuple[float, float]:
        return self.to_world(r, *arm_points(r, side)[2])

    # ------------------------------------------------------------------ arms
    def command_joints(self, name: str, names: List[str], positions: List[float]) -> List[str]:
        """Set joint targets; joints that aren't named keep their old target. Returns unknown names."""
        r = self.rovers[name]
        unknown = []
        for joint, value in zip(names, positions):
            if joint not in r.joint_targets:
                unknown.append(joint)
                continue
            limit = JOINT_LIMIT['shoulder' if joint.endswith('shoulder') else 'elbow']
            r.joint_targets[joint] = max(-limit, min(limit, float(value)))
        return unknown

    def _step_arms(self, r: Rover, dt: float):
        for j in JOINTS:
            before = r.joints[j]
            r.joints[j] = approach(before, r.joint_targets[j], JOINT_SPEED * dt)
            r.joint_velocity[j] = (r.joints[j] - before) / dt if dt > 0 else 0.0
        tips = {side: self.tip(r, side) for side in ('left', 'right')}
        both = r.holding['left'] and r.holding['left'] == r.holding['right']
        for side in ('left', 'right'):
            held = self.objects.get(r.holding[side])
            if held is None:
                r.holding[side] = ''
                continue
            if held.kind != 'meteorite':
                held.x, held.y = tips[side]
            elif both:
                (lx, ly), (rx, ry) = tips['left'], tips['right']
                if math.hypot(lx - rx, ly - ry) > METEORITE_SLIP:
                    r.holding = {'left': '', 'right': ''}
                    self.events.append(f'{r.name}: the grippers are too far apart, {held.id} slipped')
                    return
                held.x, held.y = (lx + rx) / 2, (ly + ry) / 2
            elif math.hypot(tips[side][0] - held.x, tips[side][1] - held.y) > held.radius + GRAB_MARGIN + 0.1:
                r.holding[side] = ''      # one arm can't lift it: pulling away loses the grip
                self.events.append(f'{r.name}: {held.id} is too heavy for one arm, the {side} gripper lost it')

    def gripper(self, r: Rover, side: str, close: bool) -> Tuple[bool, str]:
        tx, ty = self.tip(r, side)
        if close:
            if r.holding[side]:
                return False, f'Already holding {r.holding[side]}'
            other = 'right' if side == 'left' else 'left'
            taken = {h for rv in self.rovers.values() for h in rv.holding.values() if h}
            best, best_gap, best_d = None, math.inf, math.inf
            for o in self.of_kind(*GRASPABLE):
                if o.id in taken and not (o.kind == 'meteorite' and r.holding[other] == o.id):
                    continue
                d = math.hypot(o.x - tx, o.y - ty)
                gap = d - (o.radius + GRAB_MARGIN if o.kind == 'meteorite' else GRAB_RADIUS)
                if gap < best_gap:
                    best, best_gap, best_d = o, gap, d
            if best is None or best_gap > 0:
                where = f' The closest thing to grab is {best_d:.2f} m from it.' if best else ''
                return False, f'The {side} gripper closed on nothing.{where}'
            r.holding[side] = best.id
            if best.id in self.meteorites_home:
                self.meteorites_home.remove(best.id)
            if best.kind == 'meteorite' and r.holding[other] != best.id:
                return True, f'Holding {best.id} with the {side} gripper. It is heavy: grab it with the other arm too.'
            return True, f'Holding {best.id}'

        held = self.objects.get(r.holding[side])
        r.holding[side] = ''
        if held is None:
            return True, f'The {side} gripper is open.'
        if held.kind == 'meteorite':
            other = 'right' if side == 'left' else 'left'
            if r.holding[other] == held.id:
                r.holding[other] = ''
            if math.hypot(held.x - LANDER[0], held.y - LANDER[1]) <= LANDER_RADIUS:
                self.meteorites_home.append(held.id)
                return True, f'Set {held.id} down on the lander.'
            return True, f'Set {held.id} down.'
        cx, cy = self.to_world(r, *CACHE)
        if math.hypot(held.x - cx, held.y - cy) <= CACHE_RADIUS:
            if len(r.cache) >= CACHE_CAPACITY:
                return True, f'The cache is full: dropped {held.id} on the ground.'
            self.remove_object(held.id)
            r.cache.append(held.id)
            r.samples_onboard += 1
            return True, f'Stowed {held.id} in the cache ({len(r.cache)}/{CACHE_CAPACITY}).'
        return True, f'Dropped {held.id}.'

    # ------------------------------------------------------------------ drill
    def drill_site_under(self, r: Rover) -> Optional[WorldObject]:
        sites = [o for o in self.of_kind('drill_site') if math.hypot(o.x - r.x, o.y - r.y) <= DRILL_REACH]
        return min(sites, key=lambda o: math.hypot(o.x - r.x, o.y - r.y)) if sites else None

    def parked(self, r: Rover) -> bool:
        return abs(r.wheel_v) < 0.01 and abs(r.wheel_w) < 0.01

    def _step_drill(self, r: Rover, dt: float):
        if not r.drilling:
            r.drill_temp = max(DRILL_AMBIENT, r.drill_temp - DRILL_COOL * dt)
            return
        site = self.drill_site_under(r)
        if site is None or r.drill_broken:
            r.drilling = False
            return
        self.hole_depth[site.id] = self.hole_depth.get(site.id, 0.0) + DRILL_SPEED * dt
        r.drill_temp += DRILL_HEAT * dt
        if r.drill_temp > DRILL_MAX_TEMP:
            r.drill_broken = True
            r.drilling = False
            self.events.append(f'{r.name}: the drill bit overheated and broke')

    def finish_hole(self, r: Rover, site: WorldObject) -> str:
        """The hole is deep enough: the drill site turns into a core next to the rover."""
        self.remove_object(site.id)
        x, y = self.to_world(r, *CORE_OFFSET)
        return self.add_object('core', x, y, id=site.id.replace('drill_site', 'core').replace('site', 'core'))

    # ------------------------------------------------------------------ sensors
    def scan(self, r: Rover) -> List[float]:
        """Laser ranges from right (-90 deg) to left (+90 deg); inf where nothing is in range."""
        ox = r.x + LASER_OFFSET * math.cos(r.yaw)
        oy = r.y + LASER_OFFSET * math.sin(r.yaw)
        angles = r.yaw + SCAN_ANGLES
        dx, dy = np.cos(angles), np.sin(angles)
        best = np.full(SCAN_RAYS, np.inf)

        # the edges of the map
        with np.errstate(divide='ignore', invalid='ignore'):
            for t in ((0 - ox) / dx, (WORLD_SIZE - ox) / dx, (0 - oy) / dy, (WORLD_SIZE - oy) / dy):
                t = np.where(np.isfinite(t) & (t > 0), t, np.inf)
                best = np.minimum(best, t)

        # rocks and other rovers, as circles
        circles = [(o.x, o.y, o.radius) for o in self.of_kind(*SOLID)]
        circles += [(o.x, o.y, ROVER_RADIUS) for o in self.rovers.values() if o.name != r.name]
        if circles:
            c = np.array(circles)
            fx = ox - c[:, 0][:, None]                     # circles x rays
            fy = oy - c[:, 1][:, None]
            b = fx * dx + fy * dy
            cc = fx * fx + fy * fy - (c[:, 2] ** 2)[:, None]
            disc = b * b - cc
            hit = disc >= 0
            root = np.sqrt(np.where(hit, disc, 0.0))
            t1, t2 = -b - root, -b + root
            t = np.where(t1 >= 0, t1, np.where(t2 >= 0, 0.0, np.inf))  # inside a circle -> 0
            t = np.where(hit, t, np.inf)
            best = np.minimum(best, t.min(axis=0))

        noisy = best + np.array([self.rng.gauss(0.0, SCAN_NOISE) for _ in range(SCAN_RAYS)])
        out = np.where(best > SCAN_RANGE_MAX, np.inf, np.maximum(noisy, SCAN_RANGE_MIN))
        return [float(v) for v in out]

    def detections(self, r: Rover) -> List[Detection]:
        seen = []
        for o in self.of_kind(*VISIBLE):
            rng, bearing = self.relative(r, o.x, o.y)
            if rng <= CAMERA_RANGE and abs(bearing) <= CAMERA_FOV / 2:
                seen.append(Detection(o.kind, o.id, rng, bearing))
        return sorted(seen, key=lambda d: d.range)

    # ------------------------------------------------------------------ actions on the world
    def collect(self, r: Rover) -> Tuple[bool, str]:
        reachable = []
        for o in self.of_kind('sample'):
            rng, bearing = self.relative(r, o.x, o.y)
            if rng <= COLLECT_RANGE and (abs(bearing) <= COLLECT_ANGLE or rng <= ROVER_RADIUS):
                reachable.append((rng, o))
        if not reachable:
            seen = [d for d in self.detections(r) if d.kind == 'sample']
            hint = ''
            if seen:
                d = seen[0]
                side = 'left' if d.bearing > 0 else 'right'
                hint = f' The closest one in view is {d.range:.1f} m away, {abs(math.degrees(d.bearing)):.0f} deg to the {side}.'
            return False, f'No sample within {COLLECT_RANGE:.1f} m in front of the rover.{hint}'
        _, o = min(reachable, key=lambda item: item[0])
        self.remove_object(o.id)
        r.samples_onboard += 1
        return True, f'Collected {o.id}. Samples on board: {r.samples_onboard}'

    def take_photo(self, r: Rover) -> Tuple[bool, str]:
        in_view = []
        for o in self.of_kind('landmark'):
            rng, bearing = self.relative(r, o.x, o.y)
            if rng <= PHOTO_RANGE and abs(bearing) <= PHOTO_ANGLE:
                in_view.append((rng, o))
        if not in_view:
            return False, (f'No landmark in the picture. Get within {PHOTO_RANGE:.0f} m and point the camera '
                           f'at it (less than {math.degrees(PHOTO_ANGLE):.0f} deg off).')
        _, o = min(in_view, key=lambda item: item[0])
        self.photos.append((r.name, o.id))
        return True, f'Photo of {o.id} sent to Earth.'

    def unload(self, r: Rover) -> Tuple[bool, str]:
        if not self.on_lander(r):
            return False, f'Drive onto the lander first: it is at ({LANDER[0]:.1f}, {LANDER[1]:.1f}).'
        if r.samples_onboard == 0:
            return False, 'Nothing on board to unload.'
        n = r.samples_onboard
        self.delivered += n
        r.samples_onboard = 0
        r.cache.clear()
        return True, f'Unloaded {n} sample{"s" if n != 1 else ""}. The lander now has {self.delivered}.'

    def judge_state(self) -> dict:
        """Ground truth for mission_control. Learners don't get to read this."""
        return {
            'objects': [{'kind': o.kind, 'id': o.id, 'x': round(o.x, 3), 'y': round(o.y, 3), 'radius': o.radius}
                        for o in self.objects.values()],
            'rovers': {r.name: {'x': round(r.x, 3), 'y': round(r.y, 3), 'yaw': round(r.yaw, 4),
                                'teleports': r.teleports, 'bumps': r.bumps, 'battery': round(r.battery, 4),
                                'onboard': r.samples_onboard, 'dead': r.dead, 'cache': list(r.cache),
                                'holding': dict(r.holding), 'drill_broken': r.drill_broken,
                                'tips': {s: [round(v, 3) for v in self.tip(r, s)] for s in ('left', 'right')}}
                       for r in self.rovers.values()},
            'meteorites_home': list(self.meteorites_home),
            'delivered': self.delivered,
            'photos': [list(p) for p in self.photos],
        }

    def random_free_point(self, margin: float = 1.0, avoid: Optional[List[Tuple[float, float]]] = None,
                          gap: float = 1.5) -> Tuple[float, float]:
        avoid = list(avoid or []) + [LANDER] + [(o.x, o.y) for o in self.of_kind(*SOLID)]
        p = (WORLD_SIZE / 2, WORLD_SIZE / 2)
        for _ in range(300):
            p = (self.rng.uniform(margin, WORLD_SIZE - margin), self.rng.uniform(margin, WORLD_SIZE - margin))
            if all(math.hypot(p[0] - a[0], p[1] - a[1]) >= gap for a in avoid):
                break
        return p
