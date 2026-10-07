"""mars_sim: the Mars Rover Academy simulator node.

Every rover gets the same set of topics and services under its own namespace
(/rover1/odom, /rover1/cmd_vel, ...). mission_control uses the /sim/... services
to build each mission's world; learners only need the rover interfaces.
"""

import json
import math
import os
import time
from functools import partial
from typing import Dict, List, Tuple

import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.action import ActionServer, CancelResponse, GoalResponse
from rclpy.node import Node
from rclpy.qos import QoSProfile
from rclpy.task import Future

from geometry_msgs.msg import PoseArray, TransformStamped, Twist
from mars_interfaces.action import Drill
from mars_interfaces.msg import Detection, DetectionArray
from mars_interfaces.srv import PlaceObject, SpawnRover, Teleport
from nav_msgs.msg import Odometry
from sensor_msgs.msg import BatteryState, JointState, LaserScan
from std_msgs.msg import Int32, String
from std_srvs.srv import Empty, SetBool, Trigger
from tf2_ros import StaticTransformBroadcaster, TransformBroadcaster
from visualization_msgs.msg import Marker, MarkerArray

from mars_sim import world as W

PHYSICS_RATE = 50.0   # Hz, also the odom and TF rate
SENSOR_RATE = 10.0    # Hz, laser and camera
STATUS_RATE = 2.0     # Hz, battery, bumps, samples on board
RENDER_RATE = 30.0    # Hz


def yaw_to_quaternion(yaw: float) -> Tuple[float, float, float, float]:
    """(x, y, z, w) of a rotation about the z axis."""
    return 0.0, 0.0, math.sin(yaw / 2), math.cos(yaw / 2)


def transform(stamp, parent: str, child: str, x: float, y: float, yaw: float = 0.0, z: float = 0.0):
    tf = TransformStamped()
    tf.header.stamp = stamp
    tf.header.frame_id = parent
    tf.child_frame_id = child
    tf.transform.translation.x = float(x)
    tf.transform.translation.y = float(y)
    tf.transform.translation.z = float(z)
    (tf.transform.rotation.x, tf.transform.rotation.y,
     tf.transform.rotation.z, tf.transform.rotation.w) = yaw_to_quaternion(yaw)
    return tf


