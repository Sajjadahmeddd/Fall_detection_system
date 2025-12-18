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

## Pose-Based Fall Detection Settings (MediaPipe + LSTM)
# New pose-based detection system configuration

# Pose Extraction
POSE_MIN_DETECTION_CONFIDENCE = 0.5  # Minimum confidence for pose detection
POSE_MIN_TRACKING_CONFIDENCE = 0.5  # Minimum confidence for pose tracking
POSE_MODEL_COMPLEXITY = 1  # 0=Lite, 1=Full, 2=Heavy (more accurate but slower)

# Temporal Model
POSE_SEQUENCE_LENGTH = 30  # Number of frames in sliding window (e.g., 30 frames = 1 second at 30fps)
POSE_MODEL_PATH = './checkpoints/best_model.pth'  # Path to trained LSTM/GRU model
POSE_MODEL_TYPE = 'lstm'  # 'lstm' or 'gru'
POSE_CONFIDENCE_THRESHOLD = 0.7  # Minimum confidence to trigger fall alert (0.0-1.0)
POSE_FALL_COOLDOWN = 2.0  # Seconds before detecting another fall

# Model Architecture
POSE_INPUT_SIZE = 34  # 17 keypoints * 2 coordinates (x, y)
POSE_HIDDEN_SIZE = 128  # LSTM hidden layer size
POSE_NUM_LAYERS = 2  # Number of LSTM layers
POSE_DROPOUT = 0.3  # Dropout rate for regularization
POSE_BIDIRECTIONAL = True  # Use bidirectional LSTM

# Frame Processing
POSE_FRAME_WIDTH = 640  # Width for pose extraction
POSE_FRAME_HEIGHT = 480  # Height for pose extraction

## Detection Mode
# Choose between 'yolo' (bounding box) or 'pose' (MediaPipe + LSTM)
DETECTION_MODE = 'pose'  # Options: 'yolo' or 'pose'

## Notes:
# - Lower ratio thresholds = more sensitive (detects more falls, may have false positives)
# - Higher ratio thresholds = less sensitive (misses some falls, fewer false positives)
# - Increase MIN_CONDITIONS_FOR_FALL for higher confidence (fewer false positives)
# - Decrease MIN_CONDITIONS_FOR_FALL for higher sensitivity (may have false positives)
# 
# Pose-based detection notes:
# - POSE_CONFIDENCE_THRESHOLD: Higher = fewer false positives, Lower = more sensitive
# - POSE_SEQUENCE_LENGTH: Longer = more context but slower response
# - Train the model first using train.py before using pose-based detection
