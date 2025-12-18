"""
Real-time Fall Detection Inference
Captures webcam frames, extracts pose, and runs through trained model
"""

import cv2
import torch
import numpy as np
import time
from typing import Optional
import argparse
import os

from pose_extractor import PoseExtractor, PoseSequenceBuffer, preprocess_frame
from model import get_model


class FallDetectionInference:
    """
    Real-time fall detection inference system
    """
    
    def __init__(self,
                 model_path: str,
                 sequence_length: int = 30,
                 num_keypoints: int = 17,
                 confidence_threshold: float = 0.7,
                 device: str = 'cuda' if torch.cuda.is_available() else 'cpu',
                 model_type: str = 'lstm'):
        """
        Initialize inference system
        
        Args:
            model_path: Path to trained model checkpoint
            sequence_length: Length of pose sequence (must match training)
            num_keypoints: Number of pose keypoints (default 17 for MediaPipe)
            confidence_threshold: Minimum confidence to trigger fall alert
            device: 'cuda' or 'cpu'
            model_type: 'lstm' or 'gru'
        """
        self.sequence_length = sequence_length
        self.num_keypoints = num_keypoints
        self.confidence_threshold = confidence_threshold
        self.device = device
        
        # Load model
        print(f"Loading model from {model_path}...")
        input_size = num_keypoints * 2
        self.model = get_model(
            model_type=model_type,
            input_size=input_size,
            hidden_size=128,
            num_layers=2,
            dropout=0.3,
            bidirectional=True
        )
        
        # Load checkpoint
        checkpoint = torch.load(model_path, map_location=device)
        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.model.to(device)
        self.model.eval()
        print(f"Model loaded successfully on {device}")
        
        # Initialize pose extractor
        self.pose_extractor = PoseExtractor(
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
            model_complexity=1
        )
        
        # Initialize pose sequence buffer
        self.pose_buffer = PoseSequenceBuffer(sequence_length=sequence_length)
        
        # Fall detection state
        self.fall_detected = False
        self.fall_confidence = 0.0
        self.last_fall_time = 0
        self.fall_cooldown = 2.0  # Seconds before detecting another fall
        
        # Performance tracking
        self.fps = 0
        self.frame_count = 0
        self.start_time = time.time()
    
    def predict(self, sequence: np.ndarray) -> tuple:
        """
        Run inference on a pose sequence
        
        Args:
            sequence: numpy array of shape (sequence_length, num_keypoints * 2)
            
        Returns:
            is_fall: bool, True if fall detected
            confidence: float, confidence score for fall class
        """
        # Convert to tensor and add batch dimension
        sequence_tensor = torch.FloatTensor(sequence).unsqueeze(0).to(self.device)
        
        # Inference
        with torch.no_grad():
            predictions, probabilities = self.model.predict(sequence_tensor)
        
        # Get fall probability (class 1)
        fall_prob = probabilities[0, 1].item()
        is_fall = fall_prob > self.confidence_threshold
        
        return is_fall, fall_prob
    
    def process_frame(self, frame: np.ndarray) -> tuple:
        """
        Process a single frame
        
        Args:
            frame: BGR image frame
            
        Returns:
            processed_frame: Frame with pose and fall detection overlay
            is_fall: bool, True if fall detected
            confidence: float, confidence score
        """
        # Extract and normalize pose
        keypoints = self.pose_extractor.extract_and_normalize(frame)
        
        is_fall = False
        confidence = 0.0
        
        if keypoints is not None:
            # Add to buffer
            self.pose_buffer.add_frame(keypoints)
            
            # If buffer is full, run inference
            if self.pose_buffer.is_full():
                sequence = self.pose_buffer.get_flattened_sequence()
                is_fall, confidence = self.predict(sequence)
                
                # Update fall detection state with cooldown
                current_time = time.time()
                if is_fall and (current_time - self.last_fall_time) > self.fall_cooldown:
                    self.fall_detected = True
                    self.fall_confidence = confidence
                    self.last_fall_time = current_time
                elif not is_fall:
                    self.fall_detected = False
                    self.fall_confidence = 0.0
            
            # Draw pose on frame (convert normalized back for visualization)
            # For simplicity, we'll just draw detection result
        else:
            # No pose detected
            self.pose_buffer.reset()
        
        # Draw overlay
        processed_frame = self.draw_overlay(frame, keypoints, is_fall, confidence)
        
        return processed_frame, is_fall, confidence
    
    def draw_overlay(self, 
                    frame: np.ndarray, 
                    keypoints: Optional[np.ndarray],
                    is_fall: bool, 
                    confidence: float) -> np.ndarray:
        """
        Draw detection overlay on frame
        
        Args:
            frame: BGR image frame
            keypoints: Pose keypoints (normalized)
            is_fall: Whether fall is detected
            confidence: Confidence score
            
        Returns:
            frame_with_overlay: Frame with overlay
        """
        frame_copy = frame.copy()
        h, w = frame.shape[:2]
        
        # Draw pose keypoints if available
        if keypoints is not None:
            # Draw skeleton (simplified - just draw keypoint circles)
            # Note: keypoints are normalized, so we need to denormalize for drawing
            # For simplicity, we'll skip detailed skeleton drawing
            cv2.putText(frame_copy, "Pose Detected", (10, h - 70),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        else:
            cv2.putText(frame_copy, "No Pose Detected", (10, h - 70),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
        
        # Draw buffer status
        buffer_status = f"Buffer: {len(self.pose_buffer)}/{self.sequence_length}"
        cv2.putText(frame_copy, buffer_status, (10, h - 40),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        # Draw FPS
        fps_text = f"FPS: {self.fps:.1f}"
        cv2.putText(frame_copy, fps_text, (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        # Draw fall detection result
        if self.pose_buffer.is_full():
            if self.fall_detected or is_fall:
                # Draw red overlay
                overlay = frame_copy.copy()
                cv2.rectangle(overlay, (0, 0), (w, h), (0, 0, 255), 20)
                frame_copy = cv2.addWeighted(frame_copy, 0.7, overlay, 0.3, 0)
                
                # Draw "FALL DETECTED" text
                text = "FALL DETECTED!"
                text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 2, 3)[0]
                text_x = (w - text_size[0]) // 2
                text_y = (h + text_size[1]) // 2
                
                # Background rectangle for text
                cv2.rectangle(frame_copy, 
                            (text_x - 10, text_y - text_size[1] - 10),
                            (text_x + text_size[0] + 10, text_y + 10),
                            (0, 0, 0), -1)
                
                cv2.putText(frame_copy, text, (text_x, text_y),
                           cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 3)
                
                # Draw confidence
                conf_text = f"Confidence: {confidence:.2%}"
                cv2.putText(frame_copy, conf_text, (text_x, text_y + 40),
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            else:
                # Draw "NORMAL" status
                status_text = f"Status: NORMAL ({confidence:.2%})"
                cv2.putText(frame_copy, status_text, (10, 60),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        return frame_copy
    
    def update_fps(self):
        """Update FPS counter"""
        self.frame_count += 1
        elapsed_time = time.time() - self.start_time
        if elapsed_time > 1.0:
            self.fps = self.frame_count / elapsed_time
            self.frame_count = 0
            self.start_time = time.time()
    
    def run(self, source: int = 0, display_size: tuple = (640, 480)):
        """
        Run real-time inference from webcam
        
        Args:
            source: Camera source (0 for default webcam)
            display_size: (width, height) for display
        """
        print("\n" + "="*60)
        print("FALL DETECTION - REAL-TIME INFERENCE")
        print("="*60)
        print(f"Model: {self.model.__class__.__name__}")
        print(f"Device: {self.device}")
        print(f"Confidence Threshold: {self.confidence_threshold}")
        print(f"Sequence Length: {self.sequence_length} frames")
        print("\nPress 'q' to quit, 's' to take screenshot")
        print("="*60 + "\n")
        
        # Open camera
        cap = cv2.VideoCapture(source)
        if not cap.isOpened():
            print(f"Error: Could not open camera {source}")
            return
        
        # Set camera properties
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, display_size[0])
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, display_size[1])
        
        screenshot_count = 0
        
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    print("Error: Could not read frame")
                    break
                
                # Preprocess frame
                frame = preprocess_frame(frame, target_size=display_size)
                
                # Process frame
                processed_frame, is_fall, confidence = self.process_frame(frame)
                
                # Update FPS
                self.update_fps()
                
                # Display
                cv2.imshow('Fall Detection', processed_frame)
                
                # Handle keyboard input
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    print("\nQuitting...")
                    break
                elif key == ord('s'):
                    # Save screenshot
                    filename = f'screenshot_{screenshot_count:04d}.png'
                    cv2.imwrite(filename, processed_frame)
                    print(f"Screenshot saved: {filename}")
                    screenshot_count += 1
        
        finally:
            # Cleanup
            cap.release()
            cv2.destroyAllWindows()
            self.pose_extractor.close()
            print("Inference stopped")
    
    def process_video(self, video_path: str, output_path: Optional[str] = None):
        """
        Process a video file
        
        Args:
            video_path: Path to input video
            output_path: Path to save output video (optional)
        """
        print(f"\nProcessing video: {video_path}")
        
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            print(f"Error: Could not open video {video_path}")
            return
        
        # Get video properties
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        print(f"Video: {width}x{height} @ {fps}fps, {total_frames} frames")
        
        # Create video writer if output path specified
        writer = None
        if output_path:
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        
        frame_idx = 0
        fall_count = 0
        
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                frame_idx += 1
                
                # Process frame
                processed_frame, is_fall, confidence = self.process_frame(frame)
                
                if is_fall:
                    fall_count += 1
                    print(f"Frame {frame_idx}/{total_frames}: FALL DETECTED (confidence: {confidence:.2%})")
                
                # Write frame
                if writer:
                    writer.write(processed_frame)
                
                # Display progress
                if frame_idx % 30 == 0:
                    progress = (frame_idx / total_frames) * 100
                    print(f"Progress: {progress:.1f}% ({frame_idx}/{total_frames})")
        
        finally:
            cap.release()
            if writer:
                writer.release()
                print(f"Output saved to: {output_path}")
            
            print(f"\nProcessing complete!")
            print(f"Total falls detected: {fall_count}")


def main():
    """
    Main function with command-line interface
    """
    parser = argparse.ArgumentParser(description='Fall Detection Inference')
    parser.add_argument('--model', type=str, default='./checkpoints/best_model.pth',
                       help='Path to trained model checkpoint')
    parser.add_argument('--source', type=int, default=0,
                       help='Camera source (0 for default webcam)')
    parser.add_argument('--video', type=str, default=None,
                       help='Path to input video file (instead of webcam)')
    parser.add_argument('--output', type=str, default=None,
                       help='Path to save output video')
    parser.add_argument('--threshold', type=float, default=0.7,
                       help='Confidence threshold for fall detection')
    parser.add_argument('--model-type', type=str, default='lstm',
                       choices=['lstm', 'gru'], help='Model type')
    parser.add_argument('--device', type=str, default='auto',
                       choices=['auto', 'cuda', 'cpu'], help='Device to use')
    
    args = parser.parse_args()
    
    # Determine device
    if args.device == 'auto':
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
    else:
        device = args.device
    
    # Check if model exists
    if not os.path.exists(args.model):
        print(f"Error: Model not found at {args.model}")
        print("\nPlease train a model first using train.py")
        return
    
    # Initialize inference system
    inference = FallDetectionInference(
        model_path=args.model,
        sequence_length=30,
        num_keypoints=17,
        confidence_threshold=args.threshold,
        device=device,
        model_type=args.model_type
    )
    
    # Run inference
    if args.video:
        # Process video file
        inference.process_video(args.video, args.output)
    else:
        # Run real-time from webcam
        inference.run(source=args.source)


if __name__ == "__main__":
    main()
