"""Mission 5: Turtle Eyes -- subscriber + publisher in one node (closed loop / P controller)"""
import math

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseArray, Twist
from turtlesim.msg import Pose

MAX_SPEED = 3.0   # top speed (m/s)
K_LINEAR = 2.0    # further away -> faster
K_ANGULAR = 6.0   # pointing further off -> turn harder


class GoToGoal(Node):
    def __init__(self):
        super().__init__('go_to_goal')
        self.pose = None   # latest turtle pose (None = not received yet)
        self.goals = []    # remaining flags, the first one is the next target
        self.create_subscription(Pose, '/turtle1/pose', self.pose_callback, 10)
        self.create_subscription(PoseArray, '/mission/goals', self.goals_callback, 10)
        self.publisher = self.create_publisher(Twist, '/turtle1/cmd_vel', 10)
        self.create_timer(0.05, self.control_loop)  # 20 Hz

    def pose_callback(self, msg: Pose):
        self.pose = msg

    def goals_callback(self, msg: PoseArray):
        self.goals = [(p.position.x, p.position.y) for p in msg.poses]

    def control_loop(self):
        cmd = Twist()
        if self.pose is not None and self.goals:
            goal_x, goal_y = self.goals[0]
            dx = goal_x - self.pose.x
            dy = goal_y - self.pose.y
            distance = math.hypot(dx, dy)
            # angle we should face minus angle we face = heading error (wrapped to -pi..pi)
            error = math.atan2(dy, dx) - self.pose.theta
            error = math.atan2(math.sin(error), math.cos(error))

            cmd.angular.z = K_ANGULAR * error
            if abs(error) < 0.5:  # only drive once we roughly face the goal
                cmd.linear.x = min(K_LINEAR * distance, MAX_SPEED)
        self.publisher.publish(cmd)


def main():
    rclpy.init()
    node = GoToGoal()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
