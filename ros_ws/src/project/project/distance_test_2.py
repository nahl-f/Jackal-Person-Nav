#!/usr/bin/env python3

import math
import time

import rclpy
from rclpy.node import Node

from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from std_srvs.srv import SetBool


class DistanceAccuracyTest(Node):

    def __init__(self):
        super().__init__('distance_accuracy_test')

        # ---------------------------------------------------------
        # Fixed topics for your Jackal
        # ---------------------------------------------------------

        self.cmd_vel_topic = '/jackal1/platform/cmd_vel_unstamped'
        self.odom_topic = '/jackal1/platform/odom/filtered'
        self.distance_service = '/distance_tracking'

        # ---------------------------------------------------------
        # ROS interfaces
        # ---------------------------------------------------------

        self.cmd_pub = self.create_publisher(
            Twist,
            self.cmd_vel_topic,
            10
        )

        self.odom_sub = self.create_subscription(
            Odometry,
            self.odom_topic,
            self.odom_callback,
            20
        )

        self.distance_client = self.create_client(
            SetBool,
            self.distance_service
        )

        # Publish velocity at 20 Hz
        self.cmd_timer = self.create_timer(
            0.05,
            self.publish_cmd
        )

        # ---------------------------------------------------------
        # Current command
        # ---------------------------------------------------------

        self.linear_velocity = 0.0
        self.angular_velocity = 0.0

        # ---------------------------------------------------------
        # Independent odometry distance
        # ---------------------------------------------------------

        self.last_x = None
        self.last_y = None
        self.odom_distance = 0.0

        self.collecting = False

        # ---------------------------------------------------------
        # Test state machine
        # ---------------------------------------------------------

        self.test_running = False
        self.test_start_time = None
        self.test_duration = 0.0
        self.expected_distance = 0.0
        self.test_name = ""

        self.timer = self.create_timer(
            0.1,
            self.test_loop
        )

        self.get_logger().info(
            'Distance accuracy test initialized.'
        )

        self.get_logger().info(
            f'Command topic: {self.cmd_vel_topic}'
        )

        self.get_logger().info(
            f'Odometry topic: {self.odom_topic}'
        )

    # =============================================================
    # VELOCITY PUBLISHER
    # =============================================================

    def publish_cmd(self):

        msg = Twist()

        msg.linear.x = self.linear_velocity
        msg.angular.z = self.angular_velocity

        self.cmd_pub.publish(msg)

    # =============================================================
    # ODOMETRY
    # =============================================================

    def odom_callback(self, msg):

        if not self.collecting:
            return

        x = msg.pose.pose.position.x
        y = msg.pose.pose.position.y

        if self.last_x is None:
            self.last_x = x
            self.last_y = y
            return

        dx = x - self.last_x
        dy = y - self.last_y

        step_distance = math.hypot(dx, dy)

        # Same threshold as your DistanceTracker
        if step_distance > 0.005:
            self.odom_distance += step_distance

            self.last_x = x
            self.last_y = y

    # =============================================================
    # RESET MEASUREMENTS
    # =============================================================

    def reset_measurements(self):

        self.last_x = None
        self.last_y = None
        self.odom_distance = 0.0

    # =============================================================
    # START DISTANCE TRACKER
    # =============================================================

    def start_distance_tracking(self):

        if not self.distance_client.wait_for_service(
            timeout_sec=2.0
        ):
            self.get_logger().error(
                'Distance tracking service not available!'
            )
            return False

        request = SetBool.Request()
        request.data = True

        future = self.distance_client.call_async(request)

        # Let ROS process until response arrives
        while rclpy.ok() and not future.done():
            rclpy.spin_once(self, timeout_sec=0.05)

        if future.result() is None:
            self.get_logger().error(
                'Failed to start distance tracking.'
            )
            return False

        self.get_logger().info(
            'DistanceTracker started.'
        )

        return True

    # =============================================================
    # STOP DISTANCE TRACKER
    # =============================================================

    def stop_distance_tracking(self):

        request = SetBool.Request()
        request.data = False

        future = self.distance_client.call_async(request)

        while rclpy.ok() and not future.done():
            rclpy.spin_once(self, timeout_sec=0.05)

        if future.result() is None:
            self.get_logger().error(
                'Failed to stop distance tracking.'
            )
            return None

        message = future.result().message

        self.get_logger().info(
            f'DistanceTracker returned: {message}'
        )

        try:
            return float(message)
        except ValueError:
            self.get_logger().error(
                f'Could not convert "{message}" to float.'
            )
            return None

    # =============================================================
    # ROBOT STOP
    # =============================================================

    def stop_robot(self):

        self.linear_velocity = 0.0
        self.angular_velocity = 0.0

    # =============================================================
    # START A TEST
    # =============================================================

    def start_test(
        self,
        name,
        distance,
        velocity
    ):

        self.get_logger().info('')
        self.get_logger().info(
            '=============================================='
        )
        self.get_logger().info(
            f'STARTING TEST: {name}'
        )
        self.get_logger().info(
            f'Expected distance: {distance:.3f} m'
        )
        self.get_logger().info(
            f'Commanded velocity: {velocity:.3f} m/s'
        )
        self.get_logger().info(
            '=============================================='
        )

        self.stop_robot()

        self.reset_measurements()

        time.sleep(0.5)

        if not self.start_distance_tracking():
            return False

        # Start odometry collection
        self.collecting = True

        # Distance / velocity = required duration
        self.test_duration = distance / velocity

        self.expected_distance = distance
        self.test_name = name

        self.test_start_time = time.monotonic()
        self.test_running = True

        self.linear_velocity = velocity

        return True

    # =============================================================
    # TEST LOOP
    # =============================================================

    def test_loop(self):

        if not self.test_running:
            return

        elapsed = time.monotonic() - self.test_start_time

        if elapsed < self.test_duration:
            return

        # ---------------------------------------------------------
        # Test finished
        # ---------------------------------------------------------

        self.stop_robot()

        # Give odom a little time to arrive
        self.collecting = False

        self.test_running = False

        # Wait for robot to stop
        self.get_logger().info(
            'Test motion finished.'
        )

        # ---------------------------------------------------------
        # Get DistanceTracker result
        # ---------------------------------------------------------

        tracker_distance = self.stop_distance_tracking()

        # ---------------------------------------------------------
        # Results
        # ---------------------------------------------------------

        self.get_logger().info('')
        self.get_logger().info(
            '=============== RESULTS ==============='
        )

        self.get_logger().info(
            f'Test:              {self.test_name}'
        )

        self.get_logger().info(
            f'Expected:          '
            f'{self.expected_distance:.4f} m'
        )

        self.get_logger().info(
            f'Independent odom:  '
            f'{self.odom_distance:.4f} m'
        )

        if tracker_distance is not None:

            tracker_error = (
                tracker_distance -
                self.expected_distance
            )

            tracker_percent = (
                abs(tracker_error) /
                self.expected_distance *
                100.0
            )

            comparison_error = (
                tracker_distance -
                self.odom_distance
            )

            self.get_logger().info(
                f'DistanceTracker:   '
                f'{tracker_distance:.4f} m'
            )

            self.get_logger().info(
                f'Tracker error:     '
                f'{tracker_error:+.4f} m'
            )

            self.get_logger().info(
                f'Tracker error %:   '
                f'{tracker_percent:.3f}%'
            )

            self.get_logger().info(
                f'Tracker vs odom:   '
                f'{comparison_error:+.6f} m'
            )

        self.get_logger().info(
            '========================================'
        )

        # ---------------------------------------------------------
        # Next test
        # ---------------------------------------------------------

        self.schedule_next_test()

    # =============================================================
    # TEST SEQUENCE
    # =============================================================

    def schedule_next_test(self):

        # Tests are stored on the first call
        if not hasattr(self, 'test_index'):
            self.test_index = 0

        tests = [
            ('1 meter', 1.0, 0.20),
            ('2 meters', 2.0, 0.20),
            ('5 meters', 5.0, 0.20),
            ('10 meters', 10.0, 0.20),
        ]

        self.test_index += 1

        if self.test_index >= len(tests):

            self.stop_robot()

            self.get_logger().info('')
            self.get_logger().info(
                '========================================'
            )
            self.get_logger().info(
                'ALL TESTS COMPLETE'
            )
            self.get_logger().info(
                '========================================'
            )

            # Don't immediately kill the node;
            # publish zero velocity for safety.
            self.destroy_timer(self.timer)

            return

        # Small pause between tests
        time.sleep(1.0)

        name, distance, velocity = tests[self.test_index]

        self.start_test(
            name,
            distance,
            velocity
        )

    # =============================================================
    # INITIAL START
    # =============================================================

    def begin(self):

        time.sleep(1.0)

        self.test_index = -1

        self.schedule_next_test()


def main(args=None):

    rclpy.init(args=args)

    node = DistanceAccuracyTest()

    node.begin()

    try:
        rclpy.spin(node)

    except KeyboardInterrupt:
        pass

    finally:

        node.stop_robot()

        node.destroy_node()

        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()