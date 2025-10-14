// Initialize Socket.IO
const socket = io();

// DOM Elements
const startBtn = document.getElementById('start-btn');
const stopBtn = document.getElementById('stop-btn');
const sourceType = document.getElementById('source-type');
const sourceInput = document.getElementById('source-input');
const sourceLabel = document.getElementById('source-label');
const videoFeed = document.getElementById('video-feed');
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
        case 'webcam':
            sourceLabel.innerHTML = '<i class="fas fa-link"></i> Webcam ID (0, 1, 2...)';
            sourceInput.placeholder = '0';
            sourceInput.value = '0';
            break;
        case 'rtsp':
            sourceLabel.innerHTML = '<i class="fas fa-link"></i> RTSP URL';
            sourceInput.placeholder = 'rtsp://username:password@ip:port/stream';
            sourceInput.value = '';
            break;
        case 'file':
            sourceLabel.innerHTML = '<i class="fas fa-link"></i> Video File Path';
            sourceInput.placeholder = 'path/to/video.mp4';
            sourceInput.value = '';
            break;
    }
});

// Start Detection
startBtn.addEventListener('click', async () => {
    const source = sourceInput.value.trim();
    const type = sourceType.value;
    
    if (!source) {
        showNotification('Please enter a valid source', 'error');
        return;
    }
    
    try {
        startBtn.disabled = true;
        startBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Starting...';
        
        const response = await fetch('/start_detection', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ source, type })
        });
        
        const data = await response.json();
        
        if (data.status === 'success') {
            isRunning = true;
            videoFeed.src = '/video_feed?' + new Date().getTime();
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
            videoFeed.src = '';
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
