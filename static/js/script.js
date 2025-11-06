// Initialize Socket.IO
const socket = io({
    reconnection: true,
    reconnectionDelay: 1000,
    reconnectionDelayMax: 5000,
    reconnectionAttempts: 5
});

// DOM Elements
const startBtn = document.getElementById('start-btn');
const stopBtn = document.getElementById('stop-btn');
const sourceType = document.getElementById('source-type');
const sourceInput = document.getElementById('source-input');
const sourceLabel = document.getElementById('source-label');
const clientVideoEl = document.getElementById('client-video');
const serverImgEl = document.getElementById('server-img');
const bboxCanvas = document.getElementById('bbox-canvas');
const videoOverlay = document.getElementById('video-overlay');
const statusBadge = document.getElementById('status-badge');
const personCount = document.getElementById('person-count');
const fallCount = document.getElementById('fall-count');
const currentTime = document.getElementById('current-time');
const alertList = document.getElementById('alert-list');
const clearAlertsBtn = document.getElementById('clear-alerts-btn');
const alertModal = document.getElementById('alert-modal');
const acknowledgeBtn = document.getElementById('acknowledge-btn');
const alertMessage = document.getElementById('alert-message');
const alertTime = document.getElementById('alert-time');

// State
let isRunning = false;
let alertSound = null;
let clientStream = null;
let frameInterval = null;
let captureCanvas = null; // offscreen for sending sampled frames to backend
let frameCount = 0;
const FRAME_SKIP = 1;  // Send every 2nd frame (1 = skip 1, send 1)
let bboxCtx = bboxCanvas.getContext('2d');

function resizeCanvasToMedia() {
    const visibleEl = !clientVideoEl.classList.contains('hidden') ? clientVideoEl : serverImgEl;
    const w = visibleEl.clientWidth || bboxCanvas.clientWidth;
    const h = visibleEl.clientHeight || bboxCanvas.clientHeight;
    bboxCanvas.width = w;
    bboxCanvas.height = h;
}
// Resize canvas when media dimensions become available
clientVideoEl.addEventListener('loadedmetadata', resizeCanvasToMedia);
serverImgEl.addEventListener('load', resizeCanvasToMedia);

// Initialize Particles.js
particlesJS('particles-js', {
    particles: {
        number: { value: 80, density: { enable: true, value_area: 800 } },
        color: { value: '#00f7ff' },
        shape: { type: 'circle' },
        opacity: { value: 0.5, random: true },
        size: { value: 3, random: true },
        line_linked: {
            enable: true,
            distance: 150,
            color: '#00f7ff',
            opacity: 0.2,
            width: 1
        },
        move: {
            enable: true,
            speed: 2,
            direction: 'none',
            random: false,
            straight: false,
            out_mode: 'out',
            bounce: false
        }
    },
    interactivity: {
        detect_on: 'canvas',
        events: {
            onhover: { enable: true, mode: 'grab' },
            onclick: { enable: true, mode: 'push' },
            resize: true
        },
        modes: {
            grab: { distance: 140, line_linked: { opacity: 0.5 } },
            push: { particles_nb: 4 }
        }
    },
    retina_detect: true
});

// Update Clock
function updateClock() {
    const now = new Date();
    const timeString = now.toLocaleTimeString('en-US', { hour12: false });
    currentTime.textContent = timeString;
}
setInterval(updateClock, 1000);
updateClock();

// Source Type Change Handler
sourceType.addEventListener('change', () => {
    const type = sourceType.value;
    switch(type) {
        case 'client_camera':
            sourceLabel.innerHTML = '<i class="fas fa-link"></i> Using your device camera';
            sourceInput.placeholder = 'No input needed';
            sourceInput.value = '';
            sourceInput.disabled = true;
            break;
        case 'webcam':
            sourceLabel.innerHTML = '<i class="fas fa-link"></i> Webcam ID (0, 1, 2...)';
            sourceInput.placeholder = '0';
            sourceInput.value = '0';
            sourceInput.disabled = false;
            break;
        case 'rtsp':
            sourceLabel.innerHTML = '<i class="fas fa-link"></i> RTSP URL';
            sourceInput.placeholder = 'rtsp://username:password@ip:port/stream';
            sourceInput.value = '';
            sourceInput.disabled = false;
            break;
        case 'file':
            sourceLabel.innerHTML = '<i class="fas fa-link"></i> Video File Path';
            sourceInput.placeholder = 'path/to/video.mp4';
            sourceInput.value = '';
            sourceInput.disabled = false;
            break;
    }
});

