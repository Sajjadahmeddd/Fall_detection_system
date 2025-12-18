"""
Pose Extraction Module using MediaPipe Pose
Extracts 2D keypoints from video frames and normalizes them for scale invariance
"""

import cv2
import mediapipe as mp
import numpy as np
from typing import Optional, Tuple, List


class PoseExtractor:
    """
    Extract and normalize human pose keypoints using MediaPipe Pose
    """
    
    def __init__(self, 
                 min_detection_confidence: float = 0.5,
                 min_tracking_confidence: float = 0.5,
                 model_complexity: int = 1):
        """
        Initialize MediaPipe Pose
        
        Args:
            min_detection_confidence: Minimum confidence for person detection
            min_tracking_confidence: Minimum confidence for pose tracking
            model_complexity: 0=Lite, 1=Full, 2=Heavy (more accurate but slower)
        """
        self.mp_pose = mp.solutions.pose
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles
        
        self.pose = self.mp_pose.Pose(
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence,
            model_complexity=model_complexity,
            static_image_mode=False
        )
        
        # MediaPipe provides 33 landmarks
        # We'll use the most important ones for fall detection
        self.keypoint_indices = [
            0,   # nose
            11, 12,  # shoulders
            13, 14,  # elbows
            15, 16,  # wrists
            23, 24,  # hips
            25, 26,  # knees
            27, 28,  # ankles
            29, 30,  # heels
            31, 32   # feet
        ]
        
        self.num_keypoints = len(self.keypoint_indices)
        
    def extract_keypoints(self, frame: np.ndarray) -> Optional[np.ndarray]:
        """
        Extract pose keypoints from a single frame
        
        Args:
            frame: RGB image frame (H, W, 3)
            
        Returns:
            keypoints: numpy array of shape (num_keypoints, 2) containing [x, y] coordinates
                      Returns None if no pose detected
        """
        # Convert BGR to RGB if needed
        if len(frame.shape) == 3 and frame.shape[2] == 3:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        else:
            frame_rgb = frame
        
        # Process the frame
        results = self.pose.process(frame_rgb)
        
        if results.pose_landmarks is None:
            return None
        
        # Extract keypoints
        landmarks = results.pose_landmarks.landmark
        keypoints = []
        
        for idx in self.keypoint_indices:
            landmark = landmarks[idx]
            # Use x, y coordinates (ignore z and visibility for now)
            keypoints.append([landmark.x, landmark.y])
        
        return np.array(keypoints, dtype=np.float32)
    
    def normalize_keypoints(self, keypoints: np.ndarray) -> np.ndarray:
        """
        Normalize keypoints relative to hip center for scale invariance
        
        Args:
            keypoints: numpy array of shape (num_keypoints, 2)
            
        Returns:
            normalized_keypoints: numpy array of same shape, normalized
        """
        if keypoints is None or len(keypoints) == 0:
            return keypoints
        
        # Hip center is average of left hip (index 6) and right hip (index 7)
        # In our keypoint_indices, hips are at indices 6, 7
        left_hip_idx = 6
        right_hip_idx = 7
        
        hip_center = (keypoints[left_hip_idx] + keypoints[right_hip_idx]) / 2.0
        
        # Translate keypoints to center at hip
        centered_keypoints = keypoints - hip_center
        
        # Calculate scale based on torso height (shoulder to hip distance)
        # Shoulders are at indices 1, 2
        left_shoulder = keypoints[1]
        right_shoulder = keypoints[2]
        shoulder_center = (left_shoulder + right_shoulder) / 2.0
        
        torso_height = np.linalg.norm(shoulder_center - hip_center)
        
        # Avoid division by zero
        if torso_height < 1e-6:
            torso_height = 1.0
        
        # Scale normalize
        normalized_keypoints = centered_keypoints / torso_height
        
        return normalized_keypoints
    
    def extract_and_normalize(self, frame: np.ndarray) -> Optional[np.ndarray]:
        """
        Extract and normalize keypoints in one step
        
        Args:
            frame: BGR image frame
            
        Returns:
            normalized_keypoints: (num_keypoints, 2) or None if no pose detected
        """
        keypoints = self.extract_keypoints(frame)
        
        if keypoints is None:
            return None
        
        normalized = self.normalize_keypoints(keypoints)
        return normalized
    
    def draw_pose(self, frame: np.ndarray, keypoints: np.ndarray, 
                  normalized: bool = False) -> np.ndarray:
        """
        Draw pose keypoints on frame for visualization
        
        Args:
            frame: BGR image frame
            keypoints: (num_keypoints, 2) array of keypoints
            normalized: whether keypoints are normalized (needs de-normalization)
            
        Returns:
            frame_with_pose: frame with pose drawn
        """
        if keypoints is None:
            return frame
        
        frame_copy = frame.copy()
        h, w = frame.shape[:2]
        
        # If normalized, we can't directly draw (would need original reference)
        # So we just draw the raw keypoints
        if not normalized:
            # Draw connections
            connections = [
                (1, 2),   # shoulders
                (1, 3), (3, 5),  # left arm
                (2, 4), (4, 6),  # right arm
                (1, 6), (2, 7),  # shoulders to hips
                (6, 7),   # hips
                (6, 8), (8, 10), (10, 12), (12, 14),  # left leg
                (7, 9), (9, 11), (11, 13), (13, 15),  # right leg
            ]
            
            # Draw keypoints
            for i, (x, y) in enumerate(keypoints):
                px, py = int(x * w), int(y * h)
                cv2.circle(frame_copy, (px, py), 5, (0, 255, 0), -1)
                
            # Draw connections
            for start_idx, end_idx in connections:
                if start_idx < len(keypoints) and end_idx < len(keypoints):
                    start_point = (int(keypoints[start_idx][0] * w), 
                                 int(keypoints[start_idx][1] * h))
                    end_point = (int(keypoints[end_idx][0] * w), 
                               int(keypoints[end_idx][1] * h))
                    cv2.line(frame_copy, start_point, end_point, (255, 0, 0), 2)
        
        return frame_copy
    
    def flatten_keypoints(self, keypoints: np.ndarray) -> np.ndarray:
        """
        Flatten keypoints from (num_keypoints, 2) to (num_keypoints * 2,)
        
        Args:
            keypoints: (num_keypoints, 2) array
            
        Returns:
            flattened: (num_keypoints * 2,) array
        """
        return keypoints.flatten()
    
    def close(self):
        """Release MediaPipe resources"""
        self.pose.close()


