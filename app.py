from flask import Flask, render_template, Response, jsonify, request
from flask_socketio import SocketIO, emit
import cv2
import cvzone
import math
from ultralytics import YOLO
import threading
import time
from datetime import datetime
import json
import os
import base64
import numpy as np
import config  # Import configuration
from collections import deque
from queue import Queue

app = Flask(__name__)
app.config['SECRET_KEY'] = 'fall_detection_secret_key_2024'
socketio = SocketIO(app, cors_allowed_origins="*", max_http_buffer_size=10**6, async_mode='threading', 
                    engineio_logger=False, ping_timeout=60, ping_interval=25)

# Global variables
camera = None
model = None
classnames = []
is_running = False
fall_detected_flag = False
fall_alert_history = deque(maxlen=config.MAX_ALERT_HISTORY)
current_source = None
source_type = None
use_client_camera = False
latest_frame = None
frame_lock = threading.Lock()
frame_skip_counter = 0
FRAME_SKIP = 0  # Process every frame (0 = no skipping)
JPEG_QUALITY = 75  # Reduced from 85 for faster encoding

# Load configuration from config.py
MAX_ALERT_HISTORY = config.MAX_ALERT_HISTORY
FALL_COOLDOWN = config.FALL_COOLDOWN_SECONDS
CONFIDENCE_THRESHOLD = config.CONFIDENCE_THRESHOLD

# Detect available device
try:
    import torch
    DEVICE = 'cuda' if torch.cuda.is_available() else 'cpu'
except Exception as e:
    print(f"Warning: Could not detect CUDA. Using CPU. ({e})")
    DEVICE = 'cpu'

# Load YOLO model and classes
def load_model():
    global model, classnames
    model = YOLO(config.MODEL_PATH)
    
    # Try to move to device, with fallback
    try:
        model.to(DEVICE)
        if DEVICE == 'cuda':
            try:
                model.half()  # FP16 precision for faster inference on GPU
                print(f"✅ Model loaded successfully on CUDA with FP16!")
            except Exception as e:
                print(f"⚠️ FP16 not supported, using FP32: {e}")
                print(f"✅ Model loaded successfully on CUDA!")
        else:
            print(f"✅ Model loaded successfully on CPU")
    except Exception as e:
        print(f"⚠️ Could not move model to {DEVICE}, using CPU: {e}")
        model.to('cpu')
        DEVICE_ACTUAL = 'cpu'
        print(f"✅ Model loaded successfully on CPU")
    
    with open(config.CLASSES_FILE, 'r') as f:
        classnames = f.read().splitlines()
    print(f"✅ Classes loaded! ({len(classnames)} classes)")

# Initialize camera
def init_camera(source, src_type):
    global camera, current_source, source_type
    
    if camera is not None:
        camera.release()
    
    if src_type == 'webcam':
        camera = cv2.VideoCapture(int(source))
        camera.set(cv2.CAP_PROP_FRAME_WIDTH, config.WEBCAM_WIDTH)
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, config.WEBCAM_HEIGHT)
    elif src_type == 'rtsp':
        camera = cv2.VideoCapture(source)
        camera.set(cv2.CAP_PROP_BUFFERSIZE, config.RTSP_BUFFER_SIZE)
    else:
        camera = cv2.VideoCapture(source)
    
    current_source = source
    source_type = src_type
    
    if camera.isOpened():
        return True
    return False

