import cv2
import cvzone
import math
from ultralytics import YOLO
import tkinter as tk
from tkinter import filedialog
import os
from datetime import datetime

# Create a root window and hide it
root = tk.Tk()
root.withdraw()

# Ask user to choose between file or RTSP stream
choice = input("Choose input source:\n1. Video file\n2. RTSP Camera Stream\nEnter choice (1 or 2): ").strip()

if choice == '1':
    # Open file dialog to select video
    print("Please select a video file...")
    video_path = filedialog.askopenfilename(
        title="Select a video file for fall detection",
        filetypes=[
            ("Video files", "*.mp4 *.avi *.mov *.mkv *.wmv *.flv *.webm"),
            ("MP4 files", "*.mp4"),
            ("AVI files", "*.avi"),
            ("All files", "*.*")
        ]
    )
    
    # Check if a file was selected
    if not video_path:
        print("No video file selected. Exiting...")
        exit()
    
    print(f"Selected video: {video_path}")
    is_rtsp_stream = False

elif choice == '2':
    # Get RTSP URL from user
    print("\nRTSP Stream Configuration:")
    print("Example formats:")
    print("  rtsp://username:password@ip:port/stream")
    print("  rtsp://192.168.1.100:554/stream1")
    print("  rtsp://admin:password123@192.168.1.50:554/live/main")
    print("  Your working URL: rtsp://admin:AK@MrA!4501$uf@192.168.0.109:554/cam/realmonitor?channel=8&subtype=0")
    
    video_path = input("\nEnter your RTSP URL: ").strip()
    
    if not video_path:
        print("No RTSP URL provided. Exiting...")
        exit()
    
    print(f"Connecting to RTSP stream: {video_path}")
    is_rtsp_stream = True

else:
    print("Invalid choice. Exiting...")
    exit()

cap = cv2.VideoCapture(video_path)

# Configure RTSP stream settings for better reliability
if is_rtsp_stream:
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Reduce buffer size for lower latency
    cap.set(cv2.CAP_PROP_FPS, 25)  # Set FPS for RTSP
    print("Connecting to RTSP stream... This may take a few seconds...")

# Check if video/stream opened successfully
if not cap.isOpened():
    if is_rtsp_stream:
        print(f"Error: Could not connect to RTSP stream '{video_path}'")
        print("Please check:")
        print("- Network connection")
        print("- RTSP URL format")
        print("- Camera credentials (username/password)")
        print("- Camera IP and port")
        print("- Firewall settings")
    else:
        print(f"Error: Could not open video file '{video_path}'")
        print("Please make sure the file exists and is a valid video format.")
    exit()

# Get video properties for output
fps = int(cap.get(cv2.CAP_PROP_FPS)) if not is_rtsp_stream else 25  # Default 25 FPS for RTSP
width = 980  # Using the resized width
height = 740  # Using the resized height

# Video writer setup
out = None
if not is_rtsp_stream:
    # Only save video files, not live streams
    current_folder = os.path.dirname(os.path.abspath(__file__))
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    input_name = os.path.splitext(os.path.basename(video_path))[0]
    output_filename = f"fall_detection_{input_name}_{timestamp}.mp4"
    output_path = os.path.join(current_folder, output_filename)
    
    # Define codec and create VideoWriter
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    print(f"Processed video will be saved as: {output_filename}")
else:
    # For RTSP streams, ask if user wants to record
    record_choice = input("Do you want to record the RTSP stream? (y/n): ").strip().lower()
    if record_choice == 'y':
        current_folder = os.path.dirname(os.path.abspath(__file__))
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"fall_detection_rtsp_stream_{timestamp}.mp4"
        output_path = os.path.join(current_folder, output_filename)
        
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        print(f"Recording RTSP stream to: {output_filename}")

print("Connection established! Starting fall detection...")
if is_rtsp_stream:
    print("Live RTSP stream - Press 't' to stop")
else:
    print("Press 't' to stop the video")

model = YOLO('yolov8s.pt')

classnames = []
with open('classes.txt', 'r') as f:
    classnames = f.read().splitlines()


