# Client Camera Mode Guide

## Overview

The Fall Detection Web Application now supports **Client Camera Mode**, which allows any device (laptop, tablet, phone) accessing the web application to use its own camera for fall detection. The video is processed on the server, and results are sent back to the client in real-time.

## How It Works

### Architecture

1. **Client Side**: 
   - Browser accesses the device's camera using WebRTC (getUserMedia API)
   - Captures video frames at ~15 FPS
   - Sends frames to server via WebSocket connection

2. **Server Side**:
   - Receives frames from client via WebSocket
   - Processes frames using YOLO fall detection model
   - Sends back processed video stream with detection overlays
   - Sends real-time statistics and alerts

### Key Features

- ✅ **Zero Configuration**: No need to configure camera IDs or RTSP streams
- ✅ **Cross-Device Support**: Works on any device with a camera (desktop, laptop, tablet, mobile)
- ✅ **Port Forwarding Compatible**: Perfect for dev tunnels and remote access
- ✅ **Real-Time Processing**: Low-latency video processing and alerts
- ✅ **Secure**: Camera access requires user permission

## Usage

### 1. Start the Server

```bash
python app.py
```

Or use the batch file:
```bash
start_webapp.bat
```

### 2. Access via Dev Tunnel (Port Forwarding)

If using VS Code dev tunnels or similar:

```bash
# Example: Server running on port 8000
devtunnel port create -p 8000 --allow-anonymous
```

Share the tunnel URL with clients (e.g., `https://abc123.devtunnels.ms:8000`)

### 3. Open Web Application

Open the provided URL in any browser on any device.

### 4. Start Detection with Client Camera

1. **Select Source Type**: Choose "Client Camera (Your Device)" from the dropdown
2. **Click "Start Detection"**: Browser will request camera permission
3. **Grant Permission**: Allow camera access when prompted
4. **Detection Starts**: Your device's camera feed will be processed in real-time

### 5. Monitor Results

- View live video feed with fall detection overlays
- See real-time statistics (people detected, falls detected)
- Receive instant alerts when falls are detected
- View alert history

## Source Types Comparison

| Source Type | Description | Use Case |
|-------------|-------------|----------|
| **Client Camera** | Uses the camera of the device accessing the web app | Remote monitoring, mobile devices, distributed deployment |
| **Server Webcam** | Uses a camera connected to the server | Local monitoring, fixed camera setup |
| **RTSP Stream** | Connects to IP camera via RTSP | Professional camera systems, existing CCTV |
| **Video File** | Processes a video file on the server | Testing, recorded video analysis |

## Technical Details

### Frame Processing

- **Frame Rate**: ~15 FPS (configurable in code)
- **Resolution**: Captured at 1280x720 (ideal), resized to configured size for processing
- **Compression**: JPEG with 80% quality for efficient transmission
- **Transport**: WebSocket for low-latency bidirectional communication

### Network Requirements

- **Bandwidth**: ~500 KB/s - 1.5 MB/s per client (depending on resolution)
- **Latency**: <200ms typical (depends on network conditions)
- **Protocol**: HTTPS recommended for secure camera access

### Browser Compatibility

| Browser | Support | Notes |
|---------|---------|-------|
| Chrome | ✅ Full | Best performance |
| Edge | ✅ Full | Chromium-based |
| Firefox | ✅ Full | Good performance |
| Safari | ✅ Full | May require HTTPS |
| Mobile Chrome | ✅ Full | Works on Android |
| Mobile Safari | ✅ Full | Works on iOS, requires HTTPS |

## Security Considerations

1. **HTTPS Required**: 
   - Modern browsers require HTTPS for camera access (except localhost)
   - Use SSL/TLS certificates for production deployment
   - Dev tunnels typically provide HTTPS automatically

2. **User Permission**:
   - Camera access requires explicit user permission
   - Permission is per-site and can be revoked anytime

3. **Privacy**:
   - Video frames are only sent while detection is active
   - No recording on server side by default
   - Frames are processed and immediately discarded

## Troubleshooting

### Camera Access Denied

**Problem**: Browser doesn't access camera or shows permission error

**Solutions**:
- Ensure HTTPS is used (required by most browsers)
- Check browser camera permissions in settings
- Verify no other application is using the camera
- Try a different browser

