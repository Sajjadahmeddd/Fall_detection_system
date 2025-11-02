# 🌐 Accessing Your Running Fall Detection System

## ✅ App is Running Right Now!

Your fall detection system is currently running and ready to use.

---

## How to Access the Web Interface

### Option 1: Local Access (Same Computer)
Open your browser and go to:
```
http://localhost:8000
```

### Option 2: Network Access (From Another Device)
Open your browser and go to:
```
http://192.168.1.2:8000
```

Replace `192.168.1.2` with your computer's IP address if different.

---

## What You'll See

When you open the app, you'll see:

### Main Interface
```
┌─────────────────────────────────────────────────────────┐
│           AI FALL DETECTION SYSTEM                      │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  Live Feed                │  Controls & Alerts         │
│ ┌──────────────────────┐  │ ┌──────────────────────┐  │
│ │                      │  │ │ Source Type:        │  │
│ │   Camera Feed        │  │ │ ☑ Client Camera    │  │
│ │   (will show video)  │  │ │ ○ Server Webcam    │  │
│ │                      │  │ │ ○ RTSP Stream      │  │
│ │                      │  │ │                     │  │
│ └──────────────────────┘  │ │ [START] [STOP]     │  │
│                           │ │                     │  │
│ People: 0 │ Falls: 0     │ │ Alert History       │  │
│ Time: --:--:--           │ │                     │  │
│                           │ │ No alerts yet       │  │
│                           │ └──────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

---

## Getting Started

### Step 1: Choose a Source
Click the dropdown under "Source Type" and select:
- **Client Camera** (uses your device's camera)
- **Server Webcam** (uses server's webcam - enter ID like 0, 1, etc.)
- **RTSP Stream** (enter RTSP URL)
- **Video File** (enter file path)

### Step 2: Click "START DETECTION"
```
[▶️ START DETECTION]
```

### Step 3: Watch the Live Feed
The video from your selected source will appear in the "Live Feed" section.

### Step 4: Monitor for Falls
- Green boxes: Normal people detected
- Red boxes: Fall detected!
- Statistics show: People count and falls count
- Alerts appear in the right panel

### Step 5: Stop When Done
```
[⏹️ STOP DETECTION]
```

---

## Using Different Sources

### Client Camera (Your Device)
1. Select: **Client Camera**
2. Click: **START DETECTION**
3. Browser will ask for camera permission
4. Click: **Allow**
5. Feed starts streaming

### Server Webcam
1. Select: **Server Webcam**
2. Enter: Webcam ID (usually `0` for default)
3. Click: **START DETECTION**

### RTSP Stream (IP Camera)
1. Select: **RTSP Stream**
2. Enter: `rtsp://username:password@ip:port/stream`
3. Click: **START DETECTION**

Example:
```
rtsp://admin:password@192.168.1.100:554/stream1
```

### Video File
1. Select: **Video File**
2. Enter: Full path to video file
3. Click: **START DETECTION**

Example:
```
C:\Videos\fall_test.mp4
```

---

## Understanding the Display

### Live Feed Section
- Shows real-time video stream
- **Green boxes** = normal person
- **Red boxes** = fall detected
- Metrics shown: Aspect ratio (R) and Height ratio (H)

### Statistics Bar
```
👥 People Detected: 3
⚠️ Falls Detected: 1
🕐 Current Time: 15:37:42
```

### Alert Panel
Shows all detected falls with:
- **Time** of detection
- **Location** (camera name)
- **Confidence** percentage
- **Conditions** that triggered alert

### Fall Detected Modal
When a fall is detected:
```
⚠️ FALL DETECTED!

A fall has been detected at Camera: 0
Time: 2025-11-02 15:37:42 | Confidence: 95%

[✓ ACKNOWLEDGE]
```

---

## Features Available

### Alert Management
- **Clear Alerts**: Remove all alerts from history
- **View History**: See all past detections
- **Real-time Notifications**: Instant alerts when falls detected

### Performance Monitoring
- **FPS Counter**: ~5 FPS on CPU
- **Detection Count**: People and falls tracked
- **Status Badge**: Active/Inactive

