"""
Complete Usage Examples for Pose-Based Fall Detection System

This file contains practical examples for all major use cases.
"""

# ============================================================================
# Example 1: Basic Training and Inference
# ============================================================================

def example_1_basic_workflow():
    """
    Simplest workflow: Train on synthetic data and run inference
    """
    print("Example 1: Basic Workflow\n")
    print("Step 1: Train model")
    print("  Command: python train.py")
    print("  Output: ./checkpoints/best_model.pth")
    print()
    print("Step 2: Run inference")
    print("  Command: python inference.py")
    print("  Result: Real-time fall detection from webcam")
    print()


# ============================================================================
# Example 2: Custom Data Collection and Training
# ============================================================================

def example_2_custom_training():
    """
    Collect your own data and train a custom model
    """
    print("Example 2: Custom Data Training\n")
    
    # Step 1: Create dataset structure
    print("Step 1: Create dataset structure")
    print("""
    import os
    
    data_dir = './data/my_fall_dataset'
    os.makedirs(f'{data_dir}/fall', exist_ok=True)
    os.makedirs(f'{data_dir}/no_fall', exist_ok=True)
    """)
    
    # Step 2: Record fall sequences
    print("\nStep 2: Record fall sequences")
    print("""
    # Run pose extractor
    python pose_extractor.py
    
    # In the UI:
    # - Simulate falls
    # - Press 's' to save each sequence
    # - Move saved files to data/my_fall_dataset/fall/
    """)
    
    # Step 3: Record normal activity
    print("\nStep 3: Record normal activity")
    print("""
    # Continue with pose extractor
    # - Walk, sit, stand, etc.
    # - Press 's' to save sequences
    # - Move saved files to data/my_fall_dataset/no_fall/
    """)
    
    # Step 4: Modify training script
    print("\nStep 4: Modify train.py")
    print("""
    # Edit train.py, line ~370:
    DATA_DIR = './data/my_fall_dataset'  # Change this line
    
    # Then run:
    python train.py
    """)
    print()


# ============================================================================
# Example 3: Programmatic Usage (Python API)
# ============================================================================

def example_3_programmatic_usage():
    """
    Use the system as a Python library in your own code
    """
    print("Example 3: Programmatic Usage\n")
    
    code = '''
import cv2
import torch
import numpy as np
from pose_extractor import PoseExtractor, PoseSequenceBuffer
from model import get_model

# Initialize components
print("Loading model...")
pose_extractor = PoseExtractor(
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5,
    model_complexity=1
)

pose_buffer = PoseSequenceBuffer(sequence_length=30)

model = get_model('lstm', input_size=34)
checkpoint = torch.load('./checkpoints/best_model.pth', map_location='cpu')
model.load_state_dict(checkpoint['model_state_dict'])
model.eval()

print("Model loaded. Starting detection...")

# Open webcam
cap = cv2.VideoCapture(0)

try:
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Extract and normalize pose
        keypoints = pose_extractor.extract_and_normalize(frame)
        
        if keypoints is not None:
            # Add to buffer
            pose_buffer.add_frame(keypoints)
            
            # Run inference when buffer is full
            if pose_buffer.is_full():
                sequence = pose_buffer.get_flattened_sequence()
                sequence_tensor = torch.FloatTensor(sequence).unsqueeze(0)
                
                with torch.no_grad():
                    output = model(sequence_tensor)
                    probabilities = torch.softmax(output, dim=1)
                    fall_prob = probabilities[0, 1].item()
                
                # Check if fall detected
                if fall_prob > 0.7:
                    print(f"⚠️ FALL DETECTED! Confidence: {fall_prob:.2%}")
                    # Add your custom logic here (send alert, save frame, etc.)
                
                # Display on frame
                status = f"Fall Risk: {fall_prob:.1%}"
                color = (0, 0, 255) if fall_prob > 0.7 else (0, 255, 0)
                cv2.putText(frame, status, (10, 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
        
        cv2.imshow('Fall Detection', frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

finally:
    cap.release()
    cv2.destroyAllWindows()
    pose_extractor.close()
    '''
    
    print(code)
    print()


# ============================================================================
# Example 4: Batch Processing Videos
# ============================================================================

