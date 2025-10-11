# Fall Detector 2.0

An advanced fall detection system using YOLO object detection and computer vision techniques to identify when a person has fallen.

## Features

- **Multi-Video Support**: Select any video file from your computer for fall detection
- **Advanced Detection Algorithm**: Uses multiple factors for accurate fall detection:
  - Aspect ratio analysis
  - Position-based detection
  - Size-relative detection
  - Camera angle compensation
- **Real-time Processing**: Live video analysis with visual feedback
- **Video Output**: Saves processed video with annotations
- **Debug Information**: Shows detection parameters and ratios

## Requirements

```
ultralytics
cvzone
opencv-python
```

## Installation

1. Clone the repository:
```bash
git clone https://github.com/Sajjadahmeddd/fall_detector_2.0.git
cd fall_detector_2.0
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Run the main script:
```bash
python main.py
```

2. Select a video file when prompted through the file dialog

3. The system will process the video and show:
   - Real-time fall detection
   - Person bounding boxes
   - Aspect ratios and detection parameters
   - "Fall Detected" alerts in red

4. Press 't' to stop processing early

5. The processed video will be automatically saved with timestamp

## How It Works

### Detection Algorithm

The system uses a multi-factor approach to detect falls:

1. **Aspect Ratio**: Detects when width/height > 0.9 (horizontal orientation)
2. **Position Analysis**: Identifies people in lower portions of the frame
3. **Size Analysis**: Considers bounding box size relative to frame
4. **Angle Compensation**: Handles camera angle effects with thin detection boxes

### YOLO Integration

- Uses YOLOv8 for person detection
- Processes each detected person through fall detection algorithm
- Maintains high accuracy while minimizing false positives

## Files

- `main.py`: Main fall detection script
- `requirements.txt`: Python dependencies
- `classes.txt`: YOLO class names
- `yolov8s.pt`: Pre-trained YOLO model weights
- `README.md`: This documentation

## Output

Processed videos are saved with the naming convention:
```
fall_detection_[original_name]_YYYYMMDD_HHMMSS.mp4
```

## Configuration

You can adjust detection sensitivity by modifying these parameters in `main.py`:

- `fall_threshold`: Base aspect ratio threshold (default: 0.9)
- Position thresholds for frame analysis
- Size ratios for detection boxes

## Contributing

Feel free to contribute by:
- Improving detection algorithms
- Adding new features
- Reporting issues
- Submitting test videos

## License

This project is open source and available under the MIT License.