"""
MoveNet-based Fall Detection Module
Uses pose estimation to detect falls based on skeleton angles
"""

import numpy as np
import tensorflow as tf
import tensorflow_hub as hub
import cv2

class PoseFallDetector:
    def __init__(self):
        """Initialize MoveNet model"""
        print("Loading MoveNet model...")
        # Load MoveNet Thunder model (more accurate) or Lightning (faster)
        model_url = "https://tfhub.dev/google/movenet/singlepose/thunder/4"
        self.model = hub.load(model_url)
        self.movenet = self.model.signatures['serving_default']
        print("MoveNet model loaded successfully!")
        
        # Keypoint indices for MoveNet
        self.KEYPOINT_DICT = {
            'nose': 0,
            'left_eye': 1,
            'right_eye': 2,
            'left_ear': 3,
            'right_ear': 4,
            'left_shoulder': 5,
            'right_shoulder': 6,
            'left_elbow': 7,
            'right_elbow': 8,
            'left_wrist': 9,
            'right_wrist': 10,
            'left_hip': 11,
            'right_hip': 12,
            'left_knee': 13,
            'right_knee': 14,
            'left_ankle': 15,
            'right_ankle': 16
        }
        
        # Confidence threshold for keypoints
        self.keypoint_threshold = 0.2
        
    def preprocess_frame(self, frame):
        """Preprocess frame for MoveNet"""
        # Resize to 256x256 (MoveNet Thunder input size)
        img = cv2.resize(frame, (256, 256))
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img = tf.cast(img, dtype=tf.int32)
        img = tf.expand_dims(img, axis=0)
        return img
    
    def detect_pose(self, frame):
        """Run MoveNet inference on frame"""
        input_image = self.preprocess_frame(frame)
        outputs = self.movenet(input_image)
        keypoints = outputs['output_0'].numpy()[0][0]
        return keypoints
    
    def calculate_angle(self, point1, point2, point3):
        """
        Calculate angle between three points
        point2 is the vertex of the angle
        Returns angle in degrees
        """
        vector1 = np.array([point1[0] - point2[0], point1[1] - point2[1]])
        vector2 = np.array([point3[0] - point2[0], point3[1] - point2[1]])
        
        # Calculate angle using dot product
        cos_angle = np.dot(vector1, vector2) / (np.linalg.norm(vector1) * np.linalg.norm(vector2) + 1e-6)
        angle = np.arccos(np.clip(cos_angle, -1.0, 1.0))
        return np.degrees(angle)
    
    def get_torso_angle(self, keypoints, frame_height, frame_width):
        """
        Calculate torso angle from vertical
        Returns angle in degrees (0 = vertical, 90 = horizontal)
        """
        # Get shoulder and hip midpoints
        left_shoulder = keypoints[self.KEYPOINT_DICT['left_shoulder']]
        right_shoulder = keypoints[self.KEYPOINT_DICT['right_shoulder']]
        left_hip = keypoints[self.KEYPOINT_DICT['left_hip']]
        right_hip = keypoints[self.KEYPOINT_DICT['right_hip']]
        
        # Check if keypoints are confident enough
        if (left_shoulder[2] < self.keypoint_threshold or 
            right_shoulder[2] < self.keypoint_threshold or
            left_hip[2] < self.keypoint_threshold or 
            right_hip[2] < self.keypoint_threshold):
            return None
        
        # Calculate midpoints
        shoulder_mid = [(left_shoulder[1] + right_shoulder[1]) / 2 * frame_width,
                       (left_shoulder[0] + right_shoulder[0]) / 2 * frame_height]
        hip_mid = [(left_hip[1] + right_hip[1]) / 2 * frame_width,
                  (left_hip[0] + right_hip[0]) / 2 * frame_height]
        
        # Calculate angle from vertical (straight down)
        dx = hip_mid[0] - shoulder_mid[0]
        dy = hip_mid[1] - shoulder_mid[1]
        
        # Angle from vertical
        angle = abs(np.degrees(np.arctan2(abs(dx), abs(dy))))
        
        return angle, shoulder_mid, hip_mid
    
    def check_hip_shoulder_alignment(self, keypoints, frame_height, frame_width):
        """
        Check if hips and shoulders are at similar Y coordinates (lying down)
        Returns alignment score (0-1, higher = more aligned = more likely fallen)
        """
        left_shoulder = keypoints[self.KEYPOINT_DICT['left_shoulder']]
        right_shoulder = keypoints[self.KEYPOINT_DICT['right_shoulder']]
        left_hip = keypoints[self.KEYPOINT_DICT['left_hip']]
        right_hip = keypoints[self.KEYPOINT_DICT['right_hip']]
        
        # Check confidence
        if (left_shoulder[2] < self.keypoint_threshold or 
            right_shoulder[2] < self.keypoint_threshold or
            left_hip[2] < self.keypoint_threshold or 
            right_hip[2] < self.keypoint_threshold):
            return None
        
        # Get Y coordinates (normalized)
        shoulder_y = (left_shoulder[0] + right_shoulder[0]) / 2
        hip_y = (left_hip[0] + right_hip[0]) / 2
        
        # Calculate vertical distance (normalized)
        vertical_distance = abs(shoulder_y - hip_y)
        
        # Convert to alignment score (0 = far apart, 1 = same level)
        alignment_score = 1 - min(vertical_distance * 2, 1.0)  # Scale and clamp
        
        return alignment_score
    
    def detect_fall(self, frame, config):
        """
        Main fall detection logic using pose estimation
        Returns: (is_fallen, detection_data)
        """
        frame_height, frame_width = frame.shape[:2]
        
        # Get pose keypoints
        keypoints = self.detect_pose(frame)
        
        # Calculate torso angle
        torso_result = self.get_torso_angle(keypoints, frame_height, frame_width)
        if torso_result is None:
            return False, {'error': 'Could not detect torso', 'keypoints': keypoints}
        
        torso_angle, shoulder_mid, hip_mid = torso_result
        
        # Check hip-shoulder alignment
        alignment_score = self.check_hip_shoulder_alignment(keypoints, frame_height, frame_width)
        if alignment_score is None:
            alignment_score = 0
        
        # Calculate body height (shoulder to hip distance)
        body_height = np.sqrt((shoulder_mid[0] - hip_mid[0])**2 + 
                             (shoulder_mid[1] - hip_mid[1])**2)
        body_height_ratio = body_height / frame_height
        
        # Get head position (nose or average of eyes)
        nose = keypoints[self.KEYPOINT_DICT['nose']]
        if nose[2] > self.keypoint_threshold:
            head_y = nose[0] * frame_height
        else:
            left_eye = keypoints[self.KEYPOINT_DICT['left_eye']]
            right_eye = keypoints[self.KEYPOINT_DICT['right_eye']]
            head_y = ((left_eye[0] + right_eye[0]) / 2) * frame_height
        
        # Check ground proximity (head close to bottom of frame)
        distance_from_bottom = (frame_height - head_y) / frame_height
        is_near_ground = distance_from_bottom < config.GROUND_PROXIMITY_THRESHOLD
        
        # FALL DETECTION RULES
        # Rule 1: Torso is nearly horizontal (angle > 60°)
        is_horizontal = torso_angle > 60
        
        # Rule 2: Hip and shoulders are aligned (lying flat)
        is_aligned = alignment_score > 0.6
        
        # Rule 3: Body appears compressed (small vertical distance)
        is_compressed = body_height_ratio < 0.3
        
        # Rule 4: Person is in lower portion of frame
        hip_y_normalized = (hip_mid[1] / frame_height)
        is_in_lower_frame = hip_y_normalized > config.LOWER_FRAME_THRESHOLD
        
        # Combine rules
        fall_score = 0
        conditions = []
        
        if is_horizontal:
            fall_score += 2  # Strong indicator
            conditions.append('horizontal_torso')
        
        if is_aligned:
            fall_score += 2  # Strong indicator
            conditions.append('hip_shoulder_aligned')
        
        if is_compressed:
            fall_score += 1
            conditions.append('compressed_body')
        
        if is_near_ground or is_in_lower_frame:
            fall_score += 1
            conditions.append('near_ground')
        
        # Determine if fallen (need score >= 3 for high confidence)
        is_fallen = fall_score >= 3
        
        detection_data = {
            'torso_angle': round(torso_angle, 2),
            'alignment_score': round(alignment_score, 2),
            'body_height_ratio': round(body_height_ratio, 2),
            'distance_from_bottom': round(distance_from_bottom, 2),
            'fall_score': fall_score,
            'is_fallen': is_fallen,
            'conditions': conditions,
            'keypoints': keypoints,
            'shoulder_mid': shoulder_mid,
            'hip_mid': hip_mid
        }
        
        return is_fallen, detection_data
    
    def draw_skeleton(self, frame, keypoints):
        """Draw skeleton on frame"""
        frame_height, frame_width = frame.shape[:2]
        
        # Define skeleton connections
        connections = [
            ('left_shoulder', 'right_shoulder'),
            ('left_shoulder', 'left_elbow'),
            ('left_elbow', 'left_wrist'),
            ('right_shoulder', 'right_elbow'),
            ('right_elbow', 'right_wrist'),
            ('left_shoulder', 'left_hip'),
            ('right_shoulder', 'right_hip'),
            ('left_hip', 'right_hip'),
            ('left_hip', 'left_knee'),
            ('left_knee', 'left_ankle'),
            ('right_hip', 'right_knee'),
            ('right_knee', 'right_ankle'),
        ]
        
        # Draw connections
        for connection in connections:
            start_idx = self.KEYPOINT_DICT[connection[0]]
            end_idx = self.KEYPOINT_DICT[connection[1]]
            
            start_point = keypoints[start_idx]
            end_point = keypoints[end_idx]
            
            if start_point[2] > self.keypoint_threshold and end_point[2] > self.keypoint_threshold:
                start_pos = (int(start_point[1] * frame_width), int(start_point[0] * frame_height))
                end_pos = (int(end_point[1] * frame_width), int(end_point[0] * frame_height))
                cv2.line(frame, start_pos, end_pos, (0, 255, 0), 2)
        
        # Draw keypoints
        for i, keypoint in enumerate(keypoints):
            if keypoint[2] > self.keypoint_threshold:
                y, x, confidence = keypoint
                pos = (int(x * frame_width), int(y * frame_height))
                cv2.circle(frame, pos, 4, (0, 0, 255), -1)
        
        return frame
