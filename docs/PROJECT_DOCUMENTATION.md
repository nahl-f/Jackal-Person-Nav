# Project Documentation Workflow

There are five main steps to configure and run the project. 

## 1. Editing the Map
1. Generate the map following the onboard repository instructions.
2. Edit the map to add walls where required using the [ROS SLAM Map Editor](https://gyropalm.github.io/ROS-SLAM-Map-Editor/editor.html).
3. Ensure that the image field in your YAML file has the exact same name as your `.pgm` file.
4. Store the maps under `/workspaces/ros_ws/src/project/config/maps` using the name of the location (e.g., `robohub.yaml` and `robohub.pgm`).

## 2. Annotating the Map
Navigate to the project directory and run the annotator script:
```bash
cd /workspaces/ros_ws/src/project/project
python3 angle_map_annotator.py /workspaces/ros_ws/src/project/config/maps/<name_of_map>.pgm
```

Click the points on the map where you would like to save the location.
Type the name of the location and press enter.
Type the orientation required for the goal.
Repeat this process for all desired locations.
Open the image window and press **Escape**. The program will automatically save the locations to a JSON file under the maps folder.

**Example Output:**
```json
{
    "locations": {
        "location1": {
            "x": 66,
            "y": 66,
            "ori": 90.0
        },
        "location2": {
            "x": 93,
            "y": 41,
            "ori": 0.0
        }
    },
    "image_height": 119
}
```

## 3. Saving Images for Face ID
Create directories to hold reference images for the target individuals.
```bash
cd /workspaces/ros_ws/src/project/config/face_id
mkdir <name_of_person>
```
Store images of the target person inside their respective folder.

## 4. Creating Scenarios
Navigate to the scenarios folder:
```bash
cd /workspaces/ros_ws/src/project/config/scenarios
```
The name of the file must be formatted as `<location_name>_scenarios.json`. For example, if your map files are named `robohub.pgm` and `robohub.yaml`, your scenarios file must be `robohub_scenarios.json`.

**Example Scenario Configuration:**
```json
{
    "scenario_1": {
        "target": "nahl",
        "location1": 0.90,
        "location2": 0.10
    },
    "scenario_2": {
        "target": "tyler",
        "location2": 0.95,
        "location1": 0.74
    }
}
```

## 5. Launching Project Files
After making any changes (such as adding files or images), you must rebuild your workspace:
```bash
cd /workspaces/ros_ws
colcon build
source install/setup.bash
```

### Onboard Jackal Execution
Ensure the connection script is sourced in all terminals to access the Jackal topics and nodes.
Launch and test Nav2.

### Offboard Laptop Execution
Launch RViz for visualization:
```bash
ros2 launch clearpath_viz view_navigation.launch.py namespace:=jackal1
```

Launch the project orchestrator. This command requires two arguments:
*   `location`: The name of the location used for your map and scenarios.
*   `scenario`: The scenario name defined in your JSON file (e.g., `scenario_1`).
```bash
ros2 launch project full.launch.py location:=final scenario:=scenario_1
```