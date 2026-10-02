#!/usr/bin/python3
"""quest_master: runs one Turtle Quest mission against a live turtlesim_plus.

It only talks to the simulator through its public ROS 2 interface -- the same
topics and services the learner uses -- so it doubles as a worked example of a
node that subscribes, publishes and calls services.
"""

import math
import random
import time
from typing import Dict, List, Optional, Set, Tuple

import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node

from geometry_msgs.msg import Point, Pose as GeoPose, PoseArray
from rcl_interfaces.msg import ParameterEvent
from sensor_msgs.msg import JointState
from std_msgs.msg import Bool, Int64, String
from std_srvs.srv import Empty
from turtlesim.msg import Pose
from turtlesim.srv import Spawn, TeleportAbsolute
from turtlesim_plus_interfaces.msg import WorldObjectArray
from turtlesim_plus_interfaces.srv import GivePosition

from turtle_quest import progress
from turtle_quest.missions import MISSIONS

# Node names of the "drive it by hand" tools. Coding missions want movement to
# come from the learner's own node, so these are flagged when they publish commands.
MANUAL_TOOL_PREFIXES = ('_ros2cli', 'teleop')
COMMAND_TOPICS = ('cmd_vel', 'joint_command')
TELEPORT_JUMP = 1.0  # world units between two consecutive poses that counts as a teleport


class TurtleWatch:
    """Everything quest_master observes about one turtle, kept up to date by subscriptions."""

    def __init__(self, node: Node, name: str):
        self.name = name
        self.pose: Optional[Pose] = None
        self.distance = 0.0
        self.pizza = 0
        self.parcel = 0
        self.carrying = False
        self.said: List[str] = []  # everything this turtle has said, oldest first
        self.teleported = False
        self.pose_stamps: List[float] = []  # receive times of recent poses, for the rate estimate
        self.tips: Dict[str, Tuple[float, float]] = {}  # gripper tip positions (arms only)
        self.holding: Dict[str, str] = {}               # what each gripper holds ('' = nothing)
        self.joints_moving = False
        node.create_subscription(Pose, f'/{name}/pose', self._on_pose, 10)
        node.create_subscription(Int64, f'/{name}/pizza_count', self._on_pizza, 10)
        node.create_subscription(Int64, f'/{name}/parcel_count', self._on_parcel, 10)
        node.create_subscription(Bool, f'/{name}/carrying_parcel', self._on_carrying, 10)
        node.create_subscription(String, f'/{name}/say', self._on_say, 10)
        node.create_subscription(JointState, f'/{name}/joint_states', self._on_joints, 10)
        for side in ('left', 'right'):
            node.create_subscription(Point, f'/{name}/{side}_arm/tip',
                                     lambda msg, side=side: self.tips.__setitem__(side, (msg.x, msg.y)), 10)
            node.create_subscription(String, f'/{name}/{side}_gripper/holding',
                                     lambda msg, side=side: self.holding.__setitem__(side, msg.data), 10)

    def _on_pose(self, msg: Pose):
        if self.pose is not None:
            step = math.hypot(msg.x - self.pose.x, msg.y - self.pose.y)
            if step > TELEPORT_JUMP:
                self.teleported = True
            else:
                self.distance += step
        self.pose = msg
        now = time.monotonic()
        self.pose_stamps.append(now)
        while self.pose_stamps and now - self.pose_stamps[0] > 2.0:
            self.pose_stamps.pop(0)

    def _on_pizza(self, msg: Int64):
        self.pizza = msg.data

    def _on_parcel(self, msg: Int64):
        self.parcel = msg.data

    def _on_carrying(self, msg: Bool):
        self.carrying = msg.data

    def _on_say(self, msg: String):
        self.said.append(msg.data)

    def _on_joints(self, msg: JointState):
        self.joints_moving = any(abs(v) > 1e-3 for v in msg.velocity)

    def pose_rate(self) -> float:
        if len(self.pose_stamps) < 2:
            return 0.0
        span = self.pose_stamps[-1] - self.pose_stamps[0]
        return (len(self.pose_stamps) - 1) / span if span > 0 else 0.0

    def distance_to(self, x: float, y: float) -> float:
        if self.pose is None:
            return float('inf')
        return math.hypot(self.pose.x - x, self.pose.y - y)


