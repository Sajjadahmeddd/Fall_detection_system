# AI Fall Detection System - Web Application

## 🚀 Futuristic Web Interface with Real-Time Alerts

A modern, responsive web application for real-time fall detection with an advanced alert system.

## ✨ Features

### 🎯 Core Features
- **Real-time Video Processing**: Live video feed with fall detection overlay
- **Multi-Source Support**: Webcam, RTSP streams, and video files
- **Advanced Alert System**: 
  - Real-time fall notifications with WebSocket
  - Audio alerts when fall is detected
  - Alert history with detailed information
  - Modal popups for immediate attention
- **Live Statistics**: Person count, fall count, and timestamp
- **Futuristic UI**: 
  - Animated particles background
  - Neon-glow design elements
  - Responsive layout
  - Dark theme optimized for monitoring

### 🎨 Design Highlights
- Cyberpunk/Futuristic aesthetic with neon accents
- Animated elements and smooth transitions
- Mobile-responsive design
- Real-time data visualization

## 📋 Requirements

Install the required packages:

```bash
pip install -r requirements_webapp.txt
```

Required files:
- `yolov8s.pt` - YOLO model file
- `classes.txt` - Class names file

## 🚀 How to Run

1. **Install Dependencies**:
   ```bash
   pip install flask flask-socketio opencv-python cvzone ultralytics
   ```

2. **Start the Web Server**:
   ```bash
   python app.py
   ```

3. **Open Your Browser**:
   Navigate to: `http://localhost:5000`

4. **Configure Source**:
   - Select source type (Webcam/RTSP/File)
   - Enter source identifier
   - Click "Start Detection"

## 🎮 Usage Guide

### Using Webcam
1. Select "Webcam" from source type
2. Enter webcam ID (0 for default, 1 for second camera)
3. Click "Start Detection"

### Using RTSP Stream
1. Select "RTSP Stream" from source type
2. Enter RTSP URL: `rtsp://username:password@ip:port/stream`
3. Click "Start Detection"

### Using Video File
1. Select "Video File" from source type
2. Enter full path to video file
3. Click "Start Detection"

## 🔔 Alert System

### Real-Time Alerts
- **Visual Alerts**: Red bounding box and "FALL DETECTED" label on video
- **Modal Popup**: Full-screen alert notification with details
- **Audio Alert**: Beep sound when fall is detected
- **Alert History**: List of all detected falls with timestamps

### Alert Information
Each alert includes:
- Timestamp
- Camera location
- Detection confidence
- Triggered conditions
- Visual snapshot (on video feed)

### Managing Alerts
- **Acknowledge**: Click "Acknowledge" on modal to dismiss
- **Clear History**: Click trash icon to clear all alerts
- **Auto-limit**: Keeps last 50 alerts automatically

## 📊 Detection Logic

The system uses multiple conditions for high-accuracy fall detection:

1. **lying_wide**: Wide aspect ratio + Small height
2. **compressed**: Very short box + Wide ratio
3. **horizontal_pose**: Moderate width + Short height
4. **wide_area**: Wide box + Significant area coverage
5. **very_wide**: Very wide aspect ratio (>1.8)

**Trigger Condition**: At least 2 conditions must be met AND person not standing

## 🎨 UI Features

### Main Dashboard
- **Live Video Feed**: Real-time processed video with detection overlays
- **Stats Bar**: Live person count, fall count, current time
- **Control Panel**: Source selection and start/stop controls
- **Alert Panel**: Scrollable history of all fall detections

### Visual Indicators
- **Green Box**: Normal person detected
- **Red Box**: Fall detected
- **Status Badge**: Active (glowing green) / Inactive (gray)
- **Metrics Display**: Aspect ratio and height ratio on each detection

## 🌐 Network Access

To access from other devices on your network:

1. Find your computer's IP address:
   ```bash
   ipconfig  # Windows
   ifconfig  # Linux/Mac
   ```

2. Access from other devices:
   ```
   http://YOUR_IP_ADDRESS:5000
   ```

## 🔧 Configuration

### Adjusting Detection Sensitivity
Edit `app.py` and modify these values:

```python
# Fall detection thresholds
is_lying_wide = (aspect_ratio > 1.2) and (height_ratio < 0.45)
is_compressed = (height_ratio < 0.30) and (aspect_ratio > 0.8)
# ... etc
```

### Alert Cooldown
Modify alert frequency in `app.py`:

```python
FALL_COOLDOWN = 3  # Seconds between alerts
```

### Alert History Limit
Change max alerts stored:

```python
MAX_ALERT_HISTORY = 50  # Number of alerts to keep
```

## 📱 Browser Compatibility

Tested and working on:
- ✅ Chrome/Edge (Recommended)
- ✅ Firefox
- ✅ Safari
- ✅ Mobile browsers

## 🐛 Troubleshooting

### Video Feed Not Loading
- Check if camera/source is accessible
- Verify no other application is using the camera
- Check browser console for errors

### WebSocket Connection Issues
- Ensure port 5000 is not blocked by firewall
- Check if Flask-SocketIO is installed correctly
- Try clearing browser cache

### High CPU Usage
- Reduce video resolution in camera settings
- Use YOLO nano model instead of yolov8s
- Adjust frame processing rate

## 🔒 Security Notes

⚠️ This is a development server. For production:
- Use a production WSGI server (gunicorn, waitress)
- Enable HTTPS
- Add authentication
- Implement rate limiting
- Sanitize user inputs

## 📄 License

This project is for educational and monitoring purposes.

## 🤝 Contributing

Feel free to submit issues and enhancement requests!

## 📧 Support

For issues or questions, create an issue on the repository.

---

**Made with ❤️ for safety and security**
