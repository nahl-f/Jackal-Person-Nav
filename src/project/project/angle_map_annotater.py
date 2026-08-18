import cv2
import argparse
import sys
import json
import math
from pathlib import Path

# dictionary to store json structure
map_data = {
    "locations": {}
}

def draw_orientation_legend(img):
    """draws reference axis legend for orientation"""
    margin = 15
    box_w = 150
    box_h = 110
    #centre of two arrows (origin)
    cx = margin + 65
    cy = margin + 75
    axis_len = 45

    # (img, start coord (top right), stop coord (bottom left) , (BGR) , (line thickness/fill))
    cv2.rectangle(img, (margin, margin), (margin + box_w, margin + box_h), (255, 255, 255), -1)
    cv2.rectangle(img, (margin, margin), (margin + box_w, margin + box_h), (0, 0, 0), 2)
    
    # text title (img, text, end coord, font, size, colour, thickness)
    cv2.putText(img, "Angle Ref", (margin + 5, margin + 20), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)
    
    # x axis (for map frame)
    cv2.arrowedLine(img, (cx, cy), (cx + axis_len, cy), (0, 0, 255), 2, tipLength=0.2)
    cv2.putText(img, "0 (X)", (cx + axis_len + 5, cy + 4), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 255), 1, cv2.LINE_AA)
    
    # y axis (for map frame)
    cv2.arrowedLine(img, (cx, cy), (cx, cy - axis_len), (25, 180, 0), 2, tipLength=0.2)
    cv2.putText(img, "90 (Y)", (cx - 25, cy - axis_len - 5), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 150, 0), 1, cv2.LINE_AA)

# saves pixel coordinates and orientation
def click_event(event, x, y, flags, params):
    display_img, scale_factor = params
    
    if event == cv2.EVENT_LBUTTONDOWN:
        orig_x = int(x / scale_factor)
        orig_y = int(y / scale_factor)
        
        print(f"\n[Click Detected] Original Map Coordinates: (x={orig_x}, y={orig_y})")
        
        loc_name = input("Enter location name (or press Enter to skip): ").strip()
        
        if loc_name:
            ori_input = input("Enter orientation in degrees (e.g., 0, 90, 180): ").strip()

            try:
                ori = float(ori_input) if ori_input else 0.0
            except ValueError:
                print("Invalid input for angle. Defaulting to 0.0")
                ori = 0.0

            # save to dictionary
            map_data["locations"][loc_name] = {"x": orig_x, "y": orig_y, "ori": ori}
            print(f"--> Saved '{loc_name}' at ({orig_x}, {orig_y}) with heading {ori} deg")

            cv2.circle(display_img, (x, y), 4, (0, 0, 255), -1)
            cv2.putText(display_img, loc_name, (x + 8, y - 8), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2, cv2.LINE_AA)
            
            # calculate the end point for the heading arrow
            arrow_length = 35
            angle_rad = math.radians(ori)
            end_x = int(x + arrow_length * math.cos(angle_rad))
            end_y = int(y - arrow_length * math.sin(angle_rad)) 
            
            # draw heading arrow
            cv2.arrowedLine(display_img, (x, y), (end_x, end_y), (0, 0, 255), 2, tipLength=0.3)
            
            cv2.imshow('Map Annotator', display_img)
        else:
            print("--> Skipped.")

def main():
    parser = argparse.ArgumentParser(description="Annotate PGM map and export to JSON in the same directory.")
    parser.add_argument("filepath", help="Path to the .pgm map file")
    args = parser.parse_args()

    input_path = Path(args.filepath)
    desktop_path = "/workspaces/ros_ws/test.png"
    
    output_filepath = input_path.parent / f"{input_path.stem}_locations.json"

    img = cv2.imread(str(input_path), -1)

    if img is None:
        print(f"Error: Could not open image at '{input_path}'.")
        sys.exit(1)

    # ori dimensions for json
    height, width = img.shape[:2]
    map_data["image_height"] = height

    scale_factor = max(1, math.ceil(800.0 / max(height, width)))

    # convert to BGR for drawing locations
    if len(img.shape) == 2:
        bgr_img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    else:
        bgr_img = img.copy()

    display_img = cv2.resize(bgr_img, (width * scale_factor, height * scale_factor), interpolation=cv2.INTER_NEAREST)
        
    draw_orientation_legend(display_img)

    print(f"Loaded: {input_path.name} (Original size: {width}x{height}, Display scale: {scale_factor}x)")
    print("--------------------------------------------------")
    print("1. Click a location on the map window.")
    print("2. Look at this terminal to type the location name.")
    print("3. Look at this terminal to type the orientation (degrees).")
    print("4. Press 'ESC' in the map window when finished to save the JSON.")
    print("--------------------------------------------------")

    cv2.namedWindow('Map Annotator', cv2.WINDOW_NORMAL)
    cv2.resizeWindow('Map Annotator', 1280, 720)

    cv2.imshow('Map Annotator', display_img)
    
    cv2.setMouseCallback('Map Annotator', click_event, param=(display_img, scale_factor))

    # Wait for ESC key to exit
    while True:
        if cv2.waitKey(1) & 0xFF == 27:
            break

    # save presentation image
    cv2.imwrite(str(desktop_path), display_img)
    print(f"Image saved to: {desktop_path}")

    cv2.destroyAllWindows()

    # export to JSON
    with open(output_filepath, 'w') as f:
        json.dump(map_data, f, indent=4)
        
    print(f"\nSuccessfully saved {len(map_data['locations'])} locations and original image height ({height})")
    print(f"File saved to: {output_filepath}")

if __name__ == "__main__":
    main()