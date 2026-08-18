# Simulation Documentation
Always make sure to build and source packages before launching files.
```bash
cd /workspaces/ros_ws
colcon build
source install/setup.bash
```

## Launching Gazebo Simulator
Launch the gazebo simulation, this utilises the robot.yaml config saved under /home/clearpath. By default, the simulation is in the **warehouse** world.

```bash
ros2 launch clearpath_gz simulation.launch.py
```
This takes some time. Once launched, teleop the Jackal using the GUI, ensure to remap the topic to /jackal1/cmd_vel by typing the topic name in the window.

**Teleoperating the Jackal**
If you'd like to use the keyboard to teleooperate the jackal, in a seperate terminal:
```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -r cmd_vel:=/jackal1/cmd_vel
```

## Mapping & Navigation
Ensure the gazebo simulation is running in a seperate terminal first. The **warehouse**  world map is used by default for localisation.
```bash
ros2 launch project localisation.launch.py
```
Launch RViz for visualisation. Provide an **initial pose estimate** using RViz. Change the laser topic to /jackal1/sensors/lidar3d_0/scan using the dropdown menu if laser scans are not visible.  

``` bash
ros2 launch clearpath_viz view_navigation.launch.py namespace:=jackal1
```

Launch Nav2
```bash
ros2 launch project nav.launch.py
```

Provide goals using **Nav2 Goal** in RViz.