from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    namespace = "jackal1"
    #params_file = "/workspaces/ros_ws/src/project/config/navigation/new_planner.yaml"
    params_file = "/workspaces/ros_ws/src/project/config/navigation/current_physical.yaml"

    return LaunchDescription([
        # Map Server
        Node(
            package="nav2_map_server",
            executable="map_server",
            name="map_server",
            namespace=namespace,
            output="screen",
            parameters=[{"yaml_filename": "/opt/ros/humble/share/clearpath_nav2_demos/maps/warehouse.yaml"}],
            remappings=[
                ("/tf", "/jackal1/tf"),      
                ("/tf_static", "/jackal1/tf_static"),
            ],
        ),

        # AMCL
        Node(
            package="nav2_amcl",
            executable="amcl",
            name="amcl",
            namespace=namespace,
            output="screen",
            parameters=[params_file,{"use_sim_time": True}],
            remappings=[
                ("scan", "sensors/lidar3d_0/scan"), 
                ("odom", "platform/odom"), 
                ("/tf", "/jackal1/tf"),      
                ("/tf_static", "/jackal1/tf_static"),
            ],
        ),

        # Planner Server
        Node(
            package="nav2_planner",
            executable="planner_server",
            name="planner_server",
            namespace=namespace,
            output="screen",
            parameters=[params_file, {
                "use_sim_time": True,
                # "global_costmap.global_costmap.robot_base_frame": "base_link", 
                # "global_costmap.global_costmap.obstacle_layer.scan.topic": "/jackal1/sensors/lidar3d_0/scan",
                # "local_costmap.local_costmap.robot_base_frame": "base_link",
                # "local_costmap.local_costmap.voxel_layer.scan.topic": "/jackal1/sensors/lidar3d_0/scan",
            }],
            remappings=[("/tf", "/jackal1/tf"), 
                        ("/tf_static", "/jackal1/tf_static"),
                        ("scan", "/jackal1/sensors/lidar3d_0/scan")],
        ),

        # Controller Server
        Node(
            package="nav2_controller",
            executable="controller_server",
            name="controller_server",
            namespace=namespace,
            output="screen",
            parameters=[params_file, {
                "use_sim_time": True,
                # "local_costmap.local_costmap.robot_base_frame": "base_link",
                # "local_costmap.local_costmap.voxel_layer.scan.topic": "/jackal1/sensors/lidar3d_0/scan",
            }],
            remappings=[("/tf", "/jackal1/tf"), 
                        ("/tf_static", "/jackal1/tf_static"),
                        ("odom", "platform/odom"),
                        ("scan", "/jackal1/sensors/lidar3d_0/scan")],
        ),

        # Behavior Tree Navigator
        Node(
            package="nav2_bt_navigator",
            executable="bt_navigator",
            name="bt_navigator",
            namespace=namespace,
            output="screen",
            parameters=[params_file, {"use_sim_time": True}],
            remappings=[("/tf", "/jackal1/tf"), 
                        ("/tf_static", "/jackal1/tf_static"),
                        ("odom", "platform/odom"),
                        ("scan", "/jackal1/sensors/lidar3d_0/scan")],
        ),

        # Behavior Server
        Node(
            package="nav2_behaviors",
            executable="behavior_server",
            name="behavior_server",
            namespace=namespace,
            output="screen",
            parameters=[params_file, {"use_sim_time": True}],
            remappings=[("/tf", "/jackal1/tf"), 
                        ("/tf_static", "/jackal1/tf_static"),
                        ("odom", "platform/odom"),
                        ("scan", "sensors/lidar3d_0/scan")],
        ),

        # Lifecycle Manager
        Node(
            package="nav2_lifecycle_manager",
            executable="lifecycle_manager",
            name="lifecycle_manager",
            namespace=namespace,
            output="screen",
            parameters=[{
                "use_sim_time": True,
                "autostart": True,
                "node_names": [
                    "map_server", 
                    "amcl", 
                    "planner_server", 
                    "controller_server", 
                    "bt_navigator",
                    "behavior_server"
                ], 
            }],
        ),
    ])