while True:
    ret, frame = cap.read()
    
    # Check if frame was read successfully
    if not ret:
        print("End of video or failed to read frame")
        break
        
    frame = cv2.resize(frame, (980,740))

    results = model(frame)

    for info in results:
        parameters = info.boxes
        for box in parameters:
            x1, y1, x2, y2 = box.xyxy[0]
            x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
            confidence = box.conf[0]
            class_detect = box.cls[0]
            class_detect = int(class_detect)
            class_detect = classnames[class_detect]
            conf = math.ceil(confidence * 100)


            # implement fall detection using the coordinates x1,y1,x2,y2
            height = y2 - y1
            width = x2 - x1
            
            # Calculate aspect ratio (width/height)
            aspect_ratio = width / height if height > 0 else 0
            
            if conf > 80 and class_detect == 'person':
                cvzone.cornerRect(frame, [x1, y1, width, height], l=30, rt=6)
                cvzone.putTextRect(frame, f'{class_detect}', [x1 + 8, y1 - 12], thickness=2, scale=2)
                
                # Enhanced multi-factor fall detection logic
                frame_height = frame.shape[0]
                frame_width = frame.shape[1]
                
                # Calculate key metrics
                vertical_position = (y1 + y2) / 2  # Center Y of person
                relative_height = vertical_position / frame_height  # Vertical position (0=top, 1=bottom)
                height_ratio = height / frame_height  # Person height relative to frame
                width_ratio = width / frame_width  # Person width relative to frame
                
                # Key metric: Distance from bottom (how close person is to ground)
                distance_from_bottom = frame_height - y2
                distance_ratio = distance_from_bottom / frame_height
                
                # Debug: Print info for each detected person
                print(f"\nPerson detected - Conf: {conf}%")
                print(f"  Size: {width}x{height} | Aspect Ratio: {aspect_ratio:.2f}")
                print(f"  Position: ({x1},{y1})-({x2},{y2})")
                print(f"  Height%: {height_ratio:.2f} | Width%: {width_ratio:.2f}")
                print(f"  Vertical Pos%: {relative_height:.2f} | Dist from bottom: {distance_from_bottom}px ({distance_ratio:.2f})")
                
                # IMPROVED FALL DETECTION LOGIC - Optimized for overhead/angled camera
                # Camera mounted at top corner looking down
                # Key insight: A fallen person will have:
                # 1. Wide aspect ratio (width > height)
                # 2. Small height (short bounding box) - appears compressed/flat
                # 3. Position is less important with overhead camera
                
                # Calculate bounding box area (larger area = more of person visible when lying)
                bbox_area = width * height
                frame_area = frame_width * frame_height
                area_ratio = bbox_area / frame_area
                
                # Factor 1: Wide aspect ratio + Small height (classic lying down)
                # Must have BOTH wide ratio AND small height to avoid stretched arms false positive
                is_lying_wide = (aspect_ratio > 1.2) and (height_ratio < 0.35)
                
                # Factor 2: Very short box (compressed/flat appearance from overhead)
                # Regardless of position in frame
                is_compressed = (height_ratio < 0.25) and (aspect_ratio > 0.8)
                
                # Factor 3: Moderate width + Very short (lying at angle)
                # Position independent - works for overhead cameras
                is_horizontal_pose = (aspect_ratio > 0.9) and (height_ratio < 0.3)
                
                # Factor 4: Wide box with significant area coverage
                # Lying person shows more body surface area from above
                is_wide_area = (aspect_ratio > 1.0) and (height_ratio < 0.35) and (area_ratio > 0.05)
                
                # Exclude false positives: 
                # Standing person with stretched arms will have:
                # - Tall bounding box (height_ratio > 0.45)
                # Standing person appears taller even from overhead camera
                is_likely_standing = (height_ratio > 0.45)
                
                # Multi-condition fall detection with false positive filter
                fall_conditions = {
                    'lying_wide': is_lying_wide,
                    'compressed': is_compressed,
                    'horizontal_pose': is_horizontal_pose,
                    'wide_area': is_wide_area
                }
                
                # Person is fallen if ANY condition is met AND they're not likely standing
                is_fallen = any(fall_conditions.values()) and not is_likely_standing
                
                if is_fallen:
                    # Position the "Fall Detected" text above the detected person
                    cvzone.putTextRect(frame, 'Fall Detected', [x1, max(y1 - 50, 10)], 
                                     thickness=3, scale=2, colorR=(0, 0, 255))  # Red color for alert
                    
                    # Determine which condition triggered the detection
                    triggered = [k for k, v in fall_conditions.items() if v]
                    
                    print(f"  *** FALL DETECTED! ***")
                    print(f"  Triggered by: {triggered}")
                    print(f"  Standing check: {is_likely_standing}")
                else:
                    print(f"  Status: Standing/Normal")
                    if is_likely_standing:
                        print(f"  Reason: Likely standing (tall or elevated)")
                
                # Show detailed debugging info on frame
                cvzone.putTextRect(frame, f'R:{aspect_ratio:.2f} H:{height_ratio:.2f}', [x1, y2 + 10], 
                                 thickness=1, scale=1)

    # Write the frame to output video (if recording is enabled)
    if out is not None:
        out.write(frame)

    cv2.imshow('frame', frame)
    if cv2.waitKey(1) & 0xFF == ord('t'):
        break


# Clean up
cap.release()
if out is not None:
    out.release()
cv2.destroyAllWindows()

print(f"\nProcessing completed!")

# Show save information only if video was recorded
if out is not None:
    print(f"Processed video saved as: {output_filename}")
    print(f"Full path: {output_path}")
    
    # Check if file was created successfully
    if os.path.exists(output_path):
        file_size = os.path.getsize(output_path) / (1024 * 1024)  # Size in MB
        print(f"File size: {file_size:.2f} MB")
    else:
        print("Warning: Output file was not created successfully")
else:
    if is_rtsp_stream:
        print("RTSP stream monitoring completed (no recording)")
    else:
        print("Video processing completed")
