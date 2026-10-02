"""Mission 7: Turtle Team -- the reusable pizza_hunter

Two differences from mission 6:
  1. topic/service names have no leading / (relative), so they live under the node's namespace:
     run it in namespace /turtle2 and 'cmd_vel' becomes /turtle2/cmd_vel
  2. the knobs worth tuning are parameters (max_speed, patrol_start)
"""
import math

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from std_srvs.srv import Empty
from turtlesim.msg import Pose
from turtlesim_plus_interfaces.msg import ScannerDataArray

PATROL = [(2.5, 2.5), (8.4, 2.5), (8.4, 8.4), (2.5, 8.4)]


class PizzaHunter(Node):
    def __init__(self):
        super().__init__('pizza_hunter')
        self.declare_parameter('max_speed', 3.0)
        self.declare_parameter('patrol_start', 0)  # start at different corners so the two turtles don't follow each other
        self.scan = []
        self.pose = None
        self.patrol_index = self.get_parameter('patrol_start').value % len(PATROL)
        self.create_subscription(ScannerDataArray, 'scan', self.scan_callback, 10)
        self.create_subscription(Pose, 'pose', self.pose_callback, 10)
        self.publisher = self.create_publisher(Twist, 'cmd_vel', 10)
        self.eat_client = self.create_client(Empty, 'eat')
        self.eat_future = None
        self.create_timer(0.05, self.control_loop)

    def scan_callback(self, msg: ScannerDataArray):
        self.scan = msg.data

    def pose_callback(self, msg: Pose):
        self.pose = msg

    def max_speed(self) -> float:
        # read every time -> `ros2 param set` takes effect immediately
        return self.get_parameter('max_speed').value

    def steer_to(self, x: float, y: float) -> Twist:
        cmd = Twist()
        error = math.atan2(y - self.pose.y, x - self.pose.x) - self.pose.theta
        error = math.atan2(math.sin(error), math.cos(error))
        cmd.angular.z = 6.0 * error
        if abs(error) < 0.5:
            cmd.linear.x = self.max_speed()
        return cmd

    def eat(self):
        if self.eat_future is None or self.eat_future.done():
            self.eat_future = self.eat_client.call_async(Empty.Request())

    def control_loop(self):
        if self.pose is None:
            return
        pizzas = [d for d in self.scan if d.type == 'Pizza']
        if pizzas:
            target = min(pizzas, key=lambda d: d.distance)
            cmd = Twist()
            cmd.angular.z = 5.0 * target.angle
            cmd.linear.x = min(2.0 * target.distance, self.max_speed())
            if target.distance < 1.5 and abs(target.angle) < 0.4:
                self.eat()
        else:
            x, y = PATROL[self.patrol_index]
            if math.hypot(x - self.pose.x, y - self.pose.y) < 0.5:
                self.patrol_index = (self.patrol_index + 1) % len(PATROL)
            cmd = self.steer_to(x, y)
        self.publisher.publish(cmd)


def main():
    rclpy.init()
    node = PizzaHunter()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
