"""Mission 8 (boss): Turtle Express -- everything together: 3 subscribers, a publisher, 2 service clients

Every loop, decide from the state we can read from the topics:
  carrying a parcel?           -> go to DROP-OFF and call /turtle1/dropoff
  not carrying + parcel seen   -> rush to it and call /turtle1/pickup
  not carrying + nothing seen  -> patrol
"""
import math

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from std_msgs.msg import Bool
from std_srvs.srv import Empty
from turtlesim.msg import Pose
from turtlesim_plus_interfaces.msg import ScannerDataArray

DROPOFF = (9.38, 9.38)  # the drop-off zone (top-right corner)
PATROL = [(2.5, 2.5), (8.4, 2.5), (8.4, 8.4), (2.5, 8.4)]


class Delivery(Node):
    def __init__(self):
        super().__init__('delivery')
        self.pose = None
        self.scan = []
        self.carrying = False
        self.patrol_index = 0
        self.create_subscription(Pose, '/turtle1/pose', self.pose_callback, 10)
        self.create_subscription(ScannerDataArray, '/turtle1/scan', self.scan_callback, 10)
        self.create_subscription(Bool, '/turtle1/carrying_parcel', self.carrying_callback, 10)
        self.publisher = self.create_publisher(Twist, '/turtle1/cmd_vel', 10)
        self.pickup_client = self.create_client(Empty, '/turtle1/pickup')
        self.dropoff_client = self.create_client(Empty, '/turtle1/dropoff')
        self.pending = None  # the service request still waiting for an answer
        self.create_timer(0.05, self.control_loop)

    def pose_callback(self, msg: Pose):
        self.pose = msg

    def scan_callback(self, msg: ScannerDataArray):
        self.scan = msg.data

    def carrying_callback(self, msg: Bool):
        self.carrying = msg.data

    def call(self, client):
        if self.pending is None or self.pending.done():
            self.pending = client.call_async(Empty.Request())

    def distance_to(self, x: float, y: float) -> float:
        return math.hypot(x - self.pose.x, y - self.pose.y)

    def steer_to(self, x: float, y: float) -> Twist:
        cmd = Twist()
        error = math.atan2(y - self.pose.y, x - self.pose.x) - self.pose.theta
        error = math.atan2(math.sin(error), math.cos(error))
        cmd.angular.z = 6.0 * error
        if abs(error) < 0.5:
            cmd.linear.x = min(2.0 * self.distance_to(x, y), 3.0)
        return cmd

    def control_loop(self):
        if self.pose is None:
            return
        cmd = Twist()
        if self.carrying:
            if self.distance_to(*DROPOFF) < 0.6:
                self.call(self.dropoff_client)  # arrived: stop (empty cmd) and deliver
            else:
                cmd = self.steer_to(*DROPOFF)
        else:
            parcels = [d for d in self.scan if d.type == 'Parcel']
            if parcels:
                target = min(parcels, key=lambda d: d.distance)
                cmd.angular.z = 5.0 * target.angle
                cmd.linear.x = min(2.0 * target.distance, 3.0)
                if target.distance < 1.5 and abs(target.angle) < 0.4:
                    self.call(self.pickup_client)
            else:
                x, y = PATROL[self.patrol_index]
                if self.distance_to(x, y) < 0.5:
                    self.patrol_index = (self.patrol_index + 1) % len(PATROL)
                cmd = self.steer_to(x, y)
        self.publisher.publish(cmd)


def main():
    rclpy.init()
    node = Delivery()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
