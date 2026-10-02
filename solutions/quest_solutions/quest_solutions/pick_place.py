"""Mission 11: Pick & Place -- inverse kinematics + gripper service + a small state machine

    choose a pizza -> reach it -> close the gripper -> carry it over the plate -> open the gripper -> repeat
"""
import math

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseArray
from sensor_msgs.msg import JointState
from std_srvs.srv import SetBool
from turtlesim.msg import Pose

L1, L2 = 0.8, 0.7
SHOULDER_Y = {'left': 0.3, 'right': -0.3}
PLATE = (1.25, 0.0)   # plate centre in the turtle frame
TOLERANCE = 0.02      # rad: close enough to the joint target to call it "arrived"


def to_turtle_frame(pose: Pose, x: float, y: float):
    dx, dy = x - pose.x, y - pose.y
    c, s = math.cos(pose.theta), math.sin(pose.theta)
    return c * dx + s * dy, -s * dx + c * dy


def inverse_kinematics(x: float, y: float, side: str):
    dx, dy = x, y - SHOULDER_Y[side]
    cos_q2 = (dx * dx + dy * dy - L1 * L1 - L2 * L2) / (2 * L1 * L2)
    if abs(cos_q2) > 1.0:
        return None
    q2 = math.acos(cos_q2)
    if side == 'left':
        q2 = -q2
    q1 = math.atan2(dy, dx) - math.atan2(L2 * math.sin(q2), L1 + L2 * math.cos(q2))
    return math.atan2(math.sin(q1), math.cos(q1)), q2


class PickPlace(Node):
    def __init__(self):
        super().__init__('pick_place')
        self.pose = None
        self.items = []    # pizzas still to serve (world x, y)
        self.joints = {}   # joint name -> current angle
        self.create_subscription(Pose, '/turtle1/pose', self.pose_callback, 10)
        self.create_subscription(PoseArray, '/mission/items', self.items_callback, 10)
        self.create_subscription(JointState, '/turtle1/joint_states', self.joints_callback, 10)
        self.publisher = self.create_publisher(JointState, '/turtle1/joint_command', 10)
        self.grippers = {side: self.create_client(SetBool, f'/turtle1/{side}_gripper') for side in ('left', 'right')}
        self.state = 'choose'
        self.side = 'left'       # the arm doing the work right now
        self.target = (0.0, 0.0)  # its joint target
        self.future = None       # pending gripper request
        self.create_timer(0.05, self.loop)

    def pose_callback(self, msg: Pose):
        self.pose = msg

    def items_callback(self, msg: PoseArray):
        self.items = [(p.position.x, p.position.y) for p in msg.poses]

    def joints_callback(self, msg: JointState):
        self.joints = dict(zip(msg.name, msg.position))

    def move_arm(self, side: str, angles):
        self.side, self.target = side, angles
        cmd = JointState()
        cmd.name = [f'{side}_shoulder', f'{side}_elbow']
        cmd.position = list(angles)
        self.publisher.publish(cmd)

    def arrived(self) -> bool:
        q = (self.joints.get(f'{self.side}_shoulder'), self.joints.get(f'{self.side}_elbow'))
        return None not in q and all(abs(a - b) < TOLERANCE for a, b in zip(q, self.target))

    def gripper(self, close: bool):
        self.future = self.grippers[self.side].call_async(SetBool.Request(data=close))

    def loop(self):
        if self.pose is None:
            return
        if self.state == 'choose':
            todo = [to_turtle_frame(self.pose, *item) for item in self.items]
            # /mission/items may lag a moment behind: skip anything already on the plate
            todo = [(x, y) for x, y in todo if math.hypot(x - PLATE[0], y - PLATE[1]) > 0.5]
            if not todo:
                return                                   # all served
            x, y = todo[0]
            side = 'left' if y >= 0 else 'right'
            angles = inverse_kinematics(x, y, side)
            if angles is None:
                side = 'right' if side == 'left' else 'left'
                angles = inverse_kinematics(x, y, side)
            if angles is None:
                self.get_logger().warning('pizza out of reach', throttle_duration_sec=1.0)
                return
            self.move_arm(side, angles)
            self.state = 'reach'
        elif self.state == 'reach' and self.arrived():
            self.gripper(True)
            self.state = 'grab'
        elif self.state == 'grab' and self.future.done():
            if self.future.result().success:
                self.move_arm(self.side, inverse_kinematics(*PLATE, self.side))
                self.state = 'carry'
            else:
                self.get_logger().info(self.future.result().message)
                self.gripper(False)
                self.state = 'retry'
        elif self.state == 'carry' and self.arrived():
            self.gripper(False)
            self.state = 'drop'
        elif self.state in ('drop', 'retry') and self.future.done():
            self.state = 'choose'


def main():
    rclpy.init()
    node = PickPlace()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
