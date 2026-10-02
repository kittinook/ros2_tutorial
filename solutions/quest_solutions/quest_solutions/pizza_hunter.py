"""Mission 6: Pizza Hunter -- subscribers (scan, pose) + publisher (cmd_vel) + service client (eat)"""
import math

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from std_srvs.srv import Empty
from turtlesim.msg import Pose
from turtlesim_plus_interfaces.msg import ScannerDataArray

# when no pizza is in sight, patrol around these points (a square around the map)
PATROL = [(2.5, 2.5), (8.4, 2.5), (8.4, 8.4), (2.5, 8.4)]


class PizzaHunter(Node):
    def __init__(self):
        super().__init__('pizza_hunter')
        self.scan = []
        self.pose = None
        self.patrol_index = 0
        self.create_subscription(ScannerDataArray, '/turtle1/scan', self.scan_callback, 10)
        self.create_subscription(Pose, '/turtle1/pose', self.pose_callback, 10)
        self.publisher = self.create_publisher(Twist, '/turtle1/cmd_vel', 10)
        self.eat_client = self.create_client(Empty, '/turtle1/eat')
        self.eat_future = None
        self.create_timer(0.05, self.control_loop)

    def scan_callback(self, msg: ScannerDataArray):
        self.scan = msg.data

    def pose_callback(self, msg: Pose):
        self.pose = msg

    def steer_to(self, x: float, y: float) -> Twist:
        """Same recipe as mission 5: face the point (x, y) and drive to it"""
        cmd = Twist()
        error = math.atan2(y - self.pose.y, x - self.pose.x) - self.pose.theta
        error = math.atan2(math.sin(error), math.cos(error))
        cmd.angular.z = 6.0 * error
        if abs(error) < 0.5:
            cmd.linear.x = 3.0
        return cmd

    def eat(self):
        # only send a new request once the previous one was answered, so we don't spam
        if self.eat_future is None or self.eat_future.done():
            self.eat_future = self.eat_client.call_async(Empty.Request())

    def control_loop(self):
        if self.pose is None:
            return
        pizzas = [d for d in self.scan if d.type == 'Pizza']
        if pizzas:
            target = min(pizzas, key=lambda d: d.distance)  # the closest one
            cmd = Twist()
            cmd.angular.z = 5.0 * target.angle              # angle: pizza is to the left (+) / right (-)
            cmd.linear.x = min(2.0 * target.distance, 3.0)
            if target.distance < 1.5 and abs(target.angle) < 0.4:
                self.eat()
        else:
            x, y = PATROL[self.patrol_index]
            if math.hypot(x - self.pose.x, y - self.pose.y) < 0.5:
                self.patrol_index = (self.patrol_index + 1) % len(PATROL)  # reached -> next point
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