### Camera Controls
- **Start/Stop**: Easy control buttons
- **Multiple Sources**: Switch between cameras
- **Real-time Processing**: See results instantly

---

## Keyboard Shortcuts (Optional)

While viewing the app:
- `Ctrl+C` in terminal: Stop the server
- `F5`: Refresh the webpage
- `F12`: Open browser dev tools (for debugging)

---

## Mobile Access

To access from your phone/tablet:

1. Find your computer's IP address:
   - Windows: Open Command Prompt, type `ipconfig`, look for "IPv4 Address"
   - Example: `192.168.1.2`

2. On your mobile device, open browser and go to:
   ```
   http://192.168.1.2:8000
   ```

3. You'll see the same interface and can monitor falls remotely!

---

## Performance on This Device

### Expected Performance
- **FPS**: ~5 frames per second
- **Latency**: ~200ms per frame
- **Memory**: ~500MB
- **CPU Usage**: ~40-60%

### What This Means
- Smooth detection for typical fall scenarios
- Quick alerts (usually <1 second)
- Suitable for single user monitoring
- Works fine for testing and development

---

## Troubleshooting

### Q: Can't open http://localhost:8000
**A:** 
1. Make sure app is running (check terminal)
2. Try http://127.0.0.1:8000 instead
3. Check if port 8000 is already in use

### Q: Camera isn't working
**A:**
1. Make sure you granted browser permission
2. Check if camera is available on your system
3. Try a different camera ID (0, 1, 2, etc.)

### Q: No video appearing
**A:**
1. Check terminal for errors
2. Verify camera/stream is working
3. Try starting detection again

### Q: Alerts not showing up
**A:**
1. Check if fall detection is enabled
2. Verify detection parameters in config.py
3. Ensure person is in the frame

### Q: Connection dropped
**A:**
1. Check internet/network connection
2. Restart the app
3. Refresh the webpage (F5)

---

## Accessing from Different Computers

### Network Setup
Your app runs on: **http://192.168.1.2:8000**

### From Another Computer on Same Network
1. Open browser on other computer
2. Type: `http://192.168.1.2:8000`
3. Should see the same interface

### From Outside Your Network
To access from outside (internet):
1. Enable port forwarding on router (advanced)
2. Use your public IP address
3. Not recommended for security - use VPN instead

---

## Useful URLs

| URL | Purpose |
|-----|---------|
| `http://localhost:8000/` | Main interface |
| `http://localhost:8000/status` | System status (JSON) |
| `http://localhost:8000/health` | Health check |
| `http://localhost:8000/get_alerts` | Get all alerts (JSON) |
| `http://localhost:8000/video_feed` | Live video stream |

---

## API Endpoints (For Developers)

### Check System Status
```bash
curl http://localhost:8000/status
```

Response:
```json
{
  "is_running": true,
  "source": "0",
  "type": "webcam",
  "total_alerts": 5
}
```

### Get All Alerts
```bash
curl http://localhost:8000/get_alerts
```

### Clear Alerts
```bash
curl -X POST http://localhost:8000/clear_alerts
```

---

## Tips for Best Results

1. **Good Lighting**: Ensure well-lit environment for better detection
2. **Clear View**: Position camera to see full body
3. **Camera Height**: 6-8 feet high for best angle
4. **Avoid Glare**: Prevent direct sunlight on camera
5. **Test First**: Verify detection is working before relying on it

---

## System Requirements for Access

### Browser Requirements
- Modern browser (Chrome, Firefox, Safari, Edge)
- JavaScript enabled
- WebSocket support
- Camera permission (for client camera mode)

### Network Requirements
- Stable internet/LAN connection
- Port 8000 accessible
- Recommended: 10 Mbps for smooth streaming

### Device Requirements
- Computer running the app
- Camera or RTSP stream available
- Display to see alerts

---

## Summary

✅ **Your system is ready to use!**

1. Open: **http://localhost:8000**
2. Select: Camera source
3. Click: **START DETECTION**
4. Watch: Live feed with detections
5. Get: Real-time alerts

**Enjoy fall detection! 🚀**