### Poor Performance / Lag

**Problem**: Video stream is choppy or delayed

**Solutions**:
- Check network connection quality
- Reduce frame rate (modify `frameInterval` in script.js)
- Lower JPEG quality (modify `toDataURL` quality parameter)
- Ensure server has adequate CPU/GPU resources

### Connection Issues

**Problem**: WebSocket connection fails or drops

**Solutions**:
- Verify firewall allows WebSocket connections
- Check if reverse proxy/load balancer supports WebSockets
- Ensure port forwarding is configured correctly
- Try restarting the server

### "No Video Feed" After Starting

**Problem**: Detection starts but no video appears

**Solutions**:
- Check browser console for errors (F12)
- Verify camera permissions were granted
- Ensure adequate lighting (camera may not initialize in darkness)
- Try refreshing the page and starting again

## Configuration

### Adjust Frame Rate

In `static/js/script.js`, modify the `startFrameStreaming()` function:

```javascript
// Current: ~15 FPS (66ms interval)
frameInterval = setInterval(() => {
    if (clientVideo && clientVideo.readyState === clientVideo.HAVE_ENOUGH_DATA && isRunning) {
        captureAndSendFrame();
    }
}, 66);

// For 10 FPS: change to 100
// For 20 FPS: change to 50
// For 30 FPS: change to 33
```

### Adjust Video Quality

In `static/js/script.js`, modify the `captureAndSendFrame()` function:

```javascript
// Current: 80% quality
const frameData = canvasElement.toDataURL('image/jpeg', 0.8);

// Higher quality (larger bandwidth): 0.9
// Lower quality (smaller bandwidth): 0.6
```

### Adjust Resolution

In `static/js/script.js`, modify the `startClientCamera()` function:

```javascript
const constraints = {
    video: {
        width: { ideal: 1280 },  // Change as needed
        height: { ideal: 720 },   // Change as needed
        facingMode: 'user'        // 'user' = front camera, 'environment' = back camera
    },
    audio: false
};
```

## Deployment Recommendations

### For Local Network

```bash
python app.py
# Access via: http://<server-ip>:8000
```

### For Internet Access (Dev Tunnel)

```bash
# Install dev tunnel CLI
# Create tunnel
devtunnel port create -p 8000 --allow-anonymous

# Access via: https://<tunnel-url>
```

### For Production

1. Use a proper web server (Nginx + Gunicorn)
2. Configure SSL/TLS certificates
3. Set up proper firewall rules
4. Consider load balancing for multiple clients
5. Monitor server resources (CPU, memory, bandwidth)

## Performance Optimization

### Server Side

- Ensure adequate CPU/GPU for YOLO processing
- Consider using smaller YOLO model (yolov8n.pt instead of yolov8s.pt)
- Limit concurrent client connections if needed
- Use GPU acceleration if available

### Client Side

- Close other applications using camera
- Use wired internet connection if possible
- Ensure good lighting conditions
- Keep browser updated

## API Reference

### New WebSocket Events

**Client → Server**

```javascript
// Send video frame
socket.emit('frame', base64ImageData);
```

**Server → Client**

```javascript
// Existing events still work:
socket.on('stats_update', (data) => { ... });
socket.on('fall_alert', (alert) => { ... });
socket.on('connection_response', (data) => { ... });
```

### New HTTP Endpoints

**POST /start_detection**

```json
{
    "source": "client",
    "type": "client_camera"
}
```

Response:
```json
{
    "status": "success",
    "message": "Client camera mode enabled"
}
```

## Future Enhancements

Potential improvements for future versions:

- [ ] Support for multiple simultaneous client cameras
- [ ] Recording capability for client camera streams
- [ ] Adjustable frame rate from UI
- [ ] Bandwidth usage statistics
- [ ] Mobile app with native camera integration
- [ ] H.264 video encoding for better compression
- [ ] WebRTC peer-to-peer for reduced server load

## Support

For issues or questions:
1. Check this guide's troubleshooting section
2. Review browser console for error messages
3. Check server logs for backend issues
4. Verify network connectivity and permissions

---

**Last Updated**: November 2025
**Version**: 2.0
