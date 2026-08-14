#AI GENERATED TESTING DOCUMENT FOR DISTANCE

import math
import time
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from std_srvs.srv import SetBool

def move_robot(publisher, linear_vel, angular_vel, duration):
    """Publishes velocity commands at 10Hz for a set duration, then stops."""
    msg = Twist()
    msg.linear.x = float(linear_vel)
    msg.angular.z = float(angular_vel)
    
    rate = 10
    steps = int(duration * rate)
    
    for _ in range(steps):
        publisher.publish(msg)
        time.sleep(1.0 / rate)
        
    # Full stop
    msg.linear.x = 0.0
    msg.angular.z = 0.0
    publisher.publish(msg)
    time.sleep(1.0) # Let the robot settle before next action

def set_tracking(node, client, state):
    """Calls the service and returns the distance if stopping."""
    req = SetBool.Request()
    req.data = state
    future = client.call_async(req)
    rclpy.spin_until_future_complete(node, future)
    
    if not state:
        return float(future.result().message)
    return 0.0

def main(args=None):
    rclpy.init(args=args)
    
    # Create a temporary node for testing
    tester_node = Node('distance_tester')
    
    cmd_pub = tester_node.create_publisher(Twist, '/jackal1/cmd_vel', 10)
    tracker_client = tester_node.create_client(SetBool, '/distance_tracking')
    
    tester_node.get_logger().info("Waiting for distance tracker service...")
    tracker_client.wait_for_service()
    tester_node.get_logger().info("Service found! Beginning tests...\n")
    
    try:
        # ==========================================
        # TEST 1: Straight Line (1 Meter)
        # ==========================================
        tester_node.get_logger().info("--- TEST 1: 1 Meter Straight Line ---")
        set_tracking(tester_node, tracker_client, True)
        
        # 0.2 m/s for 5 seconds = 1.0 meters
        move_robot(cmd_pub, linear_vel=0.2, angular_vel=0.0, duration=5.0)
        
        dist_1 = set_tracking(tester_node, tracker_client, False)
        tester_node.get_logger().info(f"RESULT: Travelled {dist_1:.3f} meters (Expected: ~1.000m)\n")
        
        # ==========================================
        # TEST 2: Spin In Place (360 degrees)
        # ==========================================
        tester_node.get_logger().info("--- TEST 2: Spin In Place ---")
        set_tracking(tester_node, tracker_client, True)
        
        # 0.5 rad/s for ~12.56 seconds = ~360 degrees (2*pi rad)
        move_robot(cmd_pub, linear_vel=0.0, angular_vel=0.5, duration=(2 * math.pi / 0.5))
        
        dist_2 = set_tracking(tester_node, tracker_client, False)
        tester_node.get_logger().info(f"RESULT: Travelled {dist_2:.3f} meters (Expected: ~0.000m)\n")
        
        # ==========================================
        # TEST 3: 1x1 Meter Square
        # ==========================================
        tester_node.get_logger().info("--- TEST 3: 1x1 Meter Square ---")
        set_tracking(tester_node, tracker_client, True)
        
        for i in range(4):
            tester_node.get_logger().info(f"Square side {i+1}/4...")
            # Drive straight 1 meter
            move_robot(cmd_pub, linear_vel=0.2, angular_vel=0.0, duration=5.0)
            # Turn 90 degrees (pi/2 radians)
            move_robot(cmd_pub, linear_vel=0.0, angular_vel=0.5, duration=(math.pi / 2 / 0.5))
            
        dist_3 = set_tracking(tester_node, tracker_client, False)
        tester_node.get_logger().info(f"RESULT: Travelled {dist_3:.3f} meters (Expected: ~4.000m)\n")
        
    except KeyboardInterrupt:
        tester_node.get_logger().info("Tests interrupted.")
    finally:
        # Stop robot if interrupted
        move_robot(cmd_pub, 0.0, 0.0, 0.1)
        tester_node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()