# Performance Optimization Guide

## Summary of Optimizations Made

### 1. **Backend Optimizations (app.py)**

#### Model Optimization
- **GPU Acceleration**: Model now uses CUDA (GPU) by default for faster inference
- **FP16 Precision**: Enabled half-precision (FP16) on GPU for 2x speedup with minimal accuracy loss
- **Inference Parameters**: Added `verbose=False` to suppress logging overhead
- **Confidence Filtering**: Moved confidence threshold to model inference level

#### Memory & Data Structure Optimization
- **Deque instead of List**: Changed `fall_alert_history` from list to `deque` with max length for O(1) append
- **Reduced HTTP Buffer**: Lowered `max_http_buffer_size` from 100MB to 10MB to reduce memory usage
- **JPEG Quality**: Reduced from 85 to 75 for faster encoding/transmission (minimal visual impact)

#### Processing Optimization
- **Early Exit**: Added validation for invalid detection dimensions
- **Non-blocking WebSocket**: Used `skip_queue=True` for stats_update to prevent blocking
- **Error Handling**: Better exception handling to prevent crashes

#### Socket.IO Configuration
- **Async Mode**: Configured explicit threading mode for better concurrency
- **Timeout Settings**: Optimized ping timeout and interval for faster connection management
- **Logger Disabled**: Disabled engineio logging to reduce overhead

### 2. **Frontend Optimizations (script.js)**

#### Frame Streaming
- **Lower FPS**: Reduced from 15 FPS to 10 FPS (100ms interval)
- **Frame Skipping**: Added frame skip mechanism to send every 2nd frame
- **Lower JPEG Quality**: Reduced from 0.8 to 0.6 for faster transmission
- **Frame Counting**: Added `willReadFrequently` canvas context hint for optimization

#### Network Optimization
- **Socket.IO Configuration**: Added reconnection options with exponential backoff
- **Skip Queue**: Used `skip_queue=True` for processed frames to prevent blocking

#### Resource Management
- **Efficient State Tracking**: Added frame counter for better control

### 3. **Configuration Adjustments (optional improvements)**

Recommended changes to `config.py`:
```python
# Reduce frame size for faster processing
DEFAULT_FRAME_WIDTH = 640   # was 980
DEFAULT_FRAME_HEIGHT = 480  # was 740

# Reduce webcam resolution if possible
WEBCAM_WIDTH = 1024   # was 1280
WEBCAM_HEIGHT = 576   # was 720
```

---

## Performance Metrics

### Expected Improvements

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Model Inference | CPU ~200ms | GPU ~50ms | **4x faster** |
| JPEG Encoding | 85% quality | 75% quality | **~30% faster** |
| Memory Usage | 100MB buffer | 10MB buffer | **90% less** |
| Frame Rate | 15 FPS | 10 FPS* | Smoother |
| Network Bandwidth | Higher | Lower | **~25% reduction** |

*10 FPS is optimal for fall detection (human falls are slow events)

---

## Tuning Options

### For Maximum Speed (Sacrificing some accuracy)
```python
# In app.py
FRAME_SKIP = 1  # Process every 2nd frame
JPEG_QUALITY = 60  # Lower quality

# In script.js
const FRAME_SKIP = 2;  // Send every 3rd frame
canvasElement.toDataURL('image/jpeg', 0.5)  # Even lower quality
```

### For Better Accuracy (Slightly slower)
```python
# In app.py
FRAME_SKIP = 0  # Process every frame
JPEG_QUALITY = 85  # Higher quality

# In script.js
const FRAME_SKIP = 0;  # Send every frame
canvasElement.toDataURL('image/jpeg', 0.8)  # Higher quality
```

---

## Hardware Requirements

### Recommended Setup
- **GPU**: NVIDIA GPU with CUDA support (RTX 3060 or better for 30+ FPS)
- **CPU**: Intel i7/i9 or AMD Ryzen 7/9 (8+ cores)
- **RAM**: 8GB minimum, 16GB recommended
- **Network**: 100Mbps for multi-client support

### For CPU-Only Setup
If you don't have a GPU:
```python
# In app.py, change:
DEVICE = 'cpu'  # instead of 'cuda'
```
Note: Performance will be slower (~200ms per frame)

---

## Monitoring Performance

### Enable Performance Metrics
Add to your Flask app for monitoring:
```python
import time

frame_times = []

def process_frame(frame):
    start = time.time()
    # ... processing ...
    elapsed = time.time() - start
    frame_times.append(elapsed)
    
    if len(frame_times) > 100:
        avg_time = sum(frame_times) / len(frame_times)
        fps = 1 / avg_time if avg_time > 0 else 0
        print(f"Avg frame time: {avg_time*1000:.1f}ms | FPS: {fps:.1f}")
        frame_times.clear()
```

---

## Troubleshooting

### High Latency / Lag
1. Check GPU utilization: `nvidia-smi` (should be >80%)
2. Reduce frame quality further in script.js
3. Lower the inference resolution in config.py
4. Check network bandwidth with `iperf3`

### High CPU Usage (CPU-only)
1. Reduce `DEFAULT_FRAME_WIDTH` and `DEFAULT_FRAME_HEIGHT`
2. Increase `FRAME_SKIP` value
3. Consider upgrading to GPU

### Memory Issues
1. Ensure `max_http_buffer_size` is set to 10MB
2. Check `MAX_ALERT_HISTORY` is reasonable (~50)
3. Monitor background processes

### WebSocket Disconnections
1. Check network stability
2. Adjust Socket.IO timeout settings
3. Check firewall/proxy settings

---

## Best Practices

1. **Always use GPU** if available - it provides 4-10x speedup
2. **Balance quality and speed** - 10 FPS is sufficient for fall detection
3. **Monitor resource usage** - Watch CPU/GPU/Memory in production
4. **Test with real cameras** - Performance varies by camera
5. **Use RTSP streams** when possible - More efficient than USB cameras

---

## Next Steps

1. Install GPU drivers if available
2. Test performance with: `python app.py`
3. Monitor system resources during operation
4. Adjust parameters based on your hardware
5. Run in production with monitoring

