from flask import Flask, render_template, Response, jsonify, request
from flask_socketio import SocketIO, emit
import cv2
import numpy as np
import time
from datetime import datetime
import os
import config
from pose_fall_detector import PoseFallDetector

app = Flask(__name__)
app.config['SECRET_KEY'] = 'fall_detection_secret_key_2024'
socketio = SocketIO(app, cors_allowed_origins="*")

# Global variables
camera = None
pose_detector = None
is_running = False
fall_detected_flag = False
fall_alert_history = []
current_source = None
source_type = None

# Load configuration from config.py
MAX_ALERT_HISTORY = config.MAX_ALERT_HISTORY
FALL_COOLDOWN = config.FALL_COOLDOWN_SECONDS

# Load MoveNet pose detector
def load_model():
    global pose_detector
    pose_detector = PoseFallDetector()
    print("Pose detection model loaded successfully!")

# Initialize camera
def init_camera(source, src_type):
    global camera, current_source, source_type
    
    if camera is not None:
        camera.release()
    
    if src_type == 'webcam':
        camera = cv2.VideoCapture(int(source), cv2.CAP_DSHOW)  # CAP_DSHOW for better Windows performance
        camera.set(cv2.CAP_PROP_FRAME_WIDTH, config.WEBCAM_WIDTH)
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, config.WEBCAM_HEIGHT)
        camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Minimize buffer for lower latency
        camera.set(cv2.CAP_PROP_FPS, 30)  # Set target FPS
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

# Generate video frames
def generate_frames():
    global camera, is_running, pose_detector, fall_detected_flag, fall_alert_history
    
    frame_count = 0
    
    while is_running and camera is not None:
        success, frame = camera.read()
        
        if not success:
            break
        
        frame_count += 1
        
        # Resize frame
        frame = cv2.resize(frame, (config.DEFAULT_FRAME_WIDTH, config.DEFAULT_FRAME_HEIGHT))
        
        # Skip frames for better performance (process every Nth frame)
        if frame_count % config.FRAME_SKIP != 0:
            ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
            frame_bytes = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            continue
        
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
            
            # Display metrics
            y_offset = 30
            metrics = [
                f"Torso Angle: {detection_data['torso_angle']}°",
                f"Alignment: {detection_data['alignment_score']}",
                f"Fall Score: {detection_data['fall_score']}/6"
            ]
            
            for i, metric in enumerate(metrics):
                cv2.putText(frame, metric, (10, y_offset + i * 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
            # Fall alert
            if is_fallen:
                cv2.putText(frame, "*** FALL DETECTED ***", 
                           (int(frame.shape[1]/2) - 150, 60),
                           cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255), 3)
                
                # Check cooldown to avoid spam
                current_time = time.time()
                if not fall_detected_flag or (len(fall_alert_history) > 0 and 
                                             current_time - fall_alert_history[-1]['timestamp'] > FALL_COOLDOWN):
                    fall_detected_flag = True
                    alert = {
                        'timestamp': current_time,
                        'time_string': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        'location': f"Camera: {current_source}",
                        'torso_angle': detection_data['torso_angle'],
                        'fall_score': detection_data['fall_score'],
                        'conditions': detection_data['conditions']
                    }
                    fall_alert_history.append(alert)
                    
                    # Keep only recent alerts
                    if len(fall_alert_history) > MAX_ALERT_HISTORY:
                        fall_alert_history.pop(0)
                    
                    # Send real-time alert via WebSocket
                    socketio.emit('fall_alert', alert)
            else:
                fall_detected_flag = False
            
            # Send stats via WebSocket
            socketio.emit('stats_update', {
                'person_detected': True,
                'fall_detected': is_fallen,
                'torso_angle': detection_data['torso_angle'],
                'timestamp': datetime.now().strftime("%H:%M:%S")
            })
        
        # Encode frame
        ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
        frame = buffer.tobytes()
        
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

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
    global is_running
    
    data = request.json
    source = data.get('source', '0')
    src_type = data.get('type', 'webcam')
    
    if src_type == 'webcam':
        source = int(source)
    
    if init_camera(source, src_type):
        is_running = True
        return jsonify({'status': 'success', 'message': 'Detection started'})
    else:
        return jsonify({'status': 'error', 'message': 'Failed to open camera'}), 400

@app.route('/stop_detection', methods=['POST'])
def stop_detection():
    global is_running, camera
    
    is_running = False
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
        'total_alerts': len(fall_alert_history),
        'detection_model': 'MoveNet Pose'
    })

# WebSocket events
@socketio.on('connect')
def handle_connect():
    print('Client connected')
    emit('connection_response', {'data': 'Connected to Fall Detection System (MoveNet Pose)'})

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'model_loaded': pose_detector is not None,
        'model_type': 'MoveNet Pose Estimation',
        'is_running': is_running
    })

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 AI FALL DETECTION SYSTEM - MOVENET POSE")
    print("="*60)
    print("\n📦 Loading MoveNet pose estimation model...")
    load_model()
    print("✅ Model loaded successfully!")
    print("\n🌐 Starting web server...")
    print("\n" + "="*60)
    print("✨ Server is running!")
    print("="*60)
    port = int(os.environ.get('PORT', '8000'))
    host = os.environ.get('HOST', '0.0.0.0')

    print("\n📱 Access the application at:")
    print(f"   → Local:   http://localhost:{port}")
    print(f"   → Network: http://{host}:{port}")
    print("\n💡 Press CTRL+C to stop the server")
    print("="*60 + "\n")

    socketio.run(app, debug=True, host=host, port=port, allow_unsafe_werkzeug=True)
