import rclpy
from rclpy.node import Node
from sensor_msgs.msg import CompressedImage # Using CompressedImage
from cv_bridge import CvBridge
import cv2
import threading
import time
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy

# High-freshness QoS profile
qos_profile = QoSProfile(
    reliability=ReliabilityPolicy.BEST_EFFORT,
    history=HistoryPolicy.KEEP_LAST,
    depth=1  # Discard old frames, only keep the latest one
)

class CameraViewer(Node):
    def __init__(self):
        super().__init__('camera_viewer')
        self.bridge = CvBridge()
        self.latest_frame = None
        self.frame_count = 0
        self.lock = threading.Lock()
        
        self.subscription = self.create_subscription(
            CompressedImage, 
            '/jackal1/sensors/camera_0/color/compressed', 
            self.image_callback, 
            qos_profile
        )
        
        # Timer to calculate and print actual incoming FPS
        self.start_time = time.time()
        self.timer = self.create_timer(2.0, self.log_fps)
            
    def image_callback(self, msg):
        # FIX: Use compressed_imgmsg_to_cv2 instead for CompressedImage topics
        frame = self.bridge.compressed_imgmsg_to_cv2(msg, desired_encoding="bgr8")
        with self.lock:
            self.latest_frame = frame
            self.frame_count += 1

    def log_fps(self):
        elapsed = time.time() - self.start_time
        fps = self.frame_count / elapsed
        self.get_logger().info(f"Incoming Camera Rate: {fps:.2f} FPS")
        # Reset counters
        self.frame_count = 0
        self.start_time = time.time()

def main():
    rclpy.init()
    node = CameraViewer()
    
    # Spin ROS 2 in a background thread so it updates self.latest_frame constantly
    ros_thread = threading.Thread(target=rclpy.spin, args=(node,), daemon=True)
    ros_thread.start()
    
    print("Displaying live feed. Press 'q' on the video window to quit.")
    
    try:
        while rclpy.ok():
            with node.lock:
                frame = node.latest_frame.copy() if node.latest_frame is not None else None
            
            if frame is not None:
                # Add a small timestamp to visually verify if the video is frozen
                h, w, _ = frame.shape
                cv2.putText(frame, f"Live: {time.time():.2f}", (10, h - 20), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                
                cv2.imshow("Jackal Camera Diagnostic", frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
    finally:
        cv2.destroyAllWindows()
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()