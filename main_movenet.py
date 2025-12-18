"""
MoveNet-based Fall Detection - Standalone Script
Run this to test fall detection on video files or webcam
"""

import cv2
import numpy as np
import tkinter as tk
from tkinter import filedialog
import os
from datetime import datetime
import config
from pose_fall_detector import PoseFallDetector

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
    
    if not video_path:
        print("No video file selected. Exiting...")
        exit()
    
    print(f"Selected video: {video_path}")
    is_rtsp_stream = False
    is_webcam = False

elif choice == '2':
    # Get RTSP URL from user
    print("\nRTSP Stream Configuration:")
    print("Example: rtsp://username:password@ip:port/stream")
    
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

# Initialize video capture
cap = cv2.VideoCapture(video_path)

# Configure settings
if is_rtsp_stream:
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    print("Connecting to RTSP stream...")
elif is_webcam:
    print("Connecting to webcam...")
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.WEBCAM_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.WEBCAM_HEIGHT)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

# Check if opened successfully
if not cap.isOpened():
    if is_rtsp_stream:
        print(f"Error: Could not connect to RTSP stream")
    elif is_webcam:
        print(f"Error: Could not open webcam")
    else:
        print(f"Error: Could not open video file")
    exit()

print("\n" + "="*60)
print("Loading MoveNet Pose Estimation Model...")
print("="*60)

# Load pose detector
pose_detector = PoseFallDetector()

print("\n✅ Model loaded successfully!")
print("\nStarting fall detection...")
print("Press 'q' to quit\n")

frame_count = 0
fall_count = 0

while True:
    ret, frame = cap.read()
    
    if not ret:
        print("End of video or failed to read frame")
        break
    
    frame_count += 1
    
    # Resize frame
    frame = cv2.resize(frame, (config.DEFAULT_FRAME_WIDTH, config.DEFAULT_FRAME_HEIGHT))
    
    # Run pose-based fall detection
    is_fallen, detection_data = pose_detector.detect_fall(frame, config)
    
    # Draw skeleton on frame
    if 'keypoints' in detection_data:
        frame = pose_detector.draw_skeleton(frame, detection_data['keypoints'])
    
    # Display detection info
    if 'error' not in detection_data:
        # Draw torso angle line
        if 'shoulder_mid' in detection_data and 'hip_mid' in detection_data:
            shoulder = tuple(map(int, detection_data['shoulder_mid']))
            hip = tuple(map(int, detection_data['hip_mid']))
            color = (0, 0, 255) if is_fallen else (0, 255, 0)
            cv2.line(frame, shoulder, hip, color, 3)
        
        # Display metrics on frame
        y_offset = 30
        metrics = [
            f"Frame: {frame_count}",
            f"Torso Angle: {detection_data['torso_angle']}°",
            f"Alignment: {detection_data['alignment_score']:.2f}",
            f"Body Height: {detection_data['body_height_ratio']:.2f}",
            f"Fall Score: {detection_data['fall_score']}/6"
        ]
        
        for i, metric in enumerate(metrics):
            cv2.putText(frame, metric, (10, y_offset + i * 25), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        # Fall alert
        if is_fallen:
            fall_count += 1
            cv2.putText(frame, "*** FALL DETECTED ***", 
                       (int(frame.shape[1]/2) - 150, 60),
                       cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 3)
            
            # Print to console
            print(f"\n[Frame {frame_count}] *** FALL DETECTED ***")
            print(f"  Torso Angle: {detection_data['torso_angle']}°")
            print(f"  Alignment Score: {detection_data['alignment_score']:.2f}")
            print(f"  Fall Score: {detection_data['fall_score']}/6")
            print(f"  Conditions: {', '.join(detection_data['conditions'])}")
        
        # Display status at bottom
        status = f"Falls Detected: {fall_count}"
        cv2.putText(frame, status, (10, frame.shape[0] - 15), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
    else:
        # Error message
        cv2.putText(frame, "No person detected", (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
    
    cv2.imshow('MoveNet Fall Detection', frame)
    
    # Exit on 'q' key
    if cv2.waitKey(1) & 0xFF == ord('q'):
        print("\nStopped by user")
        break

# Cleanup
cap.release()
cv2.destroyAllWindows()

print("\n" + "="*60)
print("Processing completed!")
print(f"Total frames processed: {frame_count}")
print(f"Total falls detected: {fall_count}")
print("="*60)
