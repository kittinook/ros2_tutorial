"""Mission 12 (boss): Heavy Lifting -- mobile manipulation with both arms

    approach a crate -> grip it with BOTH grippers -> drive it into DROP-OFF -> let go -> back off
"""
import math

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Point, PoseArray, Twist
from sensor_msgs.msg import JointState
from std_srvs.srv import SetBool
from turtlesim.msg import Pose

L1, L2 = 0.8, 0.7
SHOULDER_Y = {'left': 0.3, 'right': -0.3}
DROPOFF = (9.38, 9.38)
REACH = 1.0        # crate centre this far in front of the turtle when gripping
GRIP_Y = 0.35      # grippers this far left/right of the crate centre


def inverse_kinematics(x: float, y: float, side: str):
    dx, dy = x, y - SHOULDER_Y[side]
    cos_q2 = (dx * dx + dy * dy - L1 * L1 - L2 * L2) / (2 * L1 * L2)
    q2 = math.acos(max(-1.0, min(1.0, cos_q2)))
    if side == 'left':
        q2 = -q2
    q1 = math.atan2(dy, dx) - math.atan2(L2 * math.sin(q2), L1 + L2 * math.cos(q2))
    return q1, q2


def wrap(angle: float) -> float:
    return math.atan2(math.sin(angle), math.cos(angle))


class CrateMover(Node):
    def __init__(self):
        super().__init__('crate_mover')
        self.pose = None
        self.crates = []
        self.tips = {}
        self.create_subscription(Pose, '/turtle1/pose', self.pose_callback, 10)
        self.create_subscription(PoseArray, '/mission/items', self.items_callback, 10)
        for side in ('left', 'right'):
            self.create_subscription(Point, f'/turtle1/{side}_arm/tip',
                                     lambda msg, side=side: self.tips.__setitem__(side, (msg.x, msg.y)), 10)
        self.cmd_pub = self.create_publisher(Twist, '/turtle1/cmd_vel', 10)
        self.joint_pub = self.create_publisher(JointState, '/turtle1/joint_command', 10)
        self.grippers = {side: self.create_client(SetBool, f'/turtle1/{side}_gripper') for side in ('left', 'right')}
        self.futures = []
        self.state = 'approach'
        self.backoff_until = 0.0
        self.create_timer(0.05, self.loop)

    def pose_callback(self, msg: Pose):
        self.pose = msg

    def items_callback(self, msg: PoseArray):
        self.crates = [(p.position.x, p.position.y) for p in msg.poses]

    def now(self) -> float:
        return self.get_clock().now().nanoseconds / 1e9

    def hold_arms_out(self):
        """Both grippers in front of the turtle, one on each side of where the crate will be."""
        cmd = JointState()
        cmd.name = ['left_shoulder', 'left_elbow', 'right_shoulder', 'right_elbow']
        cmd.position = [*inverse_kinematics(REACH, GRIP_Y, 'left'), *inverse_kinematics(REACH, -GRIP_Y, 'right')]
        self.joint_pub.publish(cmd)

    def grippers_set(self, close: bool):
        self.futures = [client.call_async(SetBool.Request(data=close)) for client in self.grippers.values()]

    def heading_error(self, x: float, y: float) -> float:
        return wrap(math.atan2(y - self.pose.y, x - self.pose.x) - self.pose.theta)

    def loop(self):
        if self.pose is None:
            return
        cmd = Twist()
        if self.state == 'approach':
            self.hold_arms_out()
            if self.crates:
                x, y = min(self.crates, key=lambda c: math.hypot(c[0] - self.pose.x, c[1] - self.pose.y))
                distance = math.hypot(x - self.pose.x, y - self.pose.y)
                error = self.heading_error(x, y)
                cmd.angular.z = 4.0 * error
                if abs(error) < 0.3:
                    cmd.linear.x = max(-0.5, min(2.0, 1.5 * (distance - REACH)))
                if abs(distance - REACH) < 0.06 and abs(error) < 0.05:
                    cmd = Twist()
                    self.grippers_set(True)
                    self.state = 'grip'
        elif self.state == 'grip':
            if all(f.done() for f in self.futures):
                if all(f.result().success for f in self.futures):
                    self.state = 'carry'
                else:                                    # missed: open up and try again
                    self.grippers_set(False)
                    self.state = 'approach'
        elif self.state == 'carry' and len(self.tips) == 2:
            crate = ((self.tips['left'][0] + self.tips['right'][0]) / 2,
                     (self.tips['left'][1] + self.tips['right'][1]) / 2)
            if math.hypot(crate[0] - DROPOFF[0], crate[1] - DROPOFF[1]) < 0.4:
                self.grippers_set(False)                 # in the zone: put it down
                self.backoff_until = self.now() + 1.0
                self.state = 'backoff'
            else:
                error = self.heading_error(*DROPOFF)
                cmd.angular.z = 3.0 * error
                if abs(error) < 0.3:
                    cmd.linear.x = 1.5
        elif self.state == 'backoff':
            if self.now() < self.backoff_until:
                cmd.linear.x = -1.0
            else:
                self.state = 'approach'
        self.cmd_pub.publish(cmd)


def main():
    rclpy.init()
    node = CrateMover()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
