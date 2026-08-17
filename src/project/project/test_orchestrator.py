import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from geometry_msgs.msg import PoseStamped
from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult
import yaml
import json

from vision_interfaces.action import FindPerson 

class JackalNav(Node):
    # def __init__(self, map_yaml, locations_json, scenarios_json):
    def __init__(self):
        super().__init__('jackal_navigation')
        self.navigator = BasicNavigator(namespace='jackal1')

        # declare parameters for map, locations, and scenarios
        self.declare_parameter('map_file', '')
        self.declare_parameter('location_file', '')
        self.declare_parameter('scenario_file', '')

        # set parameters from launch file
        map_yaml = self.get_parameter('map_file').get_parameter_value().string_value
        locations_json = self.get_parameter('location_file').get_parameter_value().string_value
        scenarios_json = self.get_parameter('scenario_file').get_parameter_value().string_value
        
        # action client for vision server
        self.vision_client = ActionClient(self, FindPerson, 'find_person')
        
        #  Load map data for conversion
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
        self.get_logger().info("locations received!")
            
        # Store scenarios
        with open(scenarios_json, 'r') as f:
            self.scenarios = json.load(f)
        self.get_logger().info("scenarios received!")

    # conversion from pgm coords to x, y in meters
    def pixel_to_real(self, pixel_x, pixel_y):
        real_x = self.origin_x + (pixel_x * self.resolution)
        real_y = self.origin_y + ((self.image_height - pixel_y) * self.resolution)
        self.get_logger().info(f"Converted pixel ({pixel_x}, {pixel_y}) to real-world coordinates ({real_x}, {real_y})")
        return real_x, real_y
    
    # action feedback callback
    def feedback_callback(self, feedback_msg):
        feedback = feedback_msg.feedback.status
        self.get_logger().info(feedback)

    def execute_scenario(self, scenario_id):
        self.get_logger().info(f"Executing {scenario_id}")
        
        scenario = self.scenarios.get(scenario_id, {})
        target = scenario.pop('target', 'unknown') 
        self.get_logger().info(f"Target to find: '{target}'")
        
        # Sorting locations by probability
        sorted_locs = sorted(scenario.items(), key=lambda item: item[1], reverse=True)
        
        for name, prob in sorted_locs:
            self.get_logger().info(f"Moving to {name} (Confidence: {prob}) to look for '{target}'")
            
            # access and convert coordinates
            px = self.points[name]['x']
            py = self.points[name]['y']
            rx, ry = self.pixel_to_real(px, py)
            
            # setup goal
            goal = PoseStamped()
            goal.header.frame_id = 'map'
            goal.pose.position.x = float(rx)
            goal.pose.position.y = float(ry)
            goal.pose.orientation.w = 1.0
            
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
                    self.get_logger().info(f"Distance remaining: {feedback.distance_remaining} m")
            
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
                    break # Target found, terminate the loop
                else:
                    self.get_logger().info(f"Target '{target}' not found at {name}. Moving to the next location in sequence.")

def main():
    rclpy.init()
    # # map_dir = "/workspaces/ros_ws/src/project/config/maps/warehouse.yaml"
    # # location_dir = "/workspaces/ros_ws/src/project/config/maps/warehouse_locations.json"
    # # scenario_dir = "/workspaces/ros_ws/src/project/config/scenarios/warehouse_scenarios.json"
    # map_dir = "/workspaces/ros_ws/src/project/config/maps/robohub.yaml"
    # location_dir = "/workspaces/ros_ws/src/project/config/maps/robohub_locations.json"
    # scenario_dir = "/workspaces/ros_ws/src/project/config/scenarios/robohub_scenarios.json"
    # # map_dir = "/workspaces/ros_ws/src/project/config/maps/final_edited_ori.yaml"
    # # location_dir = "/workspaces/ros_ws/src/project/config/maps/final_edited_locations.json"
    # # scenario_dir = "/workspaces/ros_ws/src/project/config/scenarios/final_scenarios.json"
    
    #node = JackalNav(map_dir, location_dir, scenario_dir)

    node = JackalNav()
    node.execute_scenario('scenario_1')
    
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()