import math
import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry
from std_srvs.srv import SetBool

class DistanceTracker(Node):
    def __init__(self):
        super().__init__('distance_tracker')

        self.odom_sub = self.create_subscription(
            Odometry,
            '/jackal1/platform/odom/filtered',
            self.odom_callback,
            10
        )
        
        self.srv = self.create_service(
            SetBool,
            '/distance_tracking',
            self.tracking_service_callback
        )

        # Distance Tracking State
        self.is_tracking = False
        self.total_distance = 0.0
        self.last_x = None
        self.last_y = None

        # minimum distance
        self.min_distance = 0.005 

        self.get_logger().info('Distance Tracker Service Node initialized.')

    def tracking_service_callback(self, request, response):
        if request.data == True: 
            self.is_tracking = True
            self.total_distance = 0.0
            self.last_x = None
            self.last_y = None
            
            response.success = True
            response.message = "Tracking started. Reset total distance to 0.0 m."
            self.get_logger().info("Started distance tracking.")

        else: 
            self.is_tracking = False
            response.success = True
            response.message = f"{self.total_distance:.3f}"
            self.get_logger().info(
                f"Stopped tracking. Final Distance: {self.total_distance:.2f} meters"
            )

        return response

    def odom_callback(self, msg):
        if not self.is_tracking:
            return

        curr_x = msg.pose.pose.position.x
        curr_y = msg.pose.pose.position.y

        # set start position for first time
        if self.last_x is None or self.last_y is None:
            self.last_x = curr_x
            self.last_y = curr_y
            return

        # calculate distance (sqrt(dx^2+dy^2))
        dx = curr_x - self.last_x
        dy = curr_y - self.last_y
        step_distance = math.hypot(dx, dy)

        # ignore small fluctuations
        if step_distance > self.min_distance:
            self.total_distance += step_distance
            self.last_x = curr_x
            self.last_y = curr_y


def main(args=None):
    rclpy.init(args=args)
    node = DistanceTracker()
    try:
        while rclpy.ok():
            rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()