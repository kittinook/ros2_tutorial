"""mission_control: runs one Mars Rover Academy mission against a live mars_sim.

It watches the rovers through their public topics (the same ones the learner uses),
builds the mission's world with the /sim/... services, and sends the objectives to
the simulator's panel. Only the referee topic /judge/state is private.
"""

import json
import math
import random
import time
from typing import Dict, List, Optional, Set, Tuple

import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.qos import QoSProfile

from geometry_msgs.msg import Pose, PoseArray
from mars_interfaces.srv import PlaceObject, SpawnRover, Teleport
from nav_msgs.msg import Odometry
from rcl_interfaces.msg import ParameterEvent
from sensor_msgs.msg import BatteryState, JointState
from std_msgs.msg import Int32, String
from std_srvs.srv import Empty

from mission_control import progress
from mission_control.missions import MISSIONS

# Node names of the "drive it by hand" tools. Coding missions want movement to
# come from the learner's own node, so these are flagged when they publish commands.
MANUAL_TOOL_PREFIXES = ('_ros2cli', 'teleop', 'rosbag2')  # rosbag2: replaying a recording isn't your own node either
COMMAND_TOPICS = ('cmd_vel', 'arm/joint_command')
JUDGE_TOPIC = '/judge/state'


def yaw_from_quaternion(q) -> float:
    return math.atan2(2.0 * (q.w * q.z + q.x * q.y), 1.0 - 2.0 * (q.y * q.y + q.z * q.z))


class RoverWatch:
    """Everything mission_control observes about one rover, kept up to date by subscriptions."""

    def __init__(self, node: Node, name: str):
        self.node = node
        self.name = name
        self.x: Optional[float] = None
        self.y = 0.0
        self.yaw = 0.0
        self.v = 0.0
        self.w = 0.0
        self.distance = 0.0
        self.battery: Optional[float] = None
        self.bumps = 0
        self.onboard = 0
        self.said: List[str] = []           # everything sent on /<name>/radio, oldest first
        self.odom_stamps: List[float] = []  # receive times of recent odometry, for the rate estimate
        self.joints_moving = False
        self.holding: Dict[str, str] = {'left': '', 'right': ''}
        node.create_subscription(Odometry, f'/{name}/odom', self._on_odom, 10)
        node.create_subscription(BatteryState, f'/{name}/battery', self._on_battery, 10)
        node.create_subscription(Int32, f'/{name}/bumps', lambda m: setattr(self, 'bumps', m.data), 10)
        node.create_subscription(Int32, f'/{name}/samples_onboard', lambda m: setattr(self, 'onboard', m.data), 10)
        node.create_subscription(String, f'/{name}/radio', lambda m: self.said.append(m.data), 10)
        node.create_subscription(JointState, f'/{name}/joint_states', self._on_joints, 10)
        for side in ('left', 'right'):
            node.create_subscription(String, f'/{name}/{side}_gripper/holding',
                                     lambda m, side=side: self.holding.__setitem__(side, m.data), 10)

    def _on_odom(self, msg: Odometry):
        x, y = msg.pose.pose.position.x, msg.pose.pose.position.y
        if self.x is not None:
            step = math.hypot(x - self.x, y - self.y)
            if step < 0.5:                 # bigger jumps are teleports, not driving
                self.distance += step
        self.x, self.y = x, y
        self.yaw = yaw_from_quaternion(msg.pose.pose.orientation)
        self.v, self.w = msg.twist.twist.linear.x, msg.twist.twist.angular.z
        now = time.monotonic()
        self.odom_stamps.append(now)
        while self.odom_stamps and now - self.odom_stamps[0] > 2.0:
            self.odom_stamps.pop(0)

    def _on_joints(self, msg: JointState):
        self.joints_moving = any(abs(v) > 1e-3 for v in msg.velocity)

    def _on_battery(self, msg: BatteryState):
        self.battery = msg.percentage

    @property
    def pos(self) -> Optional[Tuple[float, float]]:
        return None if self.x is None else (self.x, self.y)

    @property
    def moving(self) -> bool:
        return abs(self.v) > 0.01 or abs(self.w) > 0.01 or self.joints_moving

    def odom_rate(self) -> float:
        if len(self.odom_stamps) < 2:
            return 0.0
        span = self.odom_stamps[-1] - self.odom_stamps[0]
        return (len(self.odom_stamps) - 1) / span if span > 0 else 0.0

    def distance_to(self, x: float, y: float) -> float:
        return float('inf') if self.x is None else math.hypot(self.x - x, self.y - y)

    def _judge(self) -> dict:
        return self.node.judge.get('rovers', {}).get(self.name, {})

    def teleports(self) -> int:
        return self._judge().get('teleports', 0)

    def tip(self, side: str) -> Optional[Tuple[float, float]]:
        """Where a gripper is, in the map frame (from the referee)."""
        tip = self._judge().get('tips', {}).get(side)
        return None if tip is None else (tip[0], tip[1])

    def drill_broken(self) -> bool:
        return self._judge().get('drill_broken', False)