// Start Detection
startBtn.addEventListener('click', async () => {
    const source = sourceInput.value.trim();
    const type = sourceType.value;
    
    // Validate input for non-client camera sources
    if (type !== 'client_camera' && !source) {
        showNotification('Please enter a valid source', 'error');
        return;
    }
    
    try {
        startBtn.disabled = true;
        startBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Starting...';
        
        // If client camera, request camera access
        if (type === 'client_camera') {
            await startClientCamera();
        }
        
        const response = await fetch('/start_detection', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ source: source || 'client', type })
        });
        
        const data = await response.json();
        
            if (data.status === 'success') {
            isRunning = true;
                // Prepare UI by source type
                if (type === 'client_camera') {
                    // Show local video stream; do NOT fetch processed frames from server
                    serverImgEl.src = '';
                    serverImgEl.classList.add('hidden');
                    clientVideoEl.classList.remove('hidden');
                    resizeCanvasToMedia();
                    // Start sampling frames for backend analysis (reduced rate)
                    startFrameStreaming();
                } else {
                    // For server camera, use MJPEG endpoint in <img>
                    clientVideoEl.classList.add('hidden');
                    serverImgEl.classList.remove('hidden');
                    serverImgEl.src = '/video_feed?' + new Date().getTime();
                    resizeCanvasToMedia();
                }
                videoOverlay.classList.add('hidden');
            
            statusBadge.textContent = 'Active';
            statusBadge.classList.remove('badge-inactive');
            statusBadge.classList.add('badge-active');
            startBtn.disabled = true;
            stopBtn.disabled = false;
            startBtn.innerHTML = '<i class="fas fa-play"></i> Start Detection';
            showNotification('Detection started successfully', 'success');
        } else {
            throw new Error(data.message);
        }
    } catch (error) {
        console.error('Error starting detection:', error);
        showNotification('Failed to start detection: ' + error.message, 'error');
        startBtn.disabled = false;
        startBtn.innerHTML = '<i class="fas fa-play"></i> Start Detection';
        stopClientCamera();
    }
});

