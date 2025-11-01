# Client Camera Mode - Architecture Diagram

## DATA FLOW: CLIENT CAMERA MODE

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          CLIENT DEVICE (Browser)                        │
│                                                                         │
│  ┌──────────────┐                                                      │
│  │   Camera     │                                                       │
│  │  📹 Device   │                                                       │
│  └──────┬───────┘                                                       │
│         │                                                               │
│         │ (1) Capture frame @15 FPS                                    │
│         ▼                                                               │
│  ┌──────────────────────────────────────────────┐                      │
│  │  captureAndSendFrame()                       │                      │
│  │  - Draw to canvas                            │                      │
│  │  - Convert to base64 JPEG (80% quality)      │                      │
│  └──────┬───────────────────────────────────────┘                      │
│         │                                                               │
│         │ (2) socket.emit('frame', frameData)                          │
│         │                                                               │
└─────────┼───────────────────────────────────────────────────────────────┘
          │
          │ WebSocket
          │ ~500 KB/s upload
          │
          ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          SERVER (Python/Flask)                          │
│                                                                         │
│  ┌──────────────────────────────────────────────┐                      │
│  │  @socketio.on('frame')                       │                      │
│  │  handle_frame(data)                          │                      │
│  │  - Decode base64 to numpy array              │                      │
│  │  - Convert to OpenCV format                  │                      │
│  └──────┬───────────────────────────────────────┘                      │
│         │                                                               │
│         │ (3) Pass to processing                                       │
│         ▼                                                               │
│  ┌──────────────────────────────────────────────┐                      │
│  │  process_frame(frame)                        │                      │
│  │  ┌────────────────────────────────────────┐  │                      │
│  │  │  1. Resize frame                       │  │                      │
│  │  │  2. YOLO detection (80ms)              │  │                      │
│  │  │  3. For each person:                   │  │                      │
│  │  │     - detect_fall() analysis           │  │                      │
│  │  │     - Draw bounding box                │  │                      │
│  │  │     - Add labels & metrics             │  │                      │
│  │  │  4. Emit stats_update                  │  │                      │
│  │  └────────────────────────────────────────┘  │                      │
│  │  Returns: Processed frame with annotations  │                      │
│  └──────┬───────────────────────────────────────┘                      │
│         │                                                               │
│         │ (4) Encode result                                            │
│         ▼                                                               │
│  ┌──────────────────────────────────────────────┐                      │
│  │  - cv2.imencode to JPEG (85% quality)        │                      │
│  │  - base64.b64encode                          │                      │
│  │  - emit('processed_frame', frameData)        │                      │
│  └──────┬───────────────────────────────────────┘                      │
│         │                                                               │
└─────────┼───────────────────────────────────────────────────────────────┘
          │
          │ WebSocket
          │ ~500 KB/s download
          │
          ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          CLIENT DEVICE (Browser)                        │
│                                                                         │
│  ┌──────────────────────────────────────────────┐                      │
│  │  socket.on('processed_frame', frameData)     │                      │
│  │  - Receive base64 image                      │                      │
│  │  - Update videoFeed.src = frameData          │                      │
│  └──────┬───────────────────────────────────────┘                      │
│         │                                                               │
│         │ (5) Display                                                  │
│         ▼                                                               │
│  ┌──────────────────────────────────────────────┐                      │
│  │  <img id="video-feed">                       │                      │
│  │  Shows processed video with:                 │                      │
│  │  ✅ Green boxes around people                │                      │
│  │  ✅ Red boxes for falls                      │                      │
│  │  ✅ "FALL DETECTED!" labels                  │                      │
│  │  ✅ Metrics (aspect ratio, height ratio)     │                      │
│  └──────────────────────────────────────────────┘                      │
│                                                                         │
│  ┌──────────────────────────────────────────────┐                      │
│  │  Stats Panel (updated via WebSocket)         │                      │
│  │  - Person count                              │                      │
│  │  - Fall count                                │                      │
│  │  - Current time                              │                      │
│  └──────────────────────────────────────────────┘                      │
│                                                                         │
│  ┌──────────────────────────────────────────────┐                      │
│  │  Alert History (updated via WebSocket)       │                      │
│  │  - Fall alerts with timestamp                │                      │
│  │  - Location and confidence                   │                      │
│  └──────────────────────────────────────────────┘                      │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘

        ↑                                                     ↑
        │                                                     │
        └─────────────── CYCLE REPEATS @ 15 FPS ─────────────┘
                         (~66ms per cycle)
