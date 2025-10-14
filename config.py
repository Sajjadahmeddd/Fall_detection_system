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
CONFIDENCE_THRESHOLD = 73  # Minimum confidence for person detection (0-100)
FALL_COOLDOWN_SECONDS = 3  # Minimum seconds between fall alerts
MAX_ALERT_HISTORY = 50  # Maximum number of alerts to store

## Fall Detection Thresholds
# Adjust these values to tune detection sensitivity

# Factor 1: Wide aspect ratio + Small height
LYING_WIDE_RATIO = 1.2  # Minimum aspect ratio (width/height)
LYING_WIDE_HEIGHT = 0.45  # Maximum height ratio (height/frame_height)

# Factor 2: Compressed (very short box)
COMPRESSED_HEIGHT = 0.30  # Maximum height ratio
COMPRESSED_RATIO = 0.8  # Minimum aspect ratio

# Factor 3: Horizontal pose
HORIZONTAL_RATIO = 0.9  # Minimum aspect ratio
HORIZONTAL_HEIGHT = 0.4  # Maximum height ratio

# Factor 4: Wide area
WIDE_AREA_RATIO = 1.0  # Minimum aspect ratio
WIDE_AREA_HEIGHT = 0.45  # Maximum height ratio
WIDE_AREA_COVERAGE = 0.05  # Minimum area coverage (5%)

# Factor 5: Very wide
VERY_WIDE_RATIO = 1.8  # Minimum aspect ratio for very wide detection
VERY_WIDE_HEIGHT = 0.55  # Maximum height ratio

# Standing filter
STANDING_HEIGHT_THRESHOLD = 0.55  # Minimum height ratio to be considered standing

# Minimum conditions that must be met for fall detection
MIN_CONDITIONS_FOR_FALL = 2  # Out of 5 conditions

## Video Settings
DEFAULT_FRAME_WIDTH = 980
DEFAULT_FRAME_HEIGHT = 740
WEBCAM_WIDTH = 1280
WEBCAM_HEIGHT = 720

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
