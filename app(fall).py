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
import torch
import numpy as np
import config  # Import configuration

# Import pose-based detection modules
try:
    from pose_extractor import PoseExtractor, PoseSequenceBuffer
    from model import get_model
    POSE_DETECTION_AVAILABLE = True
except Exception as e:
    print(f"Warning: Pose detection not available: {e}")
    POSE_DETECTION_AVAILABLE = False

app = Flask(__name__)
app.config['SECRET_KEY'] = 'fall_detection_secret_key_2024'
socketio = SocketIO(app, cors_allowed_origins="*")

# Global variables
camera = None
model = None
classnames = []
is_running = False
fall_detected_flag = False
fall_alert_history = []
current_source = None
source_type = None
detection_mode = 'yolo'  # 'yolo' or 'pose'
frame_skip_counter = 0
last_fall_time = 0

# Pose-based detection variables
pose_extractor = None
pose_buffer = None
pose_model = None
pose_device = 'cpu'

# Load configuration from config.py
MAX_ALERT_HISTORY = config.MAX_ALERT_HISTORY
FALL_COOLDOWN = config.FALL_COOLDOWN_SECONDS
CONFIDENCE_THRESHOLD = config.CONFIDENCE_THRESHOLD

# Load YOLO model and classes
def load_model():
    global model, classnames
    model = YOLO(config.MODEL_PATH)
    with open(config.CLASSES_FILE, 'r') as f:
        classnames = f.read().splitlines()
    print("YOLO Model loaded successfully!")

# Load Pose-based model
def load_pose_model():
    global pose_model, pose_extractor, pose_buffer, pose_device
    
    if not POSE_DETECTION_AVAILABLE:
        print("Pose detection modules not available!")
        return False
    
    try:
        # Check if model exists
        if not os.path.exists(config.POSE_MODEL_PATH):
            print(f"Warning: Pose model not found at {config.POSE_MODEL_PATH}")
            print("Please train the model first using: python train.py")
            return False
        
        # Load pose extractor
        pose_extractor = PoseExtractor(
            min_detection_confidence=config.POSE_MIN_DETECTION_CONFIDENCE,
            min_tracking_confidence=config.POSE_MIN_TRACKING_CONFIDENCE,
            model_complexity=config.POSE_MODEL_COMPLEXITY
        )
        
        # Initialize pose buffer
        pose_buffer = PoseSequenceBuffer(sequence_length=config.POSE_SEQUENCE_LENGTH)
        
        # Load LSTM model
        pose_device = 'cuda' if torch.cuda.is_available() else 'cpu'
        pose_model = get_model(
            model_type=config.POSE_MODEL_TYPE,
            input_size=config.POSE_INPUT_SIZE,
            hidden_size=config.POSE_HIDDEN_SIZE,
            num_layers=config.POSE_NUM_LAYERS,
            dropout=config.POSE_DROPOUT,
            bidirectional=config.POSE_BIDIRECTIONAL
        )
        
        # Load checkpoint
        checkpoint = torch.load(config.POSE_MODEL_PATH, map_location=pose_device)
        pose_model.load_state_dict(checkpoint['model_state_dict'])
        pose_model.to(pose_device)
        pose_model.eval()
        
        print(f"Pose-based model loaded successfully on {pose_device}!")
        return True
        
    except Exception as e:
        print(f"Error loading pose model: {e}")
        return False

# Initialize camera
def init_camera(source, src_type):
    global camera, current_source, source_type
    
    if camera is not None:
        camera.release()
        time.sleep(0.2)
    
    print(f"📷 Initializing camera: {source} (type: {src_type})")
    
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
        print(f"✅ Camera opened successfully")
        # Read a test frame
        ret, test_frame = camera.read()
        if ret:
            print(f"✅ Test frame read successfully: {test_frame.shape}")
            return True
        else:
            print(f"❌ Failed to read test frame")
            return False
    else:
        print(f"❌ Failed to open camera")
        return False

