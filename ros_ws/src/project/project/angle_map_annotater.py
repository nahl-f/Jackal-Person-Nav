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
    """draws reference axis legend for orientation selection"""
    #centre of two arrows (origin)
    cx, cy = 70, 80

    # (img, start coord (top right), stop coord (bottom left) , (BGR) , (line thickness/fill))
    cv2.rectangle(img, (5, 5), (150, 110), (255, 255, 255), -1)
    cv2.rectangle(img, (5, 5), (150, 110), (0, 0, 0), 1)
    
    # text title (img, text, end coord, font, size, colour, thickness)
    cv2.putText(img, "Angle Ref", (7, 15), cv2.FONT_HERSHEY_SIMPLEX, 0.3, (0, 0, 0), 1)
    
    # x axis (for map frame)
    cv2.arrowedLine(img, (cx, cy), (cx + 40, cy), (0, 0, 255), 2, tipLength=0.2)
    cv2.putText(img, "0 (X)", (cx + 45, cy + 4), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 255), 1)
    
    # y axis (for map frame)
    cv2.arrowedLine(img, (cx, cy), (cx, cy - 40), (25, 180, 0), 2, tipLength=0.2)
    cv2.putText(img, "90 (Y)", (cx - 20, cy - 45), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 150, 0), 1)

# saves pixel coordinates and orientation
def click_event(event, x, y, flags, params):
    display_img = params
    
    if event == cv2.EVENT_LBUTTONDOWN:
        print(f"\n[Click Detected] Coordinates: (x={x}, y={y})")
        
        loc_name = input("Enter location name (or press Enter to skip): ").strip()
        
        if loc_name:
            ori_input = input("Enter orientation in degrees (e.g., 0, 90, 180): ").strip()

            try:
                ori = float(ori_input) if ori_input else 0.0
            except ValueError:
                print("Invalid input for angle. Defaulting to 0.0")
                ori = 0.0

            # save to dictionary
            map_data["locations"][loc_name] = {"x": x, "y": y, "ori": ori}
            print(f"--> Saved '{loc_name}' at ({x}, {y}) with heading {ori} deg")
            
            # draw location point on image
            cv2.circle(display_img, (x, y), 3, (0, 0, 255), -1)
            cv2.putText(display_img, loc_name, (x + 5, y - 5), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 255), 1)
            
            # calculate the end point for the heading arrow
            arrow_length = 20
            angle_rad = math.radians(ori)
            end_x = int(x + arrow_length * math.cos(angle_rad))
            end_y = int(y - arrow_length * math.sin(angle_rad)) # y axis increases downwards in pixels
            
            # draw heading arrow
            cv2.arrowedLine(display_img, (x, y), (end_x, end_y), (0, 0, 255), 2, tipLength=0.3)
            
            cv2.imshow('Map Annotator', display_img)
        else:
            print("--> Skipped.")

def main():
    # can pass in argument through command line (python3 map_annotater.py /path/to/map.pgm)
    parser = argparse.ArgumentParser(description="Annotate PGM map and export to JSON in the same directory.")
    parser.add_argument("filepath", help="Path to the .pgm map file")
    args = parser.parse_args()

    input_path = Path(args.filepath)
    # FOR PRESENTATION
    desktop_path = "/workspaces/ros_ws/angle_test.png"
    
    output_filepath = input_path.parent / f"{input_path.stem}_locations.json"

    img = cv2.imread(str(input_path), -1)

    if img is None:
        print(f"Error: Could not open image at '{input_path}'.")
        sys.exit(1)

    # get height and store in json
    height, width = img.shape[:2]
    map_data["image_height"] = height

    # convert to BGR for drawing locations
    if len(img.shape) == 2:
        display_img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    else:
        display_img = img.copy()
        
    # draw the legend before showing the image
    draw_orientation_legend(display_img)

    print(f"Loaded: {input_path.name} ({width}x{height})")
    print("--------------------------------------------------")
    print("1. Click a location on the map window.")
    print("2. Look at this terminal to type the location name.")
    print("3. Look at this terminal to type the orientation (degrees).")
    print("4. Press 'ESC' in the map window when finished to save the JSON.")
    print("--------------------------------------------------")

    # resize if image too large
    cv2.namedWindow('Map Annotator', cv2.WINDOW_NORMAL)
    cv2.resizeWindow('Map Annotator', 1280, 720)

    cv2.imshow('Map Annotator', display_img)
    cv2.setMouseCallback('Map Annotator', click_event, param=display_img)

    # Wait for ESC key to exit
    while True:
        if cv2.waitKey(1) & 0xFF == 27:
            break

    # for presentation
    cv2.imwrite(str(desktop_path), display_img)
    print(f"Annotated image saved to Desktop: {desktop_path}")

    cv2.destroyAllWindows()

    # Export to JSON
    with open(output_filepath, 'w') as f:
        json.dump(map_data, f, indent=4)
        
    print(f"\nSuccessfully saved {len(map_data['locations'])} locations and image height ({height})")
    print(f"File saved to: {output_filepath}")

if __name__ == "__main__":
    main()