class MissionControl(Node):
    def __init__(self):
        super().__init__('mission_control')
        self.declare_parameter('mission', 0)
        self.declare_parameter('seed', -1)
        number = self.get_parameter('mission').value
        seed = self.get_parameter('seed').value
        self.rng = random.Random(None if seed < 0 else seed)
        if number not in MISSIONS:
            raise SystemExit(f'Unknown mission {number}. Available: {sorted(MISSIONS)}')

        self.hud_pub = self.create_publisher(String, '/mission/hud', 10)
        self.goals_pub = self.create_publisher(PoseArray, '/mission/goals', 10)
        self.items_pub = self.create_publisher(PoseArray, '/mission/items', 10)
        self.radio_pubs: Dict[str, rclpy.publisher.Publisher] = {}
        # setup() places a whole world at once: keep every request, not the default 10
        self.place_cli = self.create_client(PlaceObject, '/sim/place_object', qos_profile=QoSProfile(depth=500))
        self.clear_cli = self.create_client(Empty, '/sim/clear')
        self.spawn_cli = self.create_client(SpawnRover, '/spawn_rover')
        self.teleport_clis: Dict[str, rclpy.client.Client] = {}

        self.rovers: Dict[str, RoverWatch] = {}
        self.judge: dict = {}
        self.photos: List[str] = []     # /earth/downlink messages
        self.lander_samples = 0
        self.lander_meteorites = 0
        self.changed_param_nodes: Set[str] = set()
        self.create_subscription(String, JUDGE_TOPIC, lambda m: setattr(self, 'judge', json.loads(m.data)), 10)
        self.create_subscription(String, '/earth/downlink', lambda m: self.photos.append(m.data), 10)
        self.create_subscription(Int32, '/lander/samples', lambda m: setattr(self, 'lander_samples', m.data), 10)
        self.create_subscription(Int32, '/lander/meteorites', lambda m: setattr(self, 'lander_meteorites', m.data), 10)
        self.create_subscription(ParameterEvent, '/parameter_events', self._on_param_event, 10)

        self.mission = MISSIONS[number](self)
        self.reset_future = None
        self.started_at: Optional[float] = None   # mission set up
        self.clock_start: Optional[float] = None  # stopwatch running (may wait for the first move)
        self.finished_at: Optional[float] = None
        self.failed: Optional[str] = None
        self.stars = 0
        self.manual_publishers: Set[str] = set()  # teleop / ros2 topic pub seen on a command topic
        self.own_publishers: Set[str] = set()     # any other node seen on a command topic
        self.judge_peekers: Set[str] = set()      # nodes other than us reading the referee topic
        self.create_timer(0.1, self.tick)
        self.get_logger().info(f'Mission {number}: {self.mission.title} -- waiting for mars_sim...')

    # ------------------------------------------------------------------ helpers used by missions
    def watch(self, name: str) -> RoverWatch:
        if name not in self.rovers:
            self.rovers[name] = RoverWatch(self, name)
        return self.rovers[name]

    def place(self, kind: str, x: float, y: float, radius: float = 0.0, id: str = ''):
        self.place_cli.call_async(PlaceObject.Request(kind=kind, x=float(x), y=float(y), radius=float(radius), id=id))

    def spawn_rover(self, name: str, x: float, y: float, yaw: float = 0.0):
        self.spawn_cli.call_async(SpawnRover.Request(name=name, x=float(x), y=float(y), yaw=float(yaw)))

    def teleport(self, name: str, x: float, y: float, yaw: float = 0.0):
        if name not in self.teleport_clis:
            self.teleport_clis[name] = self.create_client(Teleport, f'/{name}/teleport')
        self.teleport_clis[name].call_async(Teleport.Request(x=float(x), y=float(y), yaw=float(yaw)))

    def radio(self, name: str, text: str):
        if name not in self.radio_pubs:
            self.radio_pubs[name] = self.create_publisher(String, f'/{name}/radio', 10)
        self.radio_pubs[name].publish(String(data=text))

    def topic_exists(self, topic: str) -> bool:
        return any(t == topic for t, _ in self.get_topic_names_and_types())

    def node_namespaces(self) -> Set[str]:
        return {ns for _, ns in self.get_node_names_and_namespaces()}

    def elapsed(self) -> float:
        if self.clock_start is None:
            return 0.0
        end = self.finished_at if self.finished_at is not None else time.monotonic()
        return end - self.clock_start

    def since_start(self) -> float:
        return 0.0 if self.started_at is None else time.monotonic() - self.started_at

    # ------------------------------------------------------------------ internals
    def _on_param_event(self, msg: ParameterEvent):
        if msg.changed_parameters and msg.node not in (self.get_fully_qualified_name(), '/mars_sim'):
            self.changed_param_nodes.add(msg.node)

    def _check_graph(self):
        """Who is commanding the watched rovers? Who reads the referee topic? (ros2 topic info -v)"""
        for name in self.rovers:
            for topic in COMMAND_TOPICS:
                for info in self.get_publishers_info_by_topic(f'/{name}/{topic}'):
                    if info.node_name.startswith(MANUAL_TOOL_PREFIXES):
                        self.manual_publishers.add(info.node_name)
                    elif info.node_name != self.get_name():
                        self.own_publishers.add(f'{info.node_namespace.rstrip("/")}/{info.node_name}')
        for info in self.get_subscriptions_info_by_topic(JUDGE_TOPIC):
            if info.node_name != self.get_name():
                self.judge_peekers.add(info.node_name)

    def _services_ready(self) -> bool:
        return all(c.service_is_ready() for c in (self.place_cli, self.clear_cli, self.spawn_cli))

    def _publish_goals(self):
        msg = PoseArray()
        msg.header.frame_id = 'map'
        for x, y, r in self.mission.goals():
            p = Pose()
            p.position.x, p.position.y, p.position.z = float(x), float(y), float(r)
            msg.poses.append(p)
        self.goals_pub.publish(msg)
        items = PoseArray()
        items.header.frame_id = 'map'
        for x, y in self.mission.items():
            p = Pose()
            p.position.x, p.position.y = float(x), float(y)
            items.poses.append(p)
        self.items_pub.publish(items)

    def _hud(self) -> str:
        m = self.mission
        lines = [f'# Mission {m.number}: {m.title}']
        if self.failed is not None:
            lines += ['', '# Mission failed', f'! {self.failed}', 'Close the window and launch again to retry.']
        elif self.finished_at is not None:
            lines += ['', '# Mission complete!', f'$ {self.stars}']
        else:
            lines += m.story
        lines.append('')
        for obj in m.objectives:
            lines.append(('[x] ' if obj.done else '[ ] ') + obj.label())
        if self.finished_at is None and self.failed is None:
            lines.append('')
            lines += [f'* {h}' for h in m.hints()]
            for w in m.warnings():
                lines.append(f'! {w}')
        if self.clock_start is None:
            lines += ['', 'Time --:-- (starts when a rover moves)']
        else:
            minutes, seconds = divmod(int(self.elapsed()), 60)
            lines += ['', f'Time {minutes:02d}:{seconds:02d}']
        if self.finished_at is not None and self.failed is None:
            if m.number + 1 in MISSIONS:
                lines.append(f'* Next: mission:={m.number + 1}')
            else:
                lines.append('* You finished every mission!')
        return '\n'.join(lines)

    def tick(self):
        if self.started_at is None:
            if not self._services_ready():
                return
            # Start from an empty world, and only set the mission up once the clear has been
            # answered: requests to different services aren't guaranteed to be handled in the
            # order they were sent, so a clear racing the mission's placements could undo them.
            if self.reset_future is None:
                self.reset_future = self.clear_cli.call_async(Empty.Request())
            if not self.reset_future.done():
                return
            self.mission.setup()
            self.started_at = time.monotonic()
            if not self.mission.coding:
                self.clock_start = self.started_at
            self.get_logger().info('Mission started! The objectives are on the right of the simulator window.')
        if self.clock_start is None and self.since_start() > 1.5 and any(w.moving for w in self.rovers.values()):
            self.clock_start = time.monotonic()
        self._check_graph()   # every tick: a `ros2 topic pub --once` publisher only lives for a moment
        if self.finished_at is None and self.failed is None:
            self.mission.update()
            self.failed = self.mission.failure()
            if self.failed is not None:
                self.finished_at = time.monotonic()
                self.get_logger().warn(f'Mission failed: {self.failed}')
            elif self.mission.objectives and all(o.done for o in self.mission.objectives):
                self._finish()
        self._publish_goals()
        self.hud_pub.publish(String(data=self._hud()))

    def _finish(self):
        self.finished_at = time.monotonic()
        t = self.elapsed()
        self.stars = min(self.mission.stars(t), self.mission.star_cap())
        best = progress.record(self.mission.number, self.stars, t)
        banner = '⭐' * self.stars + '☆' * (3 - self.stars)
        self.get_logger().info(
            f'\n\n  🚀  MISSION {self.mission.number} COMPLETE  {banner}  ({t:.1f} s)\n'
            f'      best so far: {"⭐" * best["stars"]} {best["time"]:.1f} s'
            f'   -- see all: ros2 run mission_control progress\n')
        self.radio(self.mission.main_rover, 'Mission complete!')


def main(args=None):
    rclpy.init(args=args)
    node = None
    try:
        node = MissionControl()
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException, SystemExit) as exc:
        if isinstance(exc, SystemExit) and exc.code:
            print(exc.code)
    finally:
        # Ctrl+C in a launch terminal can deliver a second SIGINT while we clean up
        try:
            if node is not None:
                node.destroy_node()
            rclpy.try_shutdown()
        except (KeyboardInterrupt, Exception):
            pass


if __name__ == '__main__':
    main()