# Fall detection logic
def detect_fall(frame, box, confidence):
    global fall_detected_flag, fall_alert_history
    
    x1, y1, x2, y2 = box.xyxy[0]
    x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
    
    height = y2 - y1
    width = x2 - x1
    aspect_ratio = width / height if height > 0 else 0
    
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
            
            # Keep only recent alerts
            if len(fall_alert_history) > MAX_ALERT_HISTORY:
                fall_alert_history.pop(0)
            
            # Send real-time alert via WebSocket
            socketio.emit('fall_alert', alert)
    else:
        fall_detected_flag = False
    
    return detection_data

# Pose-based fall detection
def detect_pose_fall(confidence):
    global fall_detected_flag, fall_alert_history, last_fall_time
    
    current_time = time.time()
    
    # Only send alert if cooldown period has passed
    if current_time - last_fall_time > config.POSE_FALL_COOLDOWN:
        fall_detected_flag = True
        last_fall_time = current_time
        
        alert = {
            'timestamp': current_time,
            'time_string': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'location': f"Camera: {current_source}",
            'confidence': int(confidence * 100),
            'mode': 'pose-based',
            'conditions': ['pose-lstm-prediction']  # Add conditions field for consistency
        }
        fall_alert_history.append(alert)
        
        # Keep only recent alerts
        if len(fall_alert_history) > MAX_ALERT_HISTORY:
            fall_alert_history.pop(0)
        
        # Send real-time alert via WebSocket
        try:
            socketio.emit('fall_alert', alert)
            print(f"✅ [ALERT] Fall detected! Confidence: {confidence:.2%}")
            print(f"   Alert emitted: {alert}")
        except Exception as e:
            print(f"❌ [ERROR] Failed to emit alert: {e}")
        
        return True
    else:
        # Still in cooldown
        return False