# Fall detection logic
def detect_fall(frame, box, confidence):
    global fall_detected_flag, fall_alert_history
    
    x1, y1, x2, y2 = box.xyxy[0]
    x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
    
    height = y2 - y1
    width = x2 - x1
    
    # Early exit for invalid dimensions
    if height <= 0 or width <= 0:
        return None
    
    aspect_ratio = width / height
    
    frame_height, frame_width = frame.shape[:2]
    height_ratio = height / frame_height
    
    # Calculate metrics
    bbox_area = width * height
    frame_area = frame_width * frame_height
    area_ratio = bbox_area / frame_area
    
    # Fall detection conditions - using config values
    is_lying_wide = (aspect_ratio > config.LYING_WIDE_RATIO) and (height_ratio < config.LYING_WIDE_HEIGHT)
    is_compressed = (height_ratio < config.COMPRESSED_HEIGHT) and (aspect_ratio > config.COMPRESSED_RATIO)
    is_horizontal_pose = (aspect_ratio > config.HORIZONTAL_RATIO) and (height_ratio < config.HORIZONTAL_HEIGHT)
    is_wide_area = (aspect_ratio > config.WIDE_AREA_RATIO) and (height_ratio < config.WIDE_AREA_HEIGHT) and (area_ratio > config.WIDE_AREA_COVERAGE)
    is_very_wide = (aspect_ratio > config.VERY_WIDE_RATIO) and (height_ratio < config.VERY_WIDE_HEIGHT)
    is_likely_standing = (height_ratio > config.STANDING_HEIGHT_THRESHOLD)
    
    fall_conditions = {
        'lying_wide': is_lying_wide,
        'compressed': is_compressed,
        'horizontal_pose': is_horizontal_pose,
        'wide_area': is_wide_area,
        'very_wide': is_very_wide
    }
    
    conditions_met = sum(fall_conditions.values())
    is_fallen = (conditions_met >= config.MIN_CONDITIONS_FOR_FALL) and not is_likely_standing
    
    detection_data = {
        'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2,
        'width': width, 'height': height,
        'aspect_ratio': round(aspect_ratio, 2),
        'height_ratio': round(height_ratio, 2),
        'conditions_met': conditions_met,
        'is_fallen': is_fallen,
        'triggered_conditions': [k for k, v in fall_conditions.items() if v]
    }
    
    # Send fall alert if detected
    if is_fallen:
        # Check cooldown to avoid spam
        current_time = time.time()
        if not fall_detected_flag or (len(fall_alert_history) > 0 and 
                                     current_time - fall_alert_history[-1]['timestamp'] > FALL_COOLDOWN):
            fall_detected_flag = True
            alert = {
                'timestamp': current_time,
                'time_string': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'location': f"Camera: {current_source}",
                'confidence': int(confidence * 100),
                'conditions': detection_data['triggered_conditions']
            }
            fall_alert_history.append(alert)
            
            # Send real-time alert via WebSocket
            socketio.emit('fall_alert', alert)
    else:
        fall_detected_flag = False
    
    return detection_data

# Process frame (common function for both server and client camera)
def process_frame(frame):
    """Process a single frame and return the annotated frame"""
    global model, classnames
    
    # Resize frame - using smaller size for faster inference
    frame = cv2.resize(frame, (config.DEFAULT_FRAME_WIDTH, config.DEFAULT_FRAME_HEIGHT))
    
    # Run detection with optimized parameters
    results = model(frame, verbose=False, conf=config.CONFIDENCE_THRESHOLD / 100.0, 
                   iou=0.5, device=DEVICE)
    
    person_count = 0
    fall_count = 0
    
    for info in results:
        parameters = info.boxes
        for box in parameters:
            # Handle both CPU and GPU tensors
            try:
                confidence = box.conf[0]
                if hasattr(confidence, 'cpu'):  # GPU tensor
                    confidence = confidence.cpu().numpy()
                else:  # CPU tensor or numpy
                    confidence = float(confidence)
                    
                class_detect = box.cls[0]
                if hasattr(class_detect, 'cpu'):  # GPU tensor
                    class_detect = int(class_detect.cpu().numpy())
                else:  # CPU tensor or numpy
                    class_detect = int(class_detect)
            except Exception as e:
                print(f"Error converting tensors: {e}")
                continue
            
            if class_detect < len(classnames):
                class_name = classnames[class_detect]
                conf = math.ceil(float(confidence) * 100)
                
                if conf > config.CONFIDENCE_THRESHOLD and class_name == 'person':
                    person_count += 1
                    
                    # Get detection data
                    detection = detect_fall(frame, box, confidence)
                    
                    if detection is None:
                        continue
                    
                    x1, y1, x2, y2 = detection['x1'], detection['y1'], detection['x2'], detection['y2']
                    width, height = detection['width'], detection['height']
                    
                    # Draw bounding box
                    if detection['is_fallen']:
                        fall_count += 1
                        # Red box for fall
                        cvzone.cornerRect(frame, [x1, y1, width, height], l=30, rt=6, colorR=(0, 0, 255))
                        cvzone.putTextRect(frame, 'FALL DETECTED!', [x1, max(y1 - 50, 10)], 
                                         thickness=3, scale=2, colorR=(0, 0, 255))
                    else:
                        # Green box for normal
                        cvzone.cornerRect(frame, [x1, y1, width, height], l=30, rt=6, colorR=(0, 255, 0))
                        cvzone.putTextRect(frame, f'{class_name}', [x1 + 8, y1 - 12], 
                                         thickness=2, scale=2, colorR=(0, 255, 0))
                    
                    # Show metrics
                    cvzone.putTextRect(frame, f'R:{detection["aspect_ratio"]} H:{detection["height_ratio"]}', 
                                     [x1, y2 + 10], thickness=1, scale=1)
    
    # Send stats via WebSocket (non-blocking)
    try:
        socketio.emit('stats_update', {
            'person_count': person_count,
            'fall_count': fall_count,
            'timestamp': datetime.now().strftime("%H:%M:%S")
        }, skip_queue=True)
    except:
        pass  # Skip if no active clients
    
    return frame