def example_4_batch_processing():
    """
    Process multiple videos in batch
    """
    print("Example 4: Batch Video Processing\n")
    
    code = '''
import os
from inference import FallDetectionInference

# Initialize inference system
inference = FallDetectionInference(
    model_path='./checkpoints/best_model.pth',
    sequence_length=30,
    confidence_threshold=0.7,
    device='cuda'  # or 'cpu'
)

# Process multiple videos
video_dir = './videos'
output_dir = './processed_videos'
os.makedirs(output_dir, exist_ok=True)

video_files = [f for f in os.listdir(video_dir) if f.endswith('.mp4')]

for video_file in video_files:
    print(f"\\nProcessing: {video_file}")
    
    input_path = os.path.join(video_dir, video_file)
    output_path = os.path.join(output_dir, f'processed_{video_file}')
    
    inference.process_video(input_path, output_path)
    
    print(f"Saved to: {output_path}")

print("\\nAll videos processed!")
    '''
    
    print(code)
    print()


# ============================================================================
# Example 5: Integration with Alert System
# ============================================================================

def example_5_alert_integration():
    """
    Integrate with an alert system (email, SMS, database)
    """
    print("Example 5: Alert System Integration\n")
    
    code = '''
import cv2
import torch
import time
from datetime import datetime
from pose_extractor import PoseExtractor, PoseSequenceBuffer
from model import get_model

# Your custom alert function
def send_alert(fall_confidence, frame_image):
    """
    Send alert via your preferred method
    
    Examples:
    - Send email
    - Send SMS via Twilio
    - Save to database
    - Trigger alarm
    - Send notification to mobile app
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Example: Save frame
    filename = f"fall_detected_{timestamp.replace(':', '-')}.jpg"
    cv2.imwrite(f"alerts/{filename}", frame_image)
    
    # Example: Print alert (replace with your alert logic)
    print(f"\\n{'='*50}")
    print(f"⚠️ FALL ALERT at {timestamp}")
    print(f"Confidence: {fall_confidence:.2%}")
    print(f"Frame saved: {filename}")
    print(f"{'='*50}\\n")
    
    # Add your alert code here:
    # - send_email(recipient, subject, body, attachment=filename)
    # - send_sms(phone_number, message)
    # - save_to_database(timestamp, confidence, filename)
    # - trigger_alarm()


# Initialize
pose_extractor = PoseExtractor()
pose_buffer = PoseSequenceBuffer(30)
model = get_model('lstm', input_size=34)
checkpoint = torch.load('./checkpoints/best_model.pth')
model.load_state_dict(checkpoint['model_state_dict'])
model.eval()

cap = cv2.VideoCapture(0)
last_alert_time = 0
alert_cooldown = 5  # seconds

try:
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        keypoints = pose_extractor.extract_and_normalize(frame)
        
        if keypoints is not None:
            pose_buffer.add_frame(keypoints)
            
            if pose_buffer.is_full():
                sequence = torch.FloatTensor(
                    pose_buffer.get_flattened_sequence()
                ).unsqueeze(0)
                
                with torch.no_grad():
                    output = model(sequence)
                    fall_prob = torch.softmax(output, dim=1)[0, 1].item()
                
                # Check for fall with cooldown
                current_time = time.time()
                if (fall_prob > 0.7 and 
                    current_time - last_alert_time > alert_cooldown):
                    
                    send_alert(fall_prob, frame)
                    last_alert_time = current_time
        
        cv2.imshow('Fall Detection', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

finally:
    cap.release()
    cv2.destroyAllWindows()
    pose_extractor.close()
    '''
    
    print(code)
    print()


# ============================================================================
# Example 6: Multi-Camera System
# ============================================================================

