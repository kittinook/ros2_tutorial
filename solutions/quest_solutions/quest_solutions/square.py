"""Mission 4: My First Node -- a pure publisher that draws a square by timing (open loop)"""
import math

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist

SPEED = 2.0       # forward speed (m/s)
TURN_SPEED = 2.0  # turning speed (rad/s)
SIDE = 4.0        # side length (m)


class Square(Node):
    def __init__(self):
        super().__init__('square')
        self.publisher = self.create_publisher(Twist, '/turtle1/cmd_vel', 10)
        self.timer = self.create_timer(0.1, self.timer_callback)  # called every 0.1 s (10 Hz)

        # the plan: (forward speed, turn speed, duration) x 4 sides
        one_side = [(SPEED, 0.0, SIDE / SPEED), (0.0, TURN_SPEED, (math.pi / 2) / TURN_SPEED)]
        self.plan = one_side * 4
        self.step = 0
        self.step_started = self.now()

    def now(self) -> float:
        return self.get_clock().now().nanoseconds / 1e9

    def timer_callback(self):
        if self.step >= len(self.plan):
            self.publisher.publish(Twist())  # an empty Twist() = zero velocity = stop
            return
        linear, angular, duration = self.plan[self.step]
        if self.now() - self.step_started >= duration:
            self.step += 1  # this step is over -> next step
            self.step_started += duration
            return
        msg = Twist()
        msg.linear.x = linear
        msg.angular.z = angular
        self.publisher.publish(msg)


def main():
    rclpy.init()
    node = Square()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
