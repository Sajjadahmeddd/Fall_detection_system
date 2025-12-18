# Fall Detection Web App Configuration
# ===============================================
# This configuration file is used by BOTH:
# - app.py (Web Application)
# - main.py (CLI Application)
# 
# Changes here will affect both applications!
# ===============================================

## Server Settings
HOST = '0.0.0.0'  # 0.0.0.0 to accept connections from any IP, 127.0.0.1 for localhost only
PORT = 5000
DEBUG = True  # Set to False in production

## Detection Settings
DETECTION_MODEL = 'movenet'  # 'yolo' or 'movenet' - Choose detection method
CONFIDENCE_THRESHOLD = 25  # Minimum confidence for person detection (0-100) - YOLO only
FALL_COOLDOWN_SECONDS = 3  # Minimum seconds between fall alerts
MAX_ALERT_HISTORY = 50  # Maximum number of alerts to store

## MoveNet Pose-Based Fall Detection Settings
# More accurate than YOLO bounding box approach
POSE_KEYPOINT_THRESHOLD = 0.2  # Minimum confidence for pose keypoints (0-1)
TORSO_ANGLE_THRESHOLD = 60  # Minimum torso angle from vertical to detect fall (degrees)
ALIGNMENT_THRESHOLD = 0.6  # Minimum hip-shoulder alignment score (0-1)
BODY_HEIGHT_THRESHOLD = 0.3  # Maximum body height ratio for compressed pose
FALL_SCORE_THRESHOLD = 3  # Minimum score out of 6 to trigger fall alert

## Fall Detection Thresholds
# Adjust these values to tune detection sensitivity

## Ground Proximity Settings (CRITICAL for reducing false positives)
# Person must be close to ground to be considered fallen
GROUND_PROXIMITY_THRESHOLD = 0.15  # Max distance from bottom (15% of frame height)
LOWER_FRAME_THRESHOLD = 0.5  # Person center must be in lower 50% of frame

# Factor 1: Wide aspect ratio + Small height
LYING_WIDE_RATIO = 1.4  # Minimum aspect ratio (increased to reduce false positives)
LYING_WIDE_HEIGHT = 0.35  # Maximum height ratio (stricter)

# Factor 2: Compressed (very short box)
COMPRESSED_HEIGHT = 0.25  # Maximum height ratio (stricter)
COMPRESSED_RATIO = 1.0  # Minimum aspect ratio (increased)

# Factor 3: Horizontal pose
HORIZONTAL_RATIO = 1.2  # Minimum aspect ratio (increased)
HORIZONTAL_HEIGHT = 0.35  # Maximum height ratio (stricter)

# Factor 4: Wide area
WIDE_AREA_RATIO = 1.3  # Minimum aspect ratio (increased)
WIDE_AREA_HEIGHT = 0.4  # Maximum height ratio (stricter)
WIDE_AREA_COVERAGE = 0.08  # Minimum area coverage (8%, increased)

# Factor 5: Very wide
VERY_WIDE_RATIO = 2.0  # Minimum aspect ratio for very wide detection (stricter)
VERY_WIDE_HEIGHT = 0.45  # Maximum height ratio

# Standing filter
STANDING_HEIGHT_THRESHOLD = 0.5  # Minimum height ratio to be considered standing

# Minimum conditions that must be met for fall detection
MIN_CONDITIONS_FOR_FALL = 2  # Out of 5 conditions (requires ground proximity too)

## Video Settings
DEFAULT_FRAME_WIDTH = 640  # Reduced for better performance
DEFAULT_FRAME_HEIGHT = 480  # Reduced for better performance
WEBCAM_WIDTH = 640  # Lower resolution for faster processing
WEBCAM_HEIGHT = 480  # Lower resolution for faster processing
FRAME_SKIP = 2  # Process every Nth frame (1=all frames, 2=every 2nd, 3=every 3rd)
YOLO_IMG_SIZE = 480  # YOLO inference size (lower=faster, higher=more accurate)

## Model Settings
MODEL_PATH = 'yolov8s.pt'
CLASSES_FILE = 'classes.txt'

## RTSP Settings
RTSP_BUFFER_SIZE = 1
RTSP_FPS = 25

## Notes:
# - Lower ratio thresholds = more sensitive (detects more falls, may have false positives)
# - Higher ratio thresholds = less sensitive (misses some falls, fewer false positives)
# - Increase MIN_CONDITIONS_FOR_FALL for higher confidence (fewer false positives)
# - Decrease MIN_CONDITIONS_FOR_FALL for higher sensitivity (may have false positives)