class PoseSequenceBuffer:
    """
    Maintains a sliding window buffer of pose sequences
    """
    
    def __init__(self, sequence_length: int = 30):
        """
        Initialize sequence buffer
        
        Args:
            sequence_length: Number of frames to keep in buffer (e.g., 30 frames at 30fps = 1 second)
        """
        self.sequence_length = sequence_length
        self.buffer = []
        
    def add_frame(self, keypoints: Optional[np.ndarray]) -> bool:
        """
        Add a frame's keypoints to the buffer
        
        Args:
            keypoints: (num_keypoints, 2) array or None
            
        Returns:
            is_full: True if buffer has reached sequence_length
        """
        if keypoints is None:
            # If no pose detected, pad with zeros
            keypoints = np.zeros((17, 2), dtype=np.float32)
        
        self.buffer.append(keypoints)
        
        # Maintain sliding window
        if len(self.buffer) > self.sequence_length:
            self.buffer.pop(0)
        
        return len(self.buffer) == self.sequence_length
    
    def get_sequence(self) -> np.ndarray:
        """
        Get the current sequence as a numpy array
        
        Returns:
            sequence: (sequence_length, num_keypoints, 2)
        """
        return np.array(self.buffer, dtype=np.float32)
    
    def get_flattened_sequence(self) -> np.ndarray:
        """
        Get the current sequence flattened for model input
        
        Returns:
            sequence: (sequence_length, num_keypoints * 2)
        """
        sequence = self.get_sequence()
        batch_size, num_kp, coords = sequence.shape
        return sequence.reshape(batch_size, num_kp * coords)
    
    def reset(self):
        """Clear the buffer"""
        self.buffer = []
    
    def is_full(self) -> bool:
        """Check if buffer is full"""
        return len(self.buffer) == self.sequence_length
    
    def __len__(self) -> int:
        return len(self.buffer)


# Utility functions
def preprocess_frame(frame: np.ndarray, target_size: Tuple[int, int] = (640, 480)) -> np.ndarray:
    """
    Preprocess frame for consistent pose extraction
    
    Args:
        frame: input frame
        target_size: (width, height)
        
    Returns:
        preprocessed frame
    """
    frame = cv2.resize(frame, target_size)
    return frame


if __name__ == "__main__":
    """
    Test pose extraction with webcam
    """
    print("Testing Pose Extractor...")
    
    extractor = PoseExtractor()
    buffer = PoseSequenceBuffer(sequence_length=30)
    
    cap = cv2.VideoCapture(0)
    
    print("Press 'q' to quit, 's' to save current sequence")
    
    frame_count = 0
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        frame = preprocess_frame(frame)
        
        # Extract and normalize keypoints
        keypoints = extractor.extract_and_normalize(frame)
        
        # Add to buffer
        if keypoints is not None:
            is_full = buffer.add_frame(keypoints)
            
            # Draw pose
            frame_with_pose = extractor.draw_pose(frame, keypoints, normalized=False)
            
            # Show buffer status
            cv2.putText(frame_with_pose, 
                       f"Buffer: {len(buffer)}/{buffer.sequence_length}", 
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            if is_full:
                cv2.putText(frame_with_pose, "READY FOR INFERENCE", 
                           (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        else:
            frame_with_pose = frame.copy()
            cv2.putText(frame_with_pose, "No pose detected", 
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        
        cv2.imshow('Pose Extraction Test', frame_with_pose)
        
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('s') and buffer.is_full():
            # Save sequence
            sequence = buffer.get_flattened_sequence()
            np.save(f'test_sequence_{frame_count}.npy', sequence)
            print(f"Saved sequence with shape: {sequence.shape}")
            frame_count += 1
    
    cap.release()
    cv2.destroyAllWindows()
    extractor.close()
    print("Test complete!")
