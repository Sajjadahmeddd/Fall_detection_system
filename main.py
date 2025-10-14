import cv2
import cvzone
import math
from ultralytics import YOLO
import tkinter as tk
from tkinter import filedialog
import os
from datetime import datetime
import config  # Import configuration settings

# Create a root window and hide it
root = tk.Tk()
root.withdraw()

# Ask user to choose between file, RTSP stream, or webcam
choice = input("Choose input source:\n1. Video file\n2. RTSP Camera Stream\n3. Webcam\nEnter choice (1, 2, or 3): ").strip()

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
    is_webcam = False

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
    is_webcam = False

elif choice == '3':
    # Use webcam
    print("\nWebcam Configuration:")
    webcam_id = input("Enter webcam ID (0 for default, 1 for second camera, etc.): ").strip()
    
    # Use default webcam if no input or invalid input
    try:
        video_path = int(webcam_id) if webcam_id else 0
    except ValueError:
        print("Invalid webcam ID. Using default webcam (0)...")
        video_path = 0
    
    print(f"Using webcam ID: {video_path}")
    is_rtsp_stream = False
    is_webcam = True

else:
    print("Invalid choice. Exiting...")
    exit()

cap = cv2.VideoCapture(video_path)

# Configure RTSP stream settings for better reliability
if is_rtsp_stream:
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Reduce buffer size for lower latency
    cap.set(cv2.CAP_PROP_FPS, 25)  # Set FPS for RTSP
    print("Connecting to RTSP stream... This may take a few seconds...")
elif is_webcam:
    print("Connecting to webcam... This may take a few seconds...")
    # Optional: Set webcam resolution for better performance
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

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
    elif is_webcam:
        print(f"Error: Could not open webcam with ID '{video_path}'")
        print("Please check:")
        print("- Webcam is properly connected")
        print("- Webcam drivers are installed")
        print("- No other application is using the webcam")
        print("- Try a different webcam ID (0, 1, 2, etc.)")
    else:
        print(f"Error: Could not open video file '{video_path}'")
        print("Please make sure the file exists and is a valid video format.")
    exit()

# Get video properties for output
if is_webcam or is_rtsp_stream:
    fps = 25  # Default FPS for webcam and RTSP
else:
    fps = int(cap.get(cv2.CAP_PROP_FPS))
width = 980  # Using the resized width
height = 740  # Using the resized height

# Video writer setup
out = None
if not is_rtsp_stream and not is_webcam:
    # Only save video files, not live streams or webcam
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
    # For RTSP streams and webcam, ask if user wants to record
    source_name = "RTSP stream" if is_rtsp_stream else "webcam"
    record_choice = input(f"Do you want to record the {source_name}? (y/n): ").strip().lower()
    if record_choice == 'y':
        current_folder = os.path.dirname(os.path.abspath(__file__))
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if is_rtsp_stream:
            output_filename = f"fall_detection_rtsp_stream_{timestamp}.mp4"
        else:
            output_filename = f"fall_detection_webcam_{timestamp}.mp4"
        output_path = os.path.join(current_folder, output_filename)
        
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        print(f"Recording {source_name} to: {output_filename}")

print("Connection established! Starting fall detection...")
if is_rtsp_stream:
    print("Live RTSP stream - Press 't' to stop")
elif is_webcam:
    print("Live webcam - Press 't' to stop")
else:
    print("Press 't' to stop the video")

model = YOLO(config.MODEL_PATH)

classnames = []
with open(config.CLASSES_FILE, 'r') as f:
    classnames = f.read().splitlines()


while True:
    ret, frame = cap.read()
    
    # Check if frame was read successfully
    if not ret:
        print("End of video or failed to read frame")
        break
        
    frame = cv2.resize(frame, (config.DEFAULT_FRAME_WIDTH, config.DEFAULT_FRAME_HEIGHT))

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
            
            if conf > config.CONFIDENCE_THRESHOLD and class_detect == 'person':
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
                # Relaxed height threshold for webcam and close-range cameras
                is_lying_wide = (aspect_ratio > config.LYING_WIDE_RATIO) and (height_ratio < config.LYING_WIDE_HEIGHT)
                
                # Factor 2: Very short box (compressed/flat appearance from overhead)
                # Regardless of position in frame
                is_compressed = (height_ratio < config.COMPRESSED_HEIGHT) and (aspect_ratio > config.COMPRESSED_RATIO)
                
                # Factor 3: Moderate width + Reasonable short height (lying at angle)
                # Position independent - works for overhead cameras and webcams
                is_horizontal_pose = (aspect_ratio > config.HORIZONTAL_RATIO) and (height_ratio < config.HORIZONTAL_HEIGHT)
                
                # Factor 4: Wide box with significant area coverage
                # Lying person shows more body surface area from above
                is_wide_area = (aspect_ratio > config.WIDE_AREA_RATIO) and (height_ratio < config.WIDE_AREA_HEIGHT) and (area_ratio > config.WIDE_AREA_COVERAGE)
                
                # Factor 5: Very wide aspect ratio (clear horizontal orientation)
                # Strong indicator of lying down regardless of height
                is_very_wide = (aspect_ratio > config.VERY_WIDE_RATIO) and (height_ratio < config.VERY_WIDE_HEIGHT)
                
                # Exclude false positives: 
                # Standing person with stretched arms will have:
                # - Tall bounding box (height_ratio > 0.55)
                # Increased threshold to avoid missing falls in webcam scenarios
                is_likely_standing = (height_ratio > config.STANDING_HEIGHT_THRESHOLD)
                
                # Multi-condition fall detection with false positive filter
                fall_conditions = {
                    'lying_wide': is_lying_wide,
                    'compressed': is_compressed,
                    'horizontal_pose': is_horizontal_pose,
                    'wide_area': is_wide_area,
                    'very_wide': is_very_wide
                }
                
                # Higher confidence: Require at least 2 conditions to be met
                # AND person must not be standing
                conditions_met = sum(fall_conditions.values())
                is_fallen = (conditions_met >= config.MIN_CONDITIONS_FOR_FALL) and not is_likely_standing
                
                if is_fallen:
                    # Position the "Fall Detected" text above the detected person
                    cvzone.putTextRect(frame, 'Fall Detected', [x1, max(y1 - 50, 10)], 
                                     thickness=3, scale=2, colorR=(0, 0, 255))  # Red color for alert
                    
                    # Determine which condition triggered the detection
                    triggered = [k for k, v in fall_conditions.items() if v]
                    
                    print(f"  *** FALL DETECTED! ***")
                    print(f"  Triggered by: {triggered} ({conditions_met}/5 conditions met)")
                    print(f"  Standing check: {is_likely_standing}")
                else:
                    print(f"  Status: Standing/Normal ({conditions_met}/5 conditions met)")
                    if is_likely_standing:
                        print(f"  Reason: Likely standing (tall or elevated)")
                    elif conditions_met == 1:
                        print(f"  Reason: Only 1 condition met (need 2+)")
                
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
    elif is_webcam:
        print("Webcam monitoring completed (no recording)")
    else:
        print("Video processing completed")