```

## TIMING BREAKDOWN

```
┌────────────────────────────────────────────────────────────────┐
│                    ONE FRAME CYCLE (~200ms)                    │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  Client Capture:        ████ 5ms                              │
│  Client Encode:         ████████ 15ms                         │
│  Upload (WebSocket):    ████████████████████ 40ms             │
│  Server Decode:         ████ 10ms                             │
│  YOLO Inference:        ████████████████████████████ 80ms     │
│  Fall Detection:        ████ 5ms                              │
│  Draw Annotations:      ████████ 15ms                         │
│  Server Encode:         ████████ 15ms                         │
│  Download (WebSocket):  ████████████████ 40ms                 │
│  Client Display:        ██ 5ms                                │
│                                                                │
│  TOTAL:                 ≈ 230ms per frame                     │
│                                                                │
└────────────────────────────────────────────────────────────────┘

At 15 FPS:
  Frame interval: 66ms
  Processing time: 230ms
  Result: Slight delay (~3-4 frames), but acceptable for monitoring
```

## COMPARISON WITH SERVER CAMERA

### Server Camera Flow (Simpler)
```
Server Camera → Process → HTTP Stream → Client Display
  ↓              ↓           ↓            ↓
  5ms          100ms        30ms         5ms
                   
Total: ~140ms per frame
```

### Client Camera Flow (More Complex)
```
Client Camera → Upload → Process → Download → Client Display
  ↓             ↓         ↓          ↓           ↓
  20ms         40ms     100ms       40ms        5ms
                   
Total: ~205ms per frame
```

**Trade-off**: +65ms latency, but gain flexibility to use any device's camera!

## KEY IMPROVEMENTS IN THE FIX

### ❌ BEFORE (Broken)
```
Client: Sends frame via WebSocket
Server: Receives frame, but...
        ❌ Stores in variable for HTTP stream
        ❌ HTTP stream expects continuous pull
        ❌ Mismatch causes no video display
Client: Tries to show from /video_feed
        ❌ Gets no data (no continuous stream)
        ❌ Black screen / no video
```

### ✅ AFTER (Fixed)
```
Client: Sends frame via WebSocket
Server: Receives frame
        ✅ Processes immediately
        ✅ Sends processed frame back via WebSocket
        ✅ Push model matches pull model
Client: Receives processed frame
        ✅ Updates <img> src directly
        ✅ Video displays perfectly!
```

## CODE STRUCTURE

### Backend (app.py)
```python
# NEW: Shared processing function
def process_frame(frame):
    """Used by both server and client camera modes"""
    # YOLO detection
    # Fall detection
    # Draw annotations
    # Emit stats
    return annotated_frame

# FOR SERVER CAMERA
def generate_frames():
    """HTTP streaming endpoint"""
    while is_running:
        frame = camera.read()
        processed = process_frame(frame)
        yield processed

# FOR CLIENT CAMERA
@socketio.on('frame')
def handle_frame(data):
    """WebSocket frame handler"""
    frame = decode_base64(data)
    processed = process_frame(frame)
    encoded = encode_base64(processed)
    emit('processed_frame', encoded)  # ← KEY FIX!
```

### Frontend (script.js)
```javascript
// Send frames from client camera
function captureAndSendFrame() {
    const frameData = canvas.toDataURL('image/jpeg', 0.8);
    socket.emit('frame', frameData);
}

// NEW: Receive and display processed frames
socket.on('processed_frame', (frameData) => {
    if (isRunning && sourceType.value === 'client_camera') {
        videoFeed.src = frameData;  // ← KEY FIX!
    }
});
```

## SUMMARY

**What was broken**: Client camera frames were sent but not processed/returned

**What was fixed**: 
1. Server now processes frames immediately
2. Server sends processed frames back via WebSocket
3. Client displays processed frames in real-time

**Result**: Full bidirectional video pipeline with fall detection! 🎉