class RoverIO:
    """The ROS interface of one rover."""

    def __init__(self, sim: 'MarsSim', name: str):
        self.sim = sim
        self.name = name
        node = sim
        ns = f'/{name}'
        self.odom_pub = node.create_publisher(Odometry, f'{ns}/odom', 10)
        self.scan_pub = node.create_publisher(LaserScan, f'{ns}/scan', 10)
        self.detections_pub = node.create_publisher(DetectionArray, f'{ns}/camera/detections', 10)
        self.battery_pub = node.create_publisher(BatteryState, f'{ns}/battery', 10)
        self.bumps_pub = node.create_publisher(Int32, f'{ns}/bumps', 10)
        self.samples_pub = node.create_publisher(Int32, f'{ns}/samples_onboard', 10)
        self.subs = [
            node.create_subscription(Twist, f'{ns}/cmd_vel', self.on_cmd_vel, 10),
            node.create_subscription(String, f'{ns}/radio', self.on_radio, 10),
        ]
        self.services = [
            node.create_service(Trigger, f'{ns}/take_photo', partial(self.on_trigger, sim.world.take_photo)),
            node.create_service(Trigger, f'{ns}/collect', partial(self.on_trigger, sim.world.collect)),
            node.create_service(Trigger, f'{ns}/unload', partial(self.on_trigger, sim.world.unload)),
            node.create_service(Teleport, f'{ns}/teleport', self.on_teleport),
        ]
        self.drill_server = ActionServer(node, Drill, f'{ns}/drill', execute_callback=self.execute_drill,
                                         goal_callback=self.on_drill_goal,
                                         cancel_callback=lambda goal_handle: CancelResponse.ACCEPT)
        if sim.world.arms:
            self.joint_pub = node.create_publisher(JointState, f'{ns}/joint_states', 10)
            self.holding_pubs = {side: node.create_publisher(String, f'{ns}/{side}_gripper/holding', 10)
                                 for side in ('left', 'right')}
            self.subs.append(node.create_subscription(JointState, f'{ns}/arm/joint_command', self.on_joint_command, 10))
            self.services += [node.create_service(SetBool, f'{ns}/{side}_gripper', partial(self.on_gripper, side))
                              for side in ('left', 'right')]
        self.static_frames()

    @property
    def rover(self) -> W.Rover:
        return self.sim.world.rovers[self.name]

    def static_frames(self):
        stamp = self.sim.get_clock().now().to_msg()
        base = f'{self.name}/base_link'
        frames = [transform(stamp, base, f'{self.name}/laser', W.LASER_OFFSET, 0.0, z=0.3),
                  transform(stamp, base, f'{self.name}/drill', 0.0, 0.0)]
        if self.sim.world.arms:
            frames.append(transform(stamp, base, f'{self.name}/cache', *W.CACHE, z=0.2))
            for side, (x, y) in W.SHOULDER.items():
                frames.append(transform(stamp, base, f'{self.name}/{side}_shoulder', x, y, z=0.2))
        self.sim.static_tf.sendTransform(frames)

    def arm_frames(self, stamp) -> List[TransformStamped]:
        """Upper arm, forearm and gripper frames: they move with the joints."""
        r = self.rover
        frames = []
        for side in ('left', 'right'):
            q1, q2 = r.joints[f'{side}_shoulder'], r.joints[f'{side}_elbow']
            prefix = f'{self.name}/{side}'
            frames += [transform(stamp, f'{prefix}_shoulder', f'{prefix}_upper_arm', 0.0, 0.0, q1),
                       transform(stamp, f'{prefix}_upper_arm', f'{prefix}_forearm', W.L1, 0.0, q2),
                       transform(stamp, f'{prefix}_forearm', f'{prefix}_gripper', W.L2, 0.0)]
        return frames

    # ------------------------------------------------------------------ inputs
    def on_cmd_vel(self, msg: Twist):
        self.sim.world.command(self.name, msg.linear.x, msg.angular.z, time.monotonic())

    def on_radio(self, msg: String):
        self.rover.radio = msg.data
        self.rover.radio_time = time.monotonic()

    def on_trigger(self, action, request, response):
        response.success, response.message = action(self.rover)
        if action == self.sim.world.take_photo and response.success:
            self.sim.downlink(self.name, self.sim.world.photos[-1][1])
        return response

    def on_teleport(self, request, response):
        self.sim.world.teleport(self.name, request.x, request.y, request.yaw)
        return response

    def on_joint_command(self, msg: JointState):
        if len(msg.name) != len(msg.position):
            self.sim.get_logger().warn(f'{self.name}: joint_command needs one position per name')
            return
        unknown = self.sim.world.command_joints(self.name, list(msg.name), list(msg.position))
        if unknown:
            self.sim.get_logger().warn(f'{self.name}: unknown joints {unknown}, expected some of {list(W.JOINTS)}')

    def on_gripper(self, side, request, response):
        response.success, response.message = self.sim.world.gripper(self.rover, side, request.data)
        return response

    # ------------------------------------------------------------------ the drill action
    def on_drill_goal(self, goal):
        return GoalResponse.REJECT if self.rover.drilling else GoalResponse.ACCEPT

    async def execute_drill(self, goal_handle):
        """Runs as a coroutine on the sim's one thread: it waits for the next sensor tick between steps."""
        world, r = self.sim.world, self.rover
        target = min(max(goal_handle.request.depth, 0.1), 0.5)
        result = Drill.Result()

        def finish(success: bool, message: str, end):
            r.drilling = False
            result.success, result.message = success, message
            end()
            return result

        if r.drill_broken:
            return finish(False, 'The drill bit is broken.', goal_handle.abort)
        if not world.parked(r):
            return finish(False, 'Stop the rover before drilling.', goal_handle.abort)
        site = world.drill_site_under(r)
        if site is None:
            return finish(False, f'There is no drill site under the rover. Park with the site less than '
                                 f'{W.DRILL_REACH} m from the rover\'s centre.', goal_handle.abort)
        r.drilling = True
        while True:
            await self.sim.next_tick()
            depth = world.hole_depth.get(site.id, 0.0)
            feedback = Drill.Feedback()
            feedback.depth = float(depth)
            feedback.temperature = float(r.drill_temp)
            goal_handle.publish_feedback(feedback)
            if goal_handle.is_cancel_requested:
                return finish(False, f'Stopped at {depth:.2f} m.', goal_handle.canceled)
            if r.drill_broken:
                return finish(False, f'The drill bit overheated (over {W.DRILL_MAX_TEMP:.0f} C) and broke.',
                              goal_handle.abort)
            if not world.parked(r) or world.drill_site_under(r) is not site:
                return finish(False, 'The rover moved while drilling.', goal_handle.abort)
            if depth >= target:
                if depth < W.CORE_DEPTH:
                    return finish(True, f'The hole is {depth:.2f} m deep. A core sample needs at least '
                                        f'{W.CORE_DEPTH:.2f} m: drill again.', goal_handle.succeed)
                core = world.finish_hole(r, site)
                return finish(True, f'The hole is {depth:.2f} m deep. Core sample {core} is ready in front '
                                    f'of the rover.', goal_handle.succeed)

    # ------------------------------------------------------------------ outputs
    def publish_odom(self, stamp):
        r = self.rover
        q = yaw_to_quaternion(r.yaw)
        odom = Odometry()
        odom.header.stamp = stamp
        odom.header.frame_id = 'map'
        odom.child_frame_id = f'{self.name}/base_link'
        odom.pose.pose.position.x = r.x
        odom.pose.pose.position.y = r.y
        (odom.pose.pose.orientation.x, odom.pose.pose.orientation.y,
         odom.pose.pose.orientation.z, odom.pose.pose.orientation.w) = q
        odom.twist.twist.linear.x = r.v
        odom.twist.twist.angular.z = r.w
        self.odom_pub.publish(odom)

        frames = [transform(stamp, 'map', odom.child_frame_id, r.x, r.y, r.yaw)]
        if self.sim.world.arms:
            frames += self.arm_frames(stamp)
            joints = JointState()
            joints.header.stamp = stamp
            joints.name = list(W.JOINTS)
            joints.position = [float(r.joints[j]) for j in W.JOINTS]
            joints.velocity = [float(r.joint_velocity[j]) for j in W.JOINTS]
            self.joint_pub.publish(joints)
        return frames

    def publish_sensors(self, stamp) -> List[float]:
        r = self.rover
        ranges = self.sim.world.scan(r)
        scan = LaserScan()
        scan.header.stamp = stamp
        scan.header.frame_id = f'{self.name}/laser'
        scan.angle_min = W.SCAN_ANGLE_MIN
        scan.angle_max = W.SCAN_ANGLE_MAX
        scan.angle_increment = (W.SCAN_ANGLE_MAX - W.SCAN_ANGLE_MIN) / (W.SCAN_RAYS - 1)
        scan.scan_time = 1.0 / SENSOR_RATE
        scan.range_min = W.SCAN_RANGE_MIN
        scan.range_max = W.SCAN_RANGE_MAX
        scan.ranges = ranges
        self.scan_pub.publish(scan)

        detections = DetectionArray()
        detections.header.stamp = stamp
        detections.header.frame_id = f'{self.name}/base_link'
        for d in self.sim.world.detections(r):
            detections.detections.append(Detection(kind=d.kind, id=d.id, range=float(d.range), bearing=float(d.bearing)))
        self.detections_pub.publish(detections)
        return ranges

    def publish_status(self, stamp):
        r = self.rover
        battery = BatteryState()
        battery.header.stamp = stamp
        battery.header.frame_id = f'{self.name}/base_link'
        battery.percentage = float(r.battery)
        battery.voltage = float(24.0 + 4.0 * r.battery)
        battery.present = True
        battery.power_supply_technology = BatteryState.POWER_SUPPLY_TECHNOLOGY_LION
        if self.sim.world.charging(r):
            battery.power_supply_status = BatteryState.POWER_SUPPLY_STATUS_CHARGING
        elif r.battery >= 1.0:
            battery.power_supply_status = BatteryState.POWER_SUPPLY_STATUS_FULL
        else:
            battery.power_supply_status = BatteryState.POWER_SUPPLY_STATUS_DISCHARGING
        self.battery_pub.publish(battery)
        self.bumps_pub.publish(Int32(data=r.bumps))
        self.samples_pub.publish(Int32(data=r.samples_onboard))
        if self.sim.world.arms:
            for side, pub in self.holding_pubs.items():
                pub.publish(String(data=r.holding[side]))


