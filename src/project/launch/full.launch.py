from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, PythonExpression, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare
from launch_ros.actions import Node

def generate_launch_description():
    #  launch argument for location
    location_arg = DeclareLaunchArgument(
        'location',
        default_value='default_location',
        description='Name of the location being used for maps, locations, and scenarios.'
    )
    scenario_arg = DeclareLaunchArgument(
        'scenario',
        default_value='scenario_1',
        description='Which scenario to run from the scenarios.json file'
    )

    # launch configuration for terminal arguments
    location = LaunchConfiguration('location')
    scenario = LaunchConfiguration('scenario')

    pkg_project = FindPackageShare('project')

    map_dir = PathJoinSubstitution([
        pkg_project, 
        'config', 
        'maps', 
        [location, '.yaml']
    ])

    location_dir = PathJoinSubstitution([
        pkg_project, 
        'config', 
        'maps', 
        [location, '_locations.json']
    ])

    scenario_dir = PathJoinSubstitution([
        pkg_project, 
        'config', 
        'scenarios', 
        [location, '_scenarios.json']
    ])

    face_id_dir = PathJoinSubstitution([
        pkg_project, 
        'config', 
        'face_id'
    ])

    # file paths
    # map_dir = PythonExpression([
    #     "'/workspaces/ros_ws/src/project/config/maps/' + '", location, "' + '.yaml'"
    # ])
    # location_dir = PythonExpression([
    #     "'/workspaces/ros_ws/src/project/config/maps/' + '", location, "' + '_locations.json'"
    # ])
    # scenario_dir = PythonExpression([
    #     "'/workspaces/ros_ws/src/project/config/scenarios/' + '", location, "' + '_scenarios.json'"
    # ])

    # nodes
    orchestrator_node = Node(
        package='project',
        executable='orchestrator',
        name='orchestrator_node',
        output='screen',
        parameters=[{
            'map_file': map_dir,
            'location_file': location_dir,
            'scenario_file': scenario_dir,
            'scenario' : scenario,
        }]
    )

    vision_server_node = Node(
        package='project',
        executable='vision_server',
        name='vision_server_node',
        output='screen',
        parameters=[{
            'face_id_dir': face_id_dir,
        }]
    )

    distance_server_node = Node(
        package='project', 
        executable='distance_server',
        name='distance_server_node',
        output='screen',
    )

    return LaunchDescription([
        location_arg,
        scenario_arg,
        orchestrator_node,
        vision_server_node,
        distance_server_node
    ])