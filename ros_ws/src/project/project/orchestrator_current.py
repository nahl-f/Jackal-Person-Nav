import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from geometry_msgs.msg import PoseStamped
from std_srvs.srv import SetBool
from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult
import yaml
import json
import math

from vision_interfaces.action import FindPerson 

class JackalNav(Node):
    def __init__(self):
        super().__init__('jackal_navigation')
        self.navigator = BasicNavigator(namespace='jackal1')

        # declare parameters for map, locations, and scenarios
        self.declare_parameter('map_file', '')
        self.declare_parameter('location_file', '')
        self.declare_parameter('scenario_file', '')
        self.declare_parameter('scenario', 'scenario_1')

        # set parameters from launch file
        map_yaml = self.get_parameter('map_file').get_parameter_value().string_value
        locations_json = self.get_parameter('location_file').get_parameter_value().string_value
        scenarios_json = self.get_parameter('scenario_file').get_parameter_value().string_value
        self.target_scenario = self.get_parameter('scenario').get_parameter_value().string_value
        
        
        # action client for vision server
        self.vision_client = ActionClient(self, FindPerson, 'find_person')

        # client for distance calculation server
        self.distance_client = self.create_client(SetBool, '/distance_tracking')
        
        # Load map data for conversion
        with open(map_yaml, 'r') as f:
            map_data = yaml.safe_load(f)
            self.resolution = map_data['resolution']
            self.origin_x = map_data['origin'][0]
            self.origin_y = map_data['origin'][1]
        self.get_logger().info(f"map parsed! {map_yaml}")
            
        # Store locations
        with open(locations_json, 'r') as f:
            data = json.load(f)
            self.points = data['locations'] 
            self.image_height = data.get('image_height')
            print(self.points)
        self.get_logger().info("locations received!")
            
        # Store scenarios
        with open(scenarios_json, 'r') as f:
            self.scenarios = json.load(f)
        self.get_logger().info("scenarios received!")


    # conversion from pgm coords to x, y in meters
    def pixel_to_real(self, pixel_x, pixel_y):
        real_x = self.origin_x + (pixel_x * self.resolution)
        real_y = self.origin_y + ((self.image_height - pixel_y) * self.resolution)
        self.get_logger().info(f"Converted pixel ({pixel_x}, {pixel_y}) to real-world coordinates ({real_x:.2f}, {real_y:.2f})")
        return real_x, real_y

    # Convert angle to quaternion
    def degrees_to_quaternion(self, angle_degrees):
        angle_radians = math.radians(angle_degrees)
        qz = math.sin(angle_radians / 2.0)
        qw = math.cos(angle_radians / 2.0)
        return qz, qw
    
    # action feedback callback
    def feedback_callback(self, feedback_msg):
        feedback = feedback_msg.feedback.status
        self.get_logger().info(feedback)

    # distance server
    def start_distance_tracking(self):
        if not self.distance_client.wait_for_service(timeout_sec=5.0):
            self.get_logger().error('Distance tracker service not available!')
            return False
        
        req = SetBool.Request()
        req.data = True
        future = self.distance_client.call_async(req)
        rclpy.spin_until_future_complete(self, future)
        self.get_logger().info("Distance tracking started.")
        return True
    
    def stop_distance_tracking(self):
        if not self.distance_client.wait_for_service(timeout_sec=5.0):
            self.get_logger().error('Distance tracker service not available!')
            return 0.0

        req = SetBool.Request()
        req.data = False
        future = self.distance_client.call_async(req)
        rclpy.spin_until_future_complete(self, future)
        
        res = future.result()
        if res and res.success:
            return float(res.message)
        return 0.0
    
    def execute_scenario(self, scenario_id):
        self.get_logger().info(f"Executing {scenario_id}")

        self.start_distance_tracking()
        
        scenario = self.scenarios.get(scenario_id, {})
        target = scenario.pop('target', 'unknown') 
        self.get_logger().info(f"Target to find: '{target}'")
        
        # Sorting locations by probability
        sorted_locs = sorted(scenario.items(), key=lambda item: item[1], reverse=True)
        
        for name, prob in sorted_locs:
            self.get_logger().info(f"Moving to {name} (Confidence: {prob}) to look for '{target}'")

            px = self.points[name]['x']
            py = self.points[name]['y']
            target_ori = self.points[name].get('ori', 0.0) 
            
            # conversions
            rx, ry = self.pixel_to_real(px, py)
            qz, qw = self.degrees_to_quaternion(target_ori)
            
            # setup goal
            goal = PoseStamped()
            goal.header.frame_id = 'map'
            # goal.header.stamp = self.get_clock().now().to_msg() # Nav2 prefers clean timestamps
            
            # create translational goal
            goal.pose.position.x = float(rx)
            goal.pose.position.y = float(ry)
            goal.pose.position.z = 0.0
            
            # create orientation goal
            goal.pose.orientation.x = 0.0
            goal.pose.orientation.y = 0.0
            goal.pose.orientation.z = float(qz)
            goal.pose.orientation.w = float(qw)

            self.get_logger().info(f"Goal: x: {rx:.2f}, y: {ry:.2f}, orientation: {target_ori}")
            
            self.navigator.goToPose(goal)
            i = 0
            while not self.navigator.isTaskComplete():
                i += 1
                feedback = self.navigator.getFeedback()

                # will update based on real life timing
                if feedback and feedback.navigation_time.sec > 500:
                    self.navigator.cancelTask()
                    self.get_logger().info("Navigation taking too long, cancelling task.")
                if feedback and i % 100 == 0:
                    self.get_logger().info(f"Distance remaining: {feedback.distance_remaining:.3f} m")
            
            if self.navigator.getResult() == TaskResult.SUCCEEDED:
                self.get_logger().info(f"Successfully reached {name}. Initiating vision search for '{target}'...")
                
                if not self.vision_client.wait_for_server(timeout_sec=5.0):
                    self.get_logger().error('Vision action server is not available! Skipping search.')
                    continue
                
                search_goal = FindPerson.Goal()
                search_goal.target_name = target
                
                send_goal_future = self.vision_client.send_goal_async(search_goal, feedback_callback=self.feedback_callback)
                rclpy.spin_until_future_complete(self, send_goal_future)
                
                goal_handle = send_goal_future.result()
                if not goal_handle.accepted:
                    self.get_logger().error('Search goal was rejected by the vision server.')
                    continue
                
                result_future = goal_handle.get_result_async()
                rclpy.spin_until_future_complete(self, result_future)
                
                action_result = result_future.result().result
                
                if action_result.is_found:
                    self.get_logger().info(f"SUCCESS: Target '{target}' found at {name}! Stopping navigation sequence.")
                    total_dist = self.stop_distance_tracking()
                    break # Target found, terminate the loop
                else:
                    self.get_logger().info(f"Target '{target}' not found at {name}. Moving to the next location in sequence.")
        total_dist = self.stop_distance_tracking()
        self.get_logger().info(f"End of search. \n \n Total distance travelled: {total_dist} \n")

def main():
    rclpy.init()
    node = JackalNav()
    # node.execute_scenario('scenario_2')

    node.execute_scenario(node.target_scenario)

    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()