// Stop Detection
stopBtn.addEventListener('click', async () => {
    try {
        stopBtn.disabled = true;
        stopBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Stopping...';
        
        const response = await fetch('/stop_detection', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        
        const data = await response.json();
        
        if (data.status === 'success') {
            isRunning = false;
            
            // Stop client camera if active
            stopClientCamera();
            
            // Clear media elements
            serverImgEl.src = '';
            clientVideoEl.srcObject = null;
            clientVideoEl.classList.add('hidden');
            serverImgEl.classList.add('hidden');
            videoOverlay.classList.remove('hidden');
            statusBadge.textContent = 'Inactive';
            statusBadge.classList.remove('badge-active');
            statusBadge.classList.add('badge-inactive');
            startBtn.disabled = false;
            stopBtn.disabled = true;
            stopBtn.innerHTML = '<i class="fas fa-stop"></i> Stop Detection';
            personCount.textContent = '0';
            fallCount.textContent = '0';
            showNotification('Detection stopped', 'info');
        }
    } catch (error) {
        console.error('Error stopping detection:', error);
        showNotification('Failed to stop detection', 'error');
        stopBtn.disabled = false;
        stopBtn.innerHTML = '<i class="fas fa-stop"></i> Stop Detection';
    }
});

// Clear Alerts
clearAlertsBtn.addEventListener('click', async () => {
    try {
        const response = await fetch('/clear_alerts', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        
        const data = await response.json();
        
        if (data.status === 'success') {
            alertList.innerHTML = '<div class="no-alerts"><i class="fas fa-check-circle"></i><p>No alerts yet</p></div>';
            showNotification('Alerts cleared', 'info');
        }
    } catch (error) {
        console.error('Error clearing alerts:', error);
    }
});

// Acknowledge Alert Modal
acknowledgeBtn.addEventListener('click', () => {
    alertModal.classList.remove('show');
    playAlertSound(false);
});

// Socket.IO Event Handlers
socket.on('connect', () => {
    console.log('Connected to server');
});

socket.on('stats_update', (data) => {
    personCount.textContent = data.person_count;
    fallCount.textContent = data.fall_count;
});

socket.on('fall_alert', (alert) => {
    console.log('Fall alert received:', alert);
    addAlertToList(alert);
    showAlertModal(alert);
    playAlertSound(true);
});

// Receive bbox updates from server and render overlays on canvas
socket.on('bbox_update', (payload) => {
    if (!isRunning) return;
    const { detections, frame_size } = payload || {};
    if (!detections || !frame_size) return;

    // Determine scale from model frame size to displayed canvas size
    const sx = bboxCanvas.width / frame_size.width;
    const sy = bboxCanvas.height / frame_size.height;

    // Clear canvas
    bboxCtx.clearRect(0, 0, bboxCanvas.width, bboxCanvas.height);

    detections.forEach(det => {
        const x = Math.round(det.x * sx);
        const y = Math.round(det.y * sy);
        const w = Math.round(det.w * sx);
        const h = Math.round(det.h * sy);
        const fallen = !!det.fallen;

        // Style
        bboxCtx.lineWidth = 3;
        bboxCtx.strokeStyle = fallen ? 'rgba(255,0,0,0.95)' : 'rgba(0,255,0,0.95)';

        // Draw border-only rectangle (no fill)
        bboxCtx.strokeRect(x, y, w, h);

        // Label
        const label = fallen ? 'FALL DETECTED!' : `${det.label} ${det.conf}%`;
        bboxCtx.font = '16px Roboto, sans-serif';
        const textW = bboxCtx.measureText(label).width + 10;
        const textH = 22;
        const tx = x + 2;
        const ty = Math.max(y - textH, 0) + textH - 6;
        bboxCtx.fillStyle = fallen ? 'rgba(255,0,0,0.9)' : 'rgba(0,255,0,0.9)';
        bboxCtx.fillRect(tx - 2, ty - textH + 4, textW, textH);
        bboxCtx.fillStyle = '#000';
        bboxCtx.fillText(label, tx, ty);
    });

    // Fallback: update counts from bbox payload if stats_update isn't received timely
    if (typeof payload.person_count === 'number') personCount.textContent = payload.person_count;
    if (typeof payload.fall_count === 'number') fallCount.textContent = payload.fall_count;
});

// Add Alert to List
function addAlertToList(alert) {
    // Remove "no alerts" message if present
    const noAlerts = alertList.querySelector('.no-alerts');
    if (noAlerts) {
        noAlerts.remove();
    }
    
    const alertItem = document.createElement('div');
    alertItem.className = 'alert-item';
    alertItem.innerHTML = `
        <div class="alert-item-header">
            <div class="alert-item-title">
                <i class="fas fa-exclamation-triangle"></i>
                <span>Fall Detected</span>
            </div>
            <div class="alert-item-time">${alert.time_string}</div>
        </div>
        <div class="alert-item-body">
            ${alert.location}
        </div>
        <div class="alert-item-details">
            Confidence: ${alert.confidence}% | Conditions: ${alert.conditions.join(', ')}
        </div>
    `;
    
    // Add to top of list
    alertList.insertBefore(alertItem, alertList.firstChild);
    
    // Limit alerts in list
    const alerts = alertList.querySelectorAll('.alert-item');
    if (alerts.length > 20) {
        alerts[alerts.length - 1].remove();
    }
}

// Show Alert Modal
function showAlertModal(alert) {
    alertMessage.textContent = `A fall has been detected at ${alert.location}`;
    alertTime.textContent = `Time: ${alert.time_string} | Confidence: ${alert.confidence}%`;
    alertModal.classList.add('show');
}

// Play Alert Sound
function playAlertSound(play) {
    if (play) {
        // Create audio context for alert sound
        if (!alertSound) {
            const AudioContext = window.AudioContext || window.webkitAudioContext;
            const audioContext = new AudioContext();
            
            // Create oscillator for beep sound
            const oscillator = audioContext.createOscillator();
            const gainNode = audioContext.createGain();
            
            oscillator.connect(gainNode);
            gainNode.connect(audioContext.destination);
            
            oscillator.frequency.value = 800;
            oscillator.type = 'sine';
            
            gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
            gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5);
            
            oscillator.start(audioContext.currentTime);
            oscillator.stop(audioContext.currentTime + 0.5);
            
            alertSound = oscillator;
            
            // Play multiple beeps
            setTimeout(() => {
                const oscillator2 = audioContext.createOscillator();
                const gainNode2 = audioContext.createGain();
                oscillator2.connect(gainNode2);
                gainNode2.connect(audioContext.destination);
                oscillator2.frequency.value = 1000;
                oscillator2.type = 'sine';
                gainNode2.gain.setValueAtTime(0.3, audioContext.currentTime);
                gainNode2.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5);
                oscillator2.start(audioContext.currentTime);
                oscillator2.stop(audioContext.currentTime + 0.5);
            }, 600);
        }
    }
}