def example_6_multi_camera():
    """
    Monitor multiple cameras simultaneously
    """
    print("Example 6: Multi-Camera System\n")
    
    code = '''
import cv2
import torch
import threading
from queue import Queue
from pose_extractor import PoseExtractor, PoseSequenceBuffer
from model import get_model

class CameraMonitor:
    """Monitor a single camera"""
    
    def __init__(self, camera_id, model, alert_queue):
        self.camera_id = camera_id
        self.model = model
        self.alert_queue = alert_queue
        self.pose_extractor = PoseExtractor()
        self.pose_buffer = PoseSequenceBuffer(30)
        self.running = False
    
    def start(self):
        self.running = True
        thread = threading.Thread(target=self._monitor)
        thread.start()
        return thread
    
    def _monitor(self):
        cap = cv2.VideoCapture(self.camera_id)
        
        while self.running:
            ret, frame = cap.read()
            if not ret:
                continue
            
            keypoints = self.pose_extractor.extract_and_normalize(frame)
            
            if keypoints is not None:
                self.pose_buffer.add_frame(keypoints)
                
                if self.pose_buffer.is_full():
                    sequence = torch.FloatTensor(
                        self.pose_buffer.get_flattened_sequence()
                    ).unsqueeze(0)
                    
                    with torch.no_grad():
                        output = self.model(sequence)
                        fall_prob = torch.softmax(output, dim=1)[0, 1].item()
                    
                    if fall_prob > 0.7:
                        alert = {
                            'camera_id': self.camera_id,
                            'confidence': fall_prob,
                            'frame': frame.copy()
                        }
                        self.alert_queue.put(alert)
        
        cap.release()
        self.pose_extractor.close()
    
    def stop(self):
        self.running = False


# Initialize shared model
model = get_model('lstm', input_size=34)
checkpoint = torch.load('./checkpoints/best_model.pth')
model.load_state_dict(checkpoint['model_state_dict'])
model.eval()
model.share_memory()  # Share model across threads

# Alert queue
alert_queue = Queue()

# Start monitoring multiple cameras
camera_ids = [0, 1, 2]  # Adjust based on your setup
monitors = []
threads = []

for cam_id in camera_ids:
    monitor = CameraMonitor(cam_id, model, alert_queue)
    thread = monitor.start()
    monitors.append(monitor)
    threads.append(thread)
    print(f"Started monitoring camera {cam_id}")

# Alert handler
try:
    while True:
        if not alert_queue.empty():
            alert = alert_queue.get()
            print(f"\\n⚠️ FALL DETECTED on Camera {alert['camera_id']}")
            print(f"Confidence: {alert['confidence']:.2%}")
            
            # Save frame
            filename = f"cam{alert['camera_id']}_fall.jpg"
            cv2.imwrite(filename, alert['frame'])
            print(f"Frame saved: {filename}")

except KeyboardInterrupt:
    print("\\nStopping all monitors...")
    for monitor in monitors:
        monitor.stop()
    
    for thread in threads:
        thread.join()
    
    print("All monitors stopped")
    '''
    
    print(code)
    print()


# ============================================================================
# Example 7: Performance Optimization
# ============================================================================

def example_7_optimization():
    """
    Optimize for different scenarios
    """
    print("Example 7: Performance Optimization\n")
    
    print("Scenario 1: Maximum Speed (Real-time on CPU)\n")
    print("""
# In config.py:
POSE_MODEL_COMPLEXITY = 0  # Use Lite model
POSE_SEQUENCE_LENGTH = 20  # Shorter sequence
MODEL_TYPE = 'gru'  # GRU is faster than LSTM

# In model creation:
model = get_model('gru', input_size=34, hidden_size=64, num_layers=1)
    """)
    
    print("\nScenario 2: Maximum Accuracy\n")
    print("""
# In config.py:
POSE_MODEL_COMPLEXITY = 2  # Use Heavy model
POSE_SEQUENCE_LENGTH = 40  # Longer context
POSE_CONFIDENCE_THRESHOLD = 0.8  # Higher threshold

# In model creation:
model = get_model('lstm', input_size=34, hidden_size=256, num_layers=3)

# Train longer:
NUM_EPOCHS = 100
BATCH_SIZE = 8  # Smaller batches for better gradients
    """)
    
    print("\nScenario 3: Balanced (Recommended)\n")
    print("""
# Use default settings in config.py
POSE_MODEL_COMPLEXITY = 1
POSE_SEQUENCE_LENGTH = 30
POSE_CONFIDENCE_THRESHOLD = 0.7

# Default model:
model = get_model('lstm', input_size=34, hidden_size=128, num_layers=2)
    """)
    print()


# ============================================================================
# Run all examples
# ============================================================================

def main():
    print("="*70)
    print("POSE-BASED FALL DETECTION - USAGE EXAMPLES")
    print("="*70)
    print()
    
    examples = [
        ("Basic Training and Inference", example_1_basic_workflow),
        ("Custom Data Collection", example_2_custom_training),
        ("Programmatic Usage", example_3_programmatic_usage),
        ("Batch Video Processing", example_4_batch_processing),
        ("Alert System Integration", example_5_alert_integration),
        ("Multi-Camera System", example_6_multi_camera),
        ("Performance Optimization", example_7_optimization),
    ]
    
    for i, (title, func) in enumerate(examples, 1):
        print(f"\n{'='*70}")
        print(f"EXAMPLE {i}: {title}")
        print(f"{'='*70}\n")
        func()
        input("Press Enter to continue to next example...")
    
    print("\n" + "="*70)
    print("All examples shown!")
    print("="*70)
    print("\nFor more information, see:")
    print("  - README_POSE_DETECTION.md (full documentation)")
    print("  - POSE_QUICK_START.md (quick start guide)")
    print("  - Individual .py files (inline comments)")
    print()


if __name__ == "__main__":
    main()
