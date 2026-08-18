import rclpy
from rclpy.node import Node
from sensor_msgs.msg import CompressedImage
from cv_bridge import CvBridge
from deepface import DeepFace
import cv2
import os

REFERENCE_DIR = (
    "/workspaces/ros_ws/src/project/config/face_id/nahl"
)

CAMERA_TOPIC = (
    "/jackal1/sensors/camera_0/color/compressed"
)


class DeepFaceTest(Node):

    def __init__(self):
        super().__init__("deepface_test")

        self.bridge = CvBridge()

        if not os.path.exists(REFERENCE_DIR):
            self.get_logger().error(f"Reference directory doesn't exist: {REFERENCE_DIR}")

        self.subscription = self.create_subscription(
            CompressedImage,
            CAMERA_TOPIC,
            self.image_callback,
            10
        )

        self.get_logger().info("DeepFace test started.")

    def image_callback(self, msg):
        try:
            # Convert ROS CompressedImage -> OpenCV image
            frame = self.bridge.compressed_imgmsg_to_cv2(
                msg,
                desired_encoding="bgr8"
            )

            # Display camera feed
            cv2.imshow("DeepFace Test", frame)

            # Check whether the reference face is present
            results = DeepFace.find(
                img_path=frame,
                db_path=REFERENCE_DIR,
                model_name="VGG-Face",
                detector_backend="mtcnn",
                enforce_detection=False,
                silent=True
            )

            print(results)
            match_found = any(not df.empty for df in results)

            if match_found:
                self.get_logger().info(
                    "Reference face detected! Closing Window"
                )
                cv2.destroyAllWindows()
                rclpy.shutdown()
                return

        except Exception as e:
            self.get_logger().error(
                f"DeepFace error: {e}"
            )

        # Keep OpenCV window responsive
        if cv2.waitKey(1) & 0xFF == ord("q"):
            rclpy.shutdown()


def main(args=None):
    rclpy.init(args=args)

    node = DeepFaceTest()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass

    cv2.destroyAllWindows()
    node.destroy_node()

    if rclpy.ok():
        rclpy.shutdown()


if __name__ == "__main__":
    main()