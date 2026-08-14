import yaml

def load_map_metadata(yaml_path):
    with open(yaml_path, 'r') as file:
        data = yaml.safe_load(file)
    
    # Extract resolution and origin
    res = data['resolution']
    # origin is usually [x, y, yaw]
    origin = data['origin'] 
    
    return res, origin

print(load_map_metadata('/workspaces/ros_ws/src/project/config/maps/warehouse.yaml'))