class QuestMaster(Node):
    def __init__(self):
        super().__init__('quest_master')
        self.declare_parameter('mission', 0)
        self.declare_parameter('seed', -1)
        number = self.get_parameter('mission').value
        seed = self.get_parameter('seed').value
        self.rng = random.Random(None if seed < 0 else seed)
        if number not in MISSIONS:
            raise SystemExit(f'Unknown mission {number}. Available: {sorted(MISSIONS)}')

        self.hud_pub = self.create_publisher(String, 'hud', 10)
        self.goals_pub = self.create_publisher(PoseArray, 'mission/goals', 10)
        self.items_pub = self.create_publisher(PoseArray, 'mission/items', 10)
        self.say_pubs: Dict[str, rclpy.publisher.Publisher] = {}
        self.spawn_pizza_cli = self.create_client(GivePosition, 'spawn_pizza')
        self.spawn_parcel_cli = self.create_client(GivePosition, 'spawn_parcel')
        self.spawn_crate_cli = self.create_client(GivePosition, 'spawn_crate')
        self.spawn_turtle_cli = self.create_client(Spawn, 'spawn_turtle')
        self.clear_objects_cli = self.create_client(Empty, 'clear_objects')
        self.clear_cli = self.create_client(Empty, 'clear')
        self.teleport_clis: Dict[str, rclpy.client.Client] = {}

        self.turtles: Dict[str, TurtleWatch] = {}
        self.changed_param_nodes: Set[str] = set()
        self.create_subscription(ParameterEvent, '/parameter_events', self._on_param_event, 10)
        self.objects = []  # every pizza/parcel/crate, from the simulator's referee topic
        self.create_subscription(WorldObjectArray, '/judge/objects', self._on_objects, 10)

        self.mission = MISSIONS[number](self)
        self.reset_future = None
        self.started_at: Optional[float] = None  # mission set up
        self.clock_start: Optional[float] = None  # stopwatch running (may wait for the first move)
        self.finished_at: Optional[float] = None
        self.stars = 0
        self.manual_publishers: Set[str] = set()  # teleop / ros2 topic pub seen on a command topic
        self.own_publishers: Set[str] = set()     # any other node seen on a command topic
        self.judge_peekers: Set[str] = set()      # nodes other than us reading /judge/objects
        self.create_timer(0.1, self.tick)
        self.get_logger().info(f'Mission {number}: {self.mission.title} -- waiting for turtlesim_plus...')

    # ------------------------------------------------------------------ helpers used by missions
    def watch(self, name: str) -> TurtleWatch:
        if name not in self.turtles:
            self.turtles[name] = TurtleWatch(self, name)
        return self.turtles[name]

    def spawn_pizza(self, x: float, y: float):
        self.spawn_pizza_cli.call_async(GivePosition.Request(x=float(x), y=float(y)))

    def spawn_parcel(self, x: float, y: float):
        self.spawn_parcel_cli.call_async(GivePosition.Request(x=float(x), y=float(y)))

    def spawn_crate(self, x: float, y: float):
        self.spawn_crate_cli.call_async(GivePosition.Request(x=float(x), y=float(y)))

    def spawn_turtle(self, name: str, x: float, y: float, theta: float = 0.0):
        self.spawn_turtle_cli.call_async(Spawn.Request(name=name, x=float(x), y=float(y), theta=float(theta)))

    def teleport(self, name: str, x: float, y: float, theta: float = 0.0):
        if name not in self.teleport_clis:
            self.teleport_clis[name] = self.create_client(TeleportAbsolute, f'/{name}/teleport_absolute')
        self.teleport_clis[name].call_async(TeleportAbsolute.Request(x=float(x), y=float(y), theta=float(theta)))

    def clear_trails(self):
        self.clear_cli.call_async(Empty.Request())

    def say(self, name: str, text: str):
        if name not in self.say_pubs:
            self.say_pubs[name] = self.create_publisher(String, f'/{name}/say', 10)
        self.say_pubs[name].publish(String(data=text))

    def topic_exists(self, topic: str) -> bool:
        return any(t == topic for t, _ in self.get_topic_names_and_types())

    def node_namespaces(self) -> Set[str]:
        return {ns for _, ns in self.get_node_names_and_namespaces()}

    def random_point(self, margin: float = 1.0, avoid=(), min_gap: float = 1.5):
        """Random (x, y) inside the world, at least min_gap from every point in avoid."""
        for _ in range(200):
            p = (self.rng.uniform(margin, 10.88 - margin), self.rng.uniform(margin, 10.88 - margin))
            if all(math.hypot(p[0] - a[0], p[1] - a[1]) >= min_gap for a in avoid):
                return p
        return p

    def elapsed(self) -> float:
        if self.clock_start is None:
            return 0.0
        end = self.finished_at if self.finished_at is not None else time.monotonic()
        return end - self.clock_start

    # ------------------------------------------------------------------ internals
    def _on_param_event(self, msg: ParameterEvent):
        if msg.changed_parameters and msg.node != self.get_fully_qualified_name():
            self.changed_param_nodes.add(msg.node)

    def _on_objects(self, msg: WorldObjectArray):
        self.objects = list(msg.objects)

    def _check_graph(self):
        """Who is commanding the watched turtles? Who reads the referee topic? (ros2 topic info -v)"""
        for name in self.turtles:
            for topic in COMMAND_TOPICS:
                for info in self.get_publishers_info_by_topic(f'/{name}/{topic}'):
                    if info.node_name.startswith(MANUAL_TOOL_PREFIXES):
                        self.manual_publishers.add(info.node_name)
                    elif info.node_name != self.get_name():
                        self.own_publishers.add(f'{info.node_namespace.rstrip("/")}/{info.node_name}')
        for info in self.get_subscriptions_info_by_topic('/judge/objects'):
            if info.node_name != self.get_name():
                self.judge_peekers.add(info.node_name)

    def _services_ready(self) -> bool:
        return all(c.service_is_ready() for c in (
            self.spawn_pizza_cli, self.spawn_parcel_cli, self.spawn_crate_cli, self.spawn_turtle_cli,
            self.clear_objects_cli, self.clear_cli))

    def _publish_goals(self):
        msg = PoseArray()
        for x, y, r in self.mission.goals():
            p = GeoPose()
            p.position.x, p.position.y, p.position.z = float(x), float(y), float(r)
            msg.poses.append(p)
        self.goals_pub.publish(msg)
        items = PoseArray()
        for x, y in self.mission.items():
            p = GeoPose()
            p.position.x, p.position.y = float(x), float(y)
            items.poses.append(p)
        self.items_pub.publish(items)

    def _hud(self) -> str:
        m = self.mission
        lines = [f'# Mission {m.number}: {m.title}']
        if self.finished_at is not None:
            lines += ['', '# Mission complete!', f'$ {self.stars}']
        else:
            lines += m.story
        lines.append('')
        for obj in m.objectives:
            lines.append(('[x] ' if obj.done else '[ ] ') + obj.label())
        if self.finished_at is None:
            lines.append('')
            lines += [f'* {h}' for h in m.hints()]
        for w in m.warnings():
            lines.append(f'! {w}')
        if self.clock_start is None:
            lines += ['', 'Time --:-- (starts when the turtle moves)']
        else:
            minutes, seconds = divmod(int(self.elapsed()), 60)
            lines += ['', f'Time {minutes:02d}:{seconds:02d}']
        if self.finished_at is not None:
            if m.number + 1 in MISSIONS:
                lines.append(f'* Next: mission:={m.number + 1}')
            else:
                lines.append('* You finished every mission!')
        return '\n'.join(lines)

    def tick(self):
        if self.started_at is None:
            if not self._services_ready():
                return
            # Start from an empty world, and only set the mission up once the clear
            # has been answered: requests to *different* services aren't guaranteed
            # to be handled in the order they were sent, so a clear racing the
            # mission's spawns could delete a freshly spawned pizza.
            if self.reset_future is None:
                self.reset_future = self.clear_objects_cli.call_async(Empty.Request())
                self.clear_trails()
            if not self.reset_future.done():
                return
            self.mission.setup()
            self.started_at = time.monotonic()
            if not self.mission.coding:
                self.clock_start = self.started_at
            self.get_logger().info('Mission started! Objectives are shown in the simulator window.')
        if self.clock_start is None and any(
                w.joints_moving or (w.pose is not None and (w.pose.linear_velocity or w.pose.angular_velocity))
                for w in self.turtles.values()):
            self.clock_start = time.monotonic()
        # every tick: a `ros2 topic pub --once` publisher only lives for a moment
        self._check_graph()
        if self.finished_at is None:
            self.mission.update()
            if self.mission.objectives and all(o.done for o in self.mission.objectives):
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
            f'\n\n  🎉  MISSION {self.mission.number} COMPLETE  {banner}  ({t:.1f} s)\n'
            f'      best so far: {"⭐" * best["stars"]} {best["time"]:.1f} s'
            f'   -- see all: ros2 run turtle_quest progress\n')
        self.say(self.mission.main_turtle, 'Mission complete!')


def main(args=None):
    rclpy.init(args=args)
    node = None
    try:
        node = QuestMaster()
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException, SystemExit) as exc:
        if isinstance(exc, SystemExit) and exc.code:
            print(exc.code)
    finally:
        if node is not None:
            node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
