import os
import warnings

# to prevent spam from YOLO startup
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
warnings.filterwarnings("ignore", category=UserWarning)

# action 
import rclpy
from rclpy.node import Node
from rclpy.action import ActionServer, CancelResponse
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy

# threading
from rclpy.executors import MultiThreadedExecutor
from rclpy.callback_groups import ReentrantCallbackGroup
import threading

# message types
from sensor_msgs.msg import CompressedImage
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry 

# libraries
from cv_bridge import CvBridge
from ultralytics import YOLO
import cv2
from deepface import DeepFace
import time
import math
import os 

# custom action interface 
from vision_interfaces.action import FindPerson 

import faulthandler
faulthandler.enable()

# keep only the latest frame
qos_profile = QoSProfile(
    reliability=ReliabilityPolicy.BEST_EFFORT,
    history=HistoryPolicy.KEEP_LAST,
    depth=1
)

class VisionSearchServer(Node):
    def __init__(self):
        super().__init__('vision_search_server')
        self.bridge = CvBridge()
        self.yolo = YOLO('yolov8n.pt')
        
        self.latest_frame = None
        self.lock = threading.Lock()
        
        # path to target person
        self.db_path = None
        self.current_target = None
        self.declare_parameter('face_id_dir', '')
        self.face_id_base_dir = self.get_parameter('face_id_dir').get_parameter_value().string_value
        
        self.search_active = False
        self.target_found = False
        self.goal_handle = None
        
        # odom tracking
        self.current_yaw = 0.0
        self.start_yaw = None
        self.accumulated_yaw = 0.0
        
        # callback group so odom, image and action callback can run simultaneously
        self.cb_group = ReentrantCallbackGroup()

        ### ROBOT DEPENDENT SECTION
        self.image_sub = self.create_subscription(
            CompressedImage, 
            '/jackal1/sensors/camera_0/color/compressed', 
            self.image_callback, 
            qos_profile,
            callback_group=self.cb_group)
            
        self.odom_sub = self.create_subscription(
            Odometry,
            '/jackal1/platform/odom',
            self.odom_callback,
            10,
            callback_group=self.cb_group)
            
        self.cmd_pub = self.create_publisher(Twist, '/jackal1/cmd_vel', 10)
        ### END OF ROBOT DEPENDENT SECTION

        # the node to add to the server, the type of action, the action name, a callback that returns a result message
        self._action_server = ActionServer(
            self,
            FindPerson,
            'find_person',
            execute_callback=self.execute_callback,
            cancel_callback=self.cancel_callback,
            callback_group=self.cb_group)

    def image_callback(self, msg):
        frame = self.bridge.compressed_imgmsg_to_cv2(msg, desired_encoding="bgr8")
        with self.lock:
            self.latest_frame = frame

    def odom_callback(self, msg):
        q = msg.pose.pose.orientation
        
        # quaternion to yaw conversion formula
        siny_cosp = 2.0 * (q.w * q.z + q.x * q.y)
        cosy_cosp = 1.0 - 2.0 * (q.y * q.y + q.z * q.z)
        new_yaw = math.atan2(siny_cosp, cosy_cosp)
        
        if self.search_active:
            if self.start_yaw is None:
                self.start_yaw = new_yaw
                self.current_yaw = new_yaw
                self.accumulated_yaw = 0.0
                return
            
            # continuous tracking
            delta_yaw = new_yaw - self.current_yaw
            if delta_yaw > math.pi:
                delta_yaw -= 2.0 * math.pi
            elif delta_yaw < -math.pi:
                delta_yaw += 2.0 * math.pi
                
            self.accumulated_yaw += abs(delta_yaw)
            
        self.current_yaw = new_yaw

    def recognize_face(self, person_crop):
        if not self.db_path:
            return None
        try:
            results = DeepFace.find(
                img_path=person_crop, 
                db_path=self.db_path, 
                model_name="VGG-Face",
                enforce_detection=False,
                silent=True
            )
            if results and not results[0].empty:
                return self.current_target
            return "Unknown"
        except Exception:
            return None

    def cancel_callback(self, cancel_request):
        print('cancelled')
        return cancel_request.ACCEPT
        return CancelResponse.ACCEPT

    def execute_callback(self, goal_handle):
        self.current_target = goal_handle.request.target_name
        self.get_logger().info(f'New search goal accepted for target: {self.current_target}.')
        
        self.goal_handle = goal_handle
        self.target_found = False
        
        # update to target
        if not self.face_id_base_dir:
            self.get_logger().error("face_id_dir parameter is empty! Ensure it is passed in the launch file.")
            
        self.db_path = os.path.join(self.face_id_base_dir, self.current_target.lower())
        
        self.start_yaw = None
        self.accumulated_yaw = 0.0
        self.search_active = True
        
        while self.search_active:
            time.sleep(0.1)
            
        result = FindPerson.Result()
        result.is_found = self.target_found
        return result
    
