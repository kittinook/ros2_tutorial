"""Mission 10: Long Reach -- inverse kinematics for a planar 2-link arm

flag (world) -> turtle frame -> pick an arm -> IK -> joint_command
"""
import math

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseArray
from sensor_msgs.msg import JointState
from turtlesim.msg import Pose

L1, L2 = 0.8, 0.7                           # upper arm, forearm
SHOULDER_Y = {'left': 0.3, 'right': -0.3}   # shoulders sit 0.3 left/right of the turtle's centre
HOME = {'left': (1.2, -2.4), 'right': (-1.2, 2.4)}


def to_turtle_frame(pose: Pose, x: float, y: float):
    """World point -> turtle frame (x forward, y left)."""
    dx, dy = x - pose.x, y - pose.y
    c, s = math.cos(pose.theta), math.sin(pose.theta)
    return c * dx + s * dy, -s * dx + c * dy


def inverse_kinematics(x: float, y: float, side: str):
    """Joint angles (shoulder, elbow) that put the gripper at (x, y) in the turtle frame, or None."""
    dx, dy = x, y - SHOULDER_Y[side]                 # target seen from the shoulder
    cos_q2 = (dx * dx + dy * dy - L1 * L1 - L2 * L2) / (2 * L1 * L2)  # law of cosines
    if abs(cos_q2) > 1.0:
        return None                                  # out of reach
    q2 = math.acos(cos_q2)
    if side == 'left':
        q2 = -q2                                     # bend the elbow outwards, away from the body
    q1 = math.atan2(dy, dx) - math.atan2(L2 * math.sin(q2), L1 + L2 * math.cos(q2))
    q1 = math.atan2(math.sin(q1), math.cos(q1))
    return q1, q2


class ArmReach(Node):
    def __init__(self):
        super().__init__('arm_reach')
        self.pose = None
        self.goals = []
        self.create_subscription(Pose, '/turtle1/pose', self.pose_callback, 10)
        self.create_subscription(PoseArray, '/mission/goals', self.goals_callback, 10)
        self.publisher = self.create_publisher(JointState, '/turtle1/joint_command', 10)
        self.create_timer(0.1, self.control_loop)

    def pose_callback(self, msg: Pose):
        self.pose = msg

    def goals_callback(self, msg: PoseArray):
        self.goals = [(p.position.x, p.position.y) for p in msg.poses]

    def control_loop(self):
        if self.pose is None or not self.goals:
            return
        x, y = to_turtle_frame(self.pose, *self.goals[0])
        # use the arm on the flag's side; fall back to the other one if it can't reach
        sides = ['left', 'right'] if y >= 0 else ['right', 'left']
        for side in sides:
            angles = inverse_kinematics(x, y, side)
            if angles is not None:
                break
        else:
            self.get_logger().warning('flag out of reach', throttle_duration_sec=1.0)
            return
        other = 'right' if side == 'left' else 'left'
        cmd = JointState()
        cmd.name = [f'{side}_shoulder', f'{side}_elbow', f'{other}_shoulder', f'{other}_elbow']
        cmd.position = [*angles, *HOME[other]]       # the idle arm tucks itself in
        self.publisher.publish(cmd)


def main():
    rclpy.init()
    node = ArmReach()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
