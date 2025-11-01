# Quick Start: Client Camera Mode

## What Changed?

The webapp now supports **Client Camera Mode** - any device accessing the web application can use its own camera for fall detection!

## How to Use

### 1. Start the Server

```bash
python app.py
```

### 2. Access from Any Device

#### Option A: Local Network
- Server device: `http://localhost:8000`
- Other devices: `http://[SERVER-IP]:8000`
  - Find server IP: `ipconfig` (Windows) or `ifconfig` (Linux/Mac)

#### Option B: Dev Tunnel (Remote Access)
```bash
# In VS Code, use Command Palette (Ctrl+Shift+P):
# > "Ports: Forward a Port"
# Then select "Port 8000"
# Choose "Public" visibility
# Copy the generated URL
```

Share the dev tunnel URL with anyone, anywhere!

### 3. Use Client Camera

1. Open the web app in your browser
2. In the **Source Type** dropdown, select **"Client Camera (Your Device)"**
3. Click **"Start Detection"**
4. Allow camera access when prompted
5. Your camera feed will be processed in real-time!

## Features Available in Client Camera Mode

✅ Real-time fall detection on YOUR device's camera  
✅ Works on phones, tablets, laptops - any device with a camera  
✅ No need to configure camera IDs or streams  
✅ Processing happens on the server (your device just sends video)  
✅ All alerts and history work exactly the same  
✅ Perfect for remote monitoring via port forwarding  

## Other Source Types (Still Available)

- **Server Webcam**: Use the camera connected to the server
- **RTSP Stream**: Connect to IP cameras
- **Video File**: Process recorded videos

## Troubleshooting

**Camera not working?**
- Make sure you granted camera permissions
- Use HTTPS (required by browsers) - dev tunnels provide this automatically
- Check if another app is using the camera

**Slow/Laggy video?**
- Check your internet connection
- Try moving closer to the WiFi router
- Close other bandwidth-heavy applications

**Connection issues?**
- Refresh the page and try again
- Check firewall settings
- Ensure the server is running

## Technical Notes

- **Frame Rate**: ~15 FPS (optimized for performance)
- **Resolution**: 1280x720 (automatically adjusted)
- **Latency**: Usually under 200ms on good connections
- **Browser**: Works on Chrome, Firefox, Safari, Edge (desktop & mobile)

## Security

- Camera access requires your explicit permission
- Video is only sent while detection is active
- No recording on server by default
- HTTPS encrypts all communication (when using dev tunnels)

---

For more details, see [CLIENT_CAMERA_GUIDE.md](CLIENT_CAMERA_GUIDE.md)