# Generate video frames (for server camera)
def generate_frames():
    global camera, is_running, frame_skip_counter
    
    while is_running and camera is not None:
        success, frame = camera.read()
        
        if not success:
            break
        
        # Skip frames for performance if needed
        frame_skip_counter += 1
        if frame_skip_counter % (FRAME_SKIP + 1) != 0:
            continue
        
        # Process frame
        frame = process_frame(frame)
        
        # Encode frame with lower quality for faster transmission
        ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
        if not ret:
            continue
            
        frame_bytes = buffer.tobytes()
        
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), 
                   mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/start_detection', methods=['POST'])
def start_detection():
    global is_running, use_client_camera
    
    data = request.json
    source = data.get('source', '0')
    src_type = data.get('type', 'webcam')
    
    # Check if client wants to use their own camera
    if src_type == 'client_camera':
        use_client_camera = True
        is_running = True
        return jsonify({'status': 'success', 'message': 'Client camera mode enabled'})
    else:
        use_client_camera = False
        if src_type == 'webcam':
            source = int(source)
        
        if init_camera(source, src_type):
            is_running = True
            return jsonify({'status': 'success', 'message': 'Detection started'})
        else:
            return jsonify({'status': 'error', 'message': 'Failed to open camera'}), 400

@app.route('/stop_detection', methods=['POST'])
def stop_detection():
    global is_running, camera, use_client_camera, latest_frame
    
    is_running = False
    use_client_camera = False
    with frame_lock:
        latest_frame = None
    
    if camera is not None:
        camera.release()
        camera = None
    
    return jsonify({'status': 'success', 'message': 'Detection stopped'})

@app.route('/get_alerts', methods=['GET'])
def get_alerts():
    return jsonify({'alerts': fall_alert_history})

@app.route('/clear_alerts', methods=['POST'])
def clear_alerts():
    global fall_alert_history
    fall_alert_history = []
    return jsonify({'status': 'success', 'message': 'Alerts cleared'})

@app.route('/status', methods=['GET'])
def status():
    return jsonify({
        'is_running': is_running,
        'source': current_source,
        'type': source_type,
        'total_alerts': len(fall_alert_history)
    })

# WebSocket events
@socketio.on('connect')
def handle_connect():
    print('Client connected')
    emit('connection_response', {'data': 'Connected to Fall Detection System'})

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

@socketio.on('frame')
def handle_frame(data):
    """Receive frame from client camera"""
    global latest_frame, use_client_camera
    
    if not use_client_camera or not is_running:
        return
    
    try:
        # Decode base64 image
        img_data = base64.b64decode(data.split(',')[1])
        nparr = np.frombuffer(img_data, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if frame is not None:
            # Process the frame
            processed_frame = process_frame(frame)
            
            # Encode processed frame back to base64 with lower quality
            ret, buffer = cv2.imencode('.jpg', processed_frame, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
            if ret:
                processed_b64 = base64.b64encode(buffer).decode('utf-8')
                # Send processed frame back to client (non-blocking)
                emit('processed_frame', f'data:image/jpeg;base64,{processed_b64}', skip_queue=True)
    except Exception as e:
        print(f"Error processing frame: {e}")

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'model_loaded': model is not None,
        'is_running': is_running
    })

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 AI FALL DETECTION SYSTEM - WEB APPLICATION")
    print("="*60)
    print("\n📦 Loading AI model...")
    load_model()
    print("✅ Model loaded successfully!")
    print("\n🌐 Starting web server...")
    print("\n" + "="*60)
    print("✨ Server is running!")
    print("="*60)
    # Read port and host from environment (fallback to 8000)
    port = int(os.environ.get('PORT', '8000'))
    host = os.environ.get('HOST', '0.0.0.0')

    print("\n📱 Access the application at:")
    print(f"   → Local:   http://localhost:{port}")
    print(f"   → Network: http://{host}:{port}")
    print("\n💡 Press CTRL+C to stop the server")
    print("="*60 + "\n")

    # Start SocketIO server on configured port
    socketio.run(app, debug=True, host=host, port=port, allow_unsafe_werkzeug=True)