def main():
    rclpy.init()
    node = VisionSearchServer()
    
    executor = MultiThreadedExecutor()
    executor.add_node(node)
    
    ros_thread = threading.Thread(target=executor.spin, daemon=True)
    ros_thread.start()
    
    print("Vision node spinning. Awaiting action goals...")
    
    rotate_msg = Twist()
    rotate_msg.angular.z = 0.5 
    stop_msg = Twist()
    
    inference_interval = 0.2  
    last_inference_time = 0.0
    center_tolerance_pct = 0.10 
    window_created = False
    
    is_verifying = False
    verification_start_time = 0.0
    ignore_center_until = 0.0

    try:
        while rclpy.ok():
            current_time = time.time()

            if node.search_active:
                current_degrees = math.degrees(node.accumulated_yaw)
                feedback_msg = FindPerson.Feedback()

                # Check for completion condition
                #old angle : 2.0 * math.pi
                if node.accumulated_yaw >= (math.pi):
                    node.get_logger().warn(f"\n Completed exact 180-degree rotation. Target '{node.current_target}' not found.")
                    node.goal_handle.abort()
                    node.search_active = False
                    node.cmd_pub.publish(stop_msg)
                    if window_created:
                        cv2.destroyAllWindows()
                        window_created = False
                    continue

                with node.lock:
                    frame = node.latest_frame.copy() if node.latest_frame is not None else None
                
                if frame is not None:
                    h, w, _ = frame.shape
                    frame_center_x = w // 2
                    allowed_offset = w * center_tolerance_pct
                    
                    if (current_time - last_inference_time) >= inference_interval:
                        last_inference_time = current_time
                        results = node.yolo(frame, conf=0.6, verbose=False)
                        
                        person_centered = False
                        target_box = None
                        
                        if current_time < ignore_center_until:
                            feedback_msg.status = f"Clearing timed-out target. Current rotation: {current_degrees:.1f}°"
                            #node.get_logger().info(feedback_msg.status)
                            node.goal_handle.publish_feedback(feedback_msg)
                            node.cmd_pub.publish(rotate_msg)
                        else:
                            for r in results:
                                for box in r.boxes:
                                    if int(box.cls[0]) == 0: 
                                        x1, y1, x2, y2 = map(int, box.xyxy[0])
                                        box_center_x = (x1 + x2) // 2
                                        
                                        if abs(box_center_x - frame_center_x) <= allowed_offset:
                                            person_centered = True
                                            target_box = (x1, y1, x2, y2)
                                            break
                            
                            if person_centered and target_box:
                                if not is_verifying:
                                    is_verifying = True
                                    verification_start_time = current_time
                                    node.cmd_pub.publish(stop_msg)
                                    time.sleep(0.2) 
                                    
                                time_verifying = current_time - verification_start_time
                                # print(time_verifying)
                                
                                if time_verifying > 15.0:
                                    print("\n")
                                    node.get_logger().warn("15-second timeout reached. Target unrecognizable. Resuming sweep. \n")
                                    is_verifying = False
                                    
                                    ignore_center_until = current_time + 2.0
                                    node.cmd_pub.publish(rotate_msg)
                                else:
                                    feedback_msg.status = f"Verifying target ({15.0 - time_verifying:.1f}s left). Angle: {current_degrees:.1f}°"
                                    #node.get_logger().info(feedback_msg.status)
                                    node.goal_handle.publish_feedback(feedback_msg)
                                    node.cmd_pub.publish(stop_msg) 
                                    
                                    with node.lock:
                                        fresh_frame = node.latest_frame.copy() if node.latest_frame is not None else frame
                                    
                                    x1, y1, x2, y2 = target_box
                                    person_crop = fresh_frame[y1:y2, x1:x2]
                                    identity = node.recognize_face(person_crop)
                                    if identity == node.current_target:
                                        node.target_found = True
                                    # #changes made july 23
                                    # if identity == "Unknown":
                                    #     node.get_logger().info("Person is not target. Resuming sweep.")
                                    #     is_verifying = False
                                    # #end of changes made
                            else:
                                if is_verifying:
                                    is_verifying = False
                                    
                                feedback_msg.status = f"Sweeping environment. Current rotation: {current_degrees:.1f}"
                                #node.get_logger().info(feedback_msg.status)
                                node.goal_handle.publish_feedback(feedback_msg)
                                node.cmd_pub.publish(rotate_msg)
                    else:
                        if not is_verifying:
                            node.cmd_pub.publish(rotate_msg)

                    # bounding lines
                    cv2.line(frame, (int(frame_center_x - allowed_offset), 0), (int(frame_center_x - allowed_offset), h), (255, 255, 0), 1)
                    cv2.line(frame, (int(frame_center_x + allowed_offset), 0), (int(frame_center_x + allowed_offset), h), (255, 255, 0), 1)
                    
                    cv2.imshow("Search Active", frame)
                    window_created = True
                    cv2.waitKey(1)
                
                if node.target_found:
                    print("\n")
                    node.get_logger().warn(f"\n Target '{node.current_target}' found!")
                    node.goal_handle.succeed()
                    node.cmd_pub.publish(stop_msg)
                    node.search_active = False
                    if window_created:
                        cv2.destroyAllWindows()
                        window_created = False
            else:
                time.sleep(0.05)
                
    finally:
        node.cmd_pub.publish(stop_msg)
        cv2.destroyAllWindows()
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()