// Show Notification (simple version)
function showNotification(message, type) {
    console.log(`[${type.toUpperCase()}] ${message}`);
    
    // You can add a toast notification library here if desired
    // For now, we'll use console.log
}

// Load existing alerts on page load
async function loadAlerts() {
    try {
        const response = await fetch('/get_alerts');
        const data = await response.json();
        
        if (data.alerts && data.alerts.length > 0) {
            alertList.innerHTML = '';
            data.alerts.reverse().forEach(alert => {
                addAlertToList(alert);
            });
        }
    } catch (error) {
        console.error('Error loading alerts:', error);
    }
}

// Initialize
loadAlerts();

// Close modal on outside click
alertModal.addEventListener('click', (e) => {
    if (e.target === alertModal) {
        alertModal.classList.remove('show');
        playAlertSound(false);
    }
});

// Client Camera Functions
async function startClientCamera() {
    try {
        // Request camera access with specific constraints
        const constraints = {
            video: {
                width: { ideal: 1280 },
                height: { ideal: 720 },
                facingMode: 'user'
            },
            audio: false
        };
        clientStream = await navigator.mediaDevices.getUserMedia(constraints);
        clientVideoEl.srcObject = clientStream;
        clientVideoEl.classList.remove('hidden');

        // Offscreen canvas for sampling frames to backend
        if (!captureCanvas) captureCanvas = document.createElement('canvas');

        // Ensure overlay canvas matches displayed element
        setTimeout(resizeCanvasToMedia, 100);
        window.addEventListener('resize', resizeCanvasToMedia);

        console.log('Client camera started successfully');
    } catch (error) {
        console.error('Error accessing client camera:', error);
        throw new Error('Could not access camera. Please ensure camera permissions are granted.');
    }
}

function stopClientCamera() {
    // Stop frame streaming
    if (frameInterval) {
        clearInterval(frameInterval);
        frameInterval = null;
    }
    
    // Stop media stream
    if (clientStream) {
        clientStream.getTracks().forEach(track => track.stop());
        clientStream = null;
    }
    // Clean up video element
    clientVideoEl.srcObject = null;
    bboxCtx.clearRect(0, 0, bboxCanvas.width, bboxCanvas.height);
    
    console.log('Client camera stopped');
}

function startFrameStreaming() {
    if (frameInterval) {
        clearInterval(frameInterval);
    }
    
    frameCount = 0;
    // Send sampled frames at ~5 FPS to reduce bandwidth
    frameInterval = setInterval(() => {
        if (clientVideoEl && clientVideoEl.readyState >= 2 && isRunning) {
            frameCount++;
            if (frameCount % (FRAME_SKIP + 1) === 0) {
                captureAndSendFrame();
            }
        }
    }, 200); // 200ms ~ 5 FPS
}

function captureAndSendFrame() {
    try {
        if (!captureCanvas) captureCanvas = document.createElement('canvas');
        // Set canvas size to match video
        captureCanvas.width = clientVideoEl.videoWidth;
        captureCanvas.height = clientVideoEl.videoHeight;

        // Draw current video frame to offscreen canvas
        const ctx = captureCanvas.getContext('2d', { willReadFrequently: true });
        ctx.drawImage(clientVideoEl, 0, 0, captureCanvas.width, captureCanvas.height);

        // Convert canvas to base64 JPEG with lower quality for faster transmission
        const frameData = captureCanvas.toDataURL('image/jpeg', 0.5);

        // Send frame to server via WebSocket (metadata-only response expected)
        socket.emit('frame', frameData);
    } catch (error) {
        console.error('Error capturing frame:', error);
    }
}

// Add play button click handler to start detection
const videoOverlayPlayButton = document.querySelector('#video-overlay i');
if (videoOverlayPlayButton) {
    videoOverlayPlayButton.addEventListener('click', async () => {
        if (!isRunning) {
            startBtn.click(); // Simulate clicking the Start Detection button
        }
    });
}