# Generate video frames
def generate_frames():
    global camera, is_running, model, detection_mode
    global pose_extractor, pose_buffer, pose_model, frame_skip_counter
    
    print(f"🎬 Starting frame generation (mode: {detection_mode})")
    frame_count = 0
    consecutive_failures = 0
    
    while is_running and camera is not None:
        try:
            success, frame = camera.read()
            
            if not success or frame is None:
                consecutive_failures += 1
                print(f"⚠️  Frame read failed (attempt {consecutive_failures}/30)")
                if consecutive_failures > 30:
                    print("❌ Too many consecutive frame read failures. Stopping...")
                    break
                time.sleep(0.1)
                continue
            
            consecutive_failures = 0
            frame_count += 1
            
            # Skip frames for RTSP to reduce latency
            if source_type == 'rtsp' and frame_count % 2 != 0:
                continue
            
            # Resize frame
            frame = cv2.resize(frame, (config.DEFAULT_FRAME_WIDTH, config.DEFAULT_FRAME_HEIGHT))
            
            person_count = 0
            fall_count = 0
            
            if detection_mode == 'yolo':
                # YOLO-based detection
                results = model(frame)
                
                for info in results:
                    parameters = info.boxes
                    for box in parameters:
                        confidence = box.conf[0]
                        class_detect = box.cls[0]
                        class_detect = int(class_detect)
                        class_name = classnames[class_detect]
                        conf = math.ceil(confidence * 100)
                        
                        if conf > config.CONFIDENCE_THRESHOLD and class_name == 'person':
                            person_count += 1
                            
                            # Get detection data
                            detection = detect_fall(frame, box, confidence)
                            
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
            
            elif detection_mode == 'pose' and POSE_DETECTION_AVAILABLE:
                # Pose-based detection
                keypoints = pose_extractor.extract_and_normalize(frame)
                
                if keypoints is not None:
                    person_count = 1
                    pose_buffer.add_frame(keypoints)
                    
                    # Draw pose indicator
                    cv2.putText(frame, "Pose Detected", (10, frame.shape[0] - 70),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                    
                    # Check if buffer is full
                    if pose_buffer.is_full():
                        # Run inference
                        sequence = pose_buffer.get_flattened_sequence()
                        sequence_tensor = torch.FloatTensor(sequence).unsqueeze(0).to(pose_device)
                        
                        with torch.no_grad():
                            output = pose_model(sequence_tensor)
                            probabilities = torch.softmax(output, dim=1)
                            fall_prob = probabilities[0, 1].item()
                        
                        # Check if fall detected
                        if fall_prob > config.POSE_CONFIDENCE_THRESHOLD:
                            fall_count = 1
                            alert_sent = detect_pose_fall(fall_prob)
                            
                            # Draw fall alert
                            h, w = frame.shape[:2]
                            overlay = frame.copy()
                            cv2.rectangle(overlay, (0, 0), (w, h), (0, 0, 255), 20)
                            frame = cv2.addWeighted(frame, 0.7, overlay, 0.3, 0)
                            
                            text = "FALL DETECTED!"
                            text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 2, 3)[0]
                            text_x = (w - text_size[0]) // 2
                            text_y = (h + text_size[1]) // 2
                            
                            cv2.rectangle(frame, 
                                        (text_x - 10, text_y - text_size[1] - 10),
                                        (text_x + text_size[0] + 10, text_y + 10),
                                        (0, 0, 0), -1)
                            
                            cv2.putText(frame, text, (text_x, text_y),
                                       cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 3)
                            
                            conf_text = f"Confidence: {fall_prob:.2%}"
                            cv2.putText(frame, conf_text, (text_x, text_y + 40),
                                       cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                        else:
                            fall_detected_flag = False  # Reset flag when no fall
                            status_text = f"Status: NORMAL ({fall_prob:.2%})"
                            cv2.putText(frame, status_text, (10, 60),
                                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                        
                        # Show confidence on frame
                        buffer_text = f"Buffer: {len(pose_buffer)}/{config.POSE_SEQUENCE_LENGTH} | Confidence: {fall_prob:.1%}"
                    else:
                        buffer_text = f"Buffer: {len(pose_buffer)}/{config.POSE_SEQUENCE_LENGTH} (Filling...)"
                    
                    cv2.putText(frame, buffer_text, (10, frame.shape[0] - 40),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                else:
                    cv2.putText(frame, "No Pose Detected", (10, frame.shape[0] - 70),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                    pose_buffer.reset()
            
            # Show detection mode
            mode_text = f"Mode: {detection_mode.upper()}"
            cv2.putText(frame, mode_text, (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
            
            # Send stats via WebSocket
            try:
                socketio.emit('stats_update', {
                    'person_count': person_count,
                    'fall_count': fall_count,
                    'timestamp': datetime.now().strftime("%H:%M:%S"),
                    'mode': detection_mode
                })
            except Exception as e:
                print(f"⚠️  Failed to emit stats: {e}")
            
            # Encode frame
            ret, buffer = cv2.imencode('.jpg', frame)
            if not ret:
                print("⚠️  Frame encoding failed")
                continue
            frame_bytes = buffer.tobytes()
            
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                
        except Exception as e:
            print(f"❌ Error in frame generation loop: {e}")
            time.sleep(0.1)
            continue
    
    print("🛑 Frame generation stopped")

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
    global is_running, detection_mode, pose_buffer
    
    data = request.json
    source = data.get('source', '0')
    src_type = data.get('type', 'webcam')
    mode = data.get('mode', 'yolo')  # Get detection mode
    
    # Validate mode
    if mode not in ['yolo', 'pose']:
        return jsonify({'status': 'error', 'message': 'Invalid detection mode'}), 400
    
    # Check if pose model is available
    if mode == 'pose' and not POSE_DETECTION_AVAILABLE:
        return jsonify({'status': 'error', 'message': 'Pose detection not available. Please install required packages.'}), 400
    
    if mode == 'pose' and pose_model is None:
        return jsonify({'status': 'error', 'message': 'Pose model not loaded. Please train the model first.'}), 400
    
    detection_mode = mode
    
    if src_type == 'webcam':
        source = int(source)
    
    if init_camera(source, src_type):
        # Reset pose buffer if using pose detection
        if detection_mode == 'pose' and pose_buffer:
            pose_buffer.reset()
        
        is_running = True
        return jsonify({
            'status': 'success', 
            'message': f'Detection started in {mode.upper()} mode',
            'mode': mode
        })
    else:
        return jsonify({'status': 'error', 'message': 'Failed to open camera'}), 400

@app.route('/stop_detection', methods=['POST'])
def stop_detection():
    global is_running, camera, pose_buffer, fall_detected_flag, last_fall_time
    
    is_running = False
    
    # Give time for the loop to exit
    time.sleep(0.3)
    
    if camera is not None:
        try:
            camera.release()
        except Exception as e:
            print(f"Error releasing camera: {e}")
        finally:
            camera = None
    
    # Reset all flags and buffers
    fall_detected_flag = False
    last_fall_time = 0
    
    if pose_buffer:
        pose_buffer.reset()
    
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
        'total_alerts': len(fall_alert_history),
        'mode': detection_mode,
        'pose_available': POSE_DETECTION_AVAILABLE,
        'pose_model_loaded': pose_model is not None
    })

@app.route('/switch_mode', methods=['POST'])
def switch_mode():
    global detection_mode, pose_buffer
    
    data = request.json
    new_mode = data.get('mode', 'yolo')
    
    if new_mode not in ['yolo', 'pose']:
        return jsonify({'status': 'error', 'message': 'Invalid mode'}), 400
    
    if new_mode == 'pose' and not POSE_DETECTION_AVAILABLE:
        return jsonify({'status': 'error', 'message': 'Pose detection not available'}), 400
    
    if new_mode == 'pose' and pose_model is None:
        return jsonify({'status': 'error', 'message': 'Pose model not loaded'}), 400
    
    detection_mode = new_mode
    
    # Reset pose buffer when switching to pose mode
    if detection_mode == 'pose' and pose_buffer:
        pose_buffer.reset()
    
    return jsonify({
        'status': 'success',
        'message': f'Switched to {new_mode.upper()} mode',
        'mode': detection_mode
    })

@app.route('/model_info', methods=['GET'])
def model_info():
    """Get information about available models"""
    info = {
        'yolo': {
            'available': model is not None,
            'path': config.MODEL_PATH if hasattr(config, 'MODEL_PATH') else None
        },
        'pose': {
            'available': POSE_DETECTION_AVAILABLE and pose_model is not None,
            'path': config.POSE_MODEL_PATH if hasattr(config, 'POSE_MODEL_PATH') else None,
            'device': pose_device if pose_model is not None else None,
            'sequence_length': config.POSE_SEQUENCE_LENGTH if hasattr(config, 'POSE_SEQUENCE_LENGTH') else None,
            'confidence_threshold': config.POSE_CONFIDENCE_THRESHOLD if hasattr(config, 'POSE_CONFIDENCE_THRESHOLD') else None
        },
        'current_mode': detection_mode
    }
    return jsonify(info)

# WebSocket events
@socketio.on('connect')
def handle_connect():
    print('Client connected')
    emit('connection_response', {'data': 'Connected to Fall Detection System'})

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

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
    
    print("\n📦 Loading YOLO model...")
    load_model()
    print("✅ YOLO model loaded successfully!")
    
    print("\n📦 Loading Pose-based model...")
    if load_pose_model():
        print("✅ Pose-based model loaded successfully!")
        print("   Both YOLO and Pose detection modes available!")
    else:
        print("⚠️  Pose-based model not available")
        print("   Only YOLO detection mode available")
        print("   To enable pose detection:")
        print("   1. Install dependencies: pip install mediapipe torch")
        print("   2. Train model: python train.py")
    
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