class MarsSim(Node):
    def __init__(self):
        super().__init__('mars_sim')
        self.declare_parameter('show_grid', True)
        self.declare_parameter('show_sensors', True)
        self.declare_parameter('cmd_vel_timeout', 1.0)
        self.declare_parameter('sand_slip', 0.6)
        self.declare_parameter('battery_start', 1.0)
        self.declare_parameter('battery_drain', 1.0)
        self.declare_parameter('seed', 0)
        self.declare_parameter('arms', False)
        self.declare_parameter('view_zoom', 1.0)       # > 1 zooms the map in around view_center
        self.declare_parameter('view_center_x', 10.0)
        self.declare_parameter('view_center_y', 10.0)
        self.declare_parameter('screenshot_dir', '/tmp')

        self.world = W.World(seed=self.get_parameter('seed').value)
        self.world.arms = self.get_parameter('arms').value
        self.apply_parameters()
        self.add_on_set_parameters_callback(self.on_parameters)
        self.static_tf = StaticTransformBroadcaster(self)
        self.tf = TransformBroadcaster(self)

        from mars_sim.render import Renderer   # imported here so `import mars_sim.node` works without a display
        from mars_sim.render import set_view
        self.renderer = Renderer()
        set_view(self.get_parameter('view_zoom').value, self.get_parameter('view_center_x').value,
                 self.get_parameter('view_center_y').value)
        self.hud = ''
        self.goals: List[Tuple[float, float, float]] = []
        self.scans: Dict[str, List[float]] = {}
        self.tick_future = Future()   # completed at every sensor tick; the drill action waits on it

        self.rovers: Dict[str, RoverIO] = {}
        self.add_rover('rover1', *W.LANDER, 0.0)

        self.create_service(SpawnRover, '/spawn_rover', self.on_spawn_rover)
        # mission_control places a whole world at once: keep every request, not the default 10
        self.create_service(PlaceObject, '/sim/place_object', self.on_place_object, qos_profile=QoSProfile(depth=500))
        self.create_service(Empty, '/sim/clear', self.on_clear)
        self.create_service(Trigger, '/sim/screenshot', self.on_screenshot)
        self.create_subscription(String, '/mission/hud', self.on_hud, 10)
        self.create_subscription(PoseArray, '/mission/goals', self.on_goals, 10)
        self.downlink_pub = self.create_publisher(String, '/earth/downlink', 10)
        self.lander_pub = self.create_publisher(Int32, '/lander/samples', 10)
        self.meteorites_pub = self.create_publisher(Int32, '/lander/meteorites', 10)
        self.markers_pub = self.create_publisher(MarkerArray, '/mars/markers', 10)
        self.judge_pub = self.create_publisher(String, '/judge/state', 10)

        self.last_step = time.monotonic()
        self.create_timer(1.0 / PHYSICS_RATE, self.on_physics)
        self.create_timer(1.0 / SENSOR_RATE, self.on_sensors)
        self.create_timer(1.0 / STATUS_RATE, self.on_status)
        self.create_timer(1.0 / RENDER_RATE, self.on_render)
        self.create_timer(1.0, self.publish_markers)
        self.get_logger().info('Mars Rover Academy simulator is up. rover1 is on the lander.')

    # ------------------------------------------------------------------ parameters
    def apply_parameters(self):
        self.world.cmd_timeout = self.get_parameter('cmd_vel_timeout').value
        self.world.sand_slip = self.get_parameter('sand_slip').value
        self.world.battery_drain = self.get_parameter('battery_drain').value

    def on_parameters(self, params):
        from rcl_interfaces.msg import SetParametersResult
        for p in params:
            if p.name == 'cmd_vel_timeout':
                self.world.cmd_timeout = p.value
            elif p.name == 'sand_slip':
                self.world.sand_slip = p.value
            elif p.name == 'battery_drain':
                self.world.battery_drain = p.value
            elif p.name == 'show_grid':
                self.renderer.ground_version = -1
        return SetParametersResult(successful=True)

    # ------------------------------------------------------------------ rovers and the world
    def add_rover(self, name: str, x: float, y: float, yaw: float) -> str:
        name = self.world.spawn_rover(name, x, y, yaw, battery=self.get_parameter('battery_start').value)
        self.rovers[name] = RoverIO(self, name)
        return name

    def on_spawn_rover(self, request, response):
        name = request.name.strip().strip('/')
        if name and not all(c.isalnum() or c == '_' for c in name):
            self.get_logger().warn(f'"{name}" is not a valid rover name (letters, digits and _ only)')
            name = ''
        response.name = self.add_rover(name or 'rover', request.x, request.y, request.yaw)
        self.get_logger().info(f'Spawned {response.name} at ({request.x:.1f}, {request.y:.1f})')
        return response

    def on_place_object(self, request, response):
        try:
            response.id = self.world.add_object(request.kind, request.x, request.y, request.radius, request.id)
        except ValueError as exc:
            self.get_logger().error(str(exc))
            response.id = ''
        return response

    def on_clear(self, request, response):
        self.world.clear()
        self.renderer.ground_version = -1
        return response

    def on_screenshot(self, request, response):
        path = os.path.join(self.get_parameter('screenshot_dir').value, f'mars_{int(time.time())}.png')
        self.renderer.save(path)
        response.success, response.message = True, path
        return response

    def on_hud(self, msg: String):
        self.hud = msg.data

    def on_goals(self, msg: PoseArray):
        self.goals = [(p.position.x, p.position.y, p.position.z or 0.5) for p in msg.poses]

    def downlink(self, rover: str, landmark: str):
        self.downlink_pub.publish(String(data=f'{rover}: photo of {landmark}'))

    # ------------------------------------------------------------------ timers
    def on_physics(self):
        now = time.monotonic()
        dt = min(max(now - self.last_step, 0.0), 0.1)
        self.last_step = now
        self.world.step(dt, now)
        stamp = self.get_clock().now().to_msg()
        self.tf.sendTransform([tf for io in self.rovers.values() for tf in io.publish_odom(stamp)])
        for event in self.world.events:
            self.get_logger().info(event)
        self.world.events.clear()

    def on_sensors(self):
        stamp = self.get_clock().now().to_msg()
        for name, io in self.rovers.items():
            self.scans[name] = io.publish_sensors(stamp)
        done, self.tick_future = self.tick_future, Future()
        done.set_result(True)

    def next_tick(self) -> Future:
        return self.tick_future

    def on_status(self):
        stamp = self.get_clock().now().to_msg()
        for io in self.rovers.values():
            io.publish_status(stamp)
        self.lander_pub.publish(Int32(data=self.world.delivered))
        self.meteorites_pub.publish(Int32(data=len(self.world.meteorites_home)))
        self.judge_pub.publish(String(data=json.dumps(self.world.judge_state())))

    def on_render(self):
        if self.renderer.closed():
            raise SystemExit
        self.renderer.draw(self.world, self.hud, self.goals, time.monotonic(),
                           show_grid=self.get_parameter('show_grid').value,
                           show_sensors=self.get_parameter('show_sensors').value,
                           scans=self.scans)

    def publish_markers(self):
        """The world as RViz markers, in the map frame."""
        out = MarkerArray()
        clear = Marker()
        clear.action = Marker.DELETEALL
        out.markers.append(clear)
        stamp = self.get_clock().now().to_msg()
        colours = {'rock': (0.38, 0.26, 0.2, 1.0), 'landmark': (0.45, 0.31, 0.24, 1.0), 'sand': (0.87, 0.66, 0.41, 0.6),
                   'crater': (0.63, 0.34, 0.19, 0.6), 'sample': (0.27, 0.8, 0.84, 1.0), 'drill_site': (1.0, 1.0, 1.0, 0.6),
                   'core': (0.9, 0.9, 0.9, 1.0), 'meteorite': (0.2, 0.2, 0.25, 1.0)}
        items = [('lander', 'lander', W.LANDER[0], W.LANDER[1], W.LANDER_RADIUS)]
        items += [(o.kind, o.id, o.x, o.y, o.radius) for o in self.world.objects.values()]
        for k, (kind, id_, x, y, radius) in enumerate(items):
            m = Marker()
            m.header.frame_id = 'map'
            m.header.stamp = stamp
            m.ns = kind
            m.id = k + 1
            m.type = Marker.SPHERE if kind in ('sample', 'core') else Marker.CYLINDER
            m.action = Marker.ADD
            height = {'rock': 0.6, 'landmark': 1.2, 'meteorite': 0.5}.get(kind, 0.02)
            m.pose.position.x, m.pose.position.y, m.pose.position.z = x, y, height / 2
            m.pose.orientation.w = 1.0
            m.scale.x = m.scale.y = 2 * radius
            m.scale.z = 2 * radius if m.type == Marker.SPHERE else height
            m.color.r, m.color.g, m.color.b, m.color.a = colours.get(kind, (0.5, 0.5, 0.55, 1.0))
            out.markers.append(m)
        self.markers_pub.publish(out)


def main(args=None):
    rclpy.init(args=args)
    node = None
    try:
        node = MarsSim()
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException, SystemExit):
        pass
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
