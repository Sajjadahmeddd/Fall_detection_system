# Pose-Based Fall Detection System

A highly accurate fall detection system using **MediaPipe Pose** for human pose estimation and **LSTM/GRU** neural networks for temporal fall pattern recognition.

## System Overview

This system uses computer vision and deep learning to detect falls in real-time:

1. **Pose Extraction**: MediaPipe extracts 17 body keypoints (x, y coordinates) from each frame
2. **Normalization**: Keypoints are normalized relative to hip center for scale invariance
3. **Temporal Modeling**: LSTM processes sequences of 30 frames to detect fall patterns
4. **Classification**: Binary classification (FALL vs NO_FALL) with confidence scores

## Architecture

```
Video Frame → MediaPipe Pose → Keypoint Extraction → Normalization
                                                          ↓
                                                  Sliding Window (30 frames)
                                                          ↓
                                                   LSTM Model
                                                          ↓
                                              Fall Detection (0/1 + confidence)
```

## Files Structure

```
fall_detector_2.0/
├── pose_extractor.py      # MediaPipe pose extraction and normalization
├── model.py               # LSTM/GRU model definitions
├── dataset_loader.py      # Dataset loading and preprocessing
├── train.py               # Training script
├── inference.py           # Real-time inference
├── config.py              # Configuration settings
├── requirements.txt       # Python dependencies
├── checkpoints/           # Saved model checkpoints (created after training)
└── data/                  # Training data (create this)
    ├── fall/              # Fall sequences (.npy files)
    └── no_fall/           # No-fall sequences (.npy files)
```

## Installation

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

**Key Dependencies:**
- `mediapipe>=0.10.0` - Pose estimation
- `torch>=2.0.0` - Deep learning framework
- `opencv-python>=4.8.0` - Video processing
- `scikit-learn>=1.3.0` - ML utilities
- `matplotlib>=3.7.0` - Visualization
- `seaborn>=0.12.0` - Statistical plots

### 2. Verify Installation

Test pose extraction:
```bash
python pose_extractor.py
```
Press 'q' to quit, 's' to save pose sequences.

## Usage

### Quick Start with Synthetic Data

Train on synthetic data for testing:

```bash
# Train model (creates synthetic dataset automatically)
python train.py

# Run inference
python inference.py --model ./checkpoints/best_model.pth
```

### Training with Real Data

#### Step 1: Collect Training Data

Create your dataset directory:
```bash
mkdir -p data/my_fall_dataset/fall
mkdir -p data/my_fall_dataset/no_fall
```

#### Step 2: Record Pose Sequences

Use the pose extractor to capture sequences:

```bash
python pose_extractor.py
```

- Press 's' to save current 30-frame sequence
- Record fall sequences and save to `data/my_fall_dataset/fall/`
- Record normal activity and save to `data/my_fall_dataset/no_fall/`

**Tips for good training data:**
- Record at least 100 samples per class
- Include various lighting conditions
- Include different fall types (forward, backward, sideways)
- Include various normal activities (walking, sitting, standing)

#### Step 3: Train the Model

```bash
python train.py
```

**Training Output:**
- Checkpoints saved to `./checkpoints/`
- Training curves: `training_curves.png`
- Confusion matrix: `confusion_matrix.png`
- History log: `training_history.json`

**Key Training Parameters (edit in train.py):**
- `SEQUENCE_LENGTH = 30` (number of frames)
- `BATCH_SIZE = 16`
- `NUM_EPOCHS = 50`
- `LEARNING_RATE = 0.001`
- `MODEL_TYPE = 'lstm'` (or 'gru')

### Real-Time Inference

#### From Webcam

```bash
python inference.py --model ./checkpoints/best_model.pth --source 0
```

#### From Video File

```bash
python inference.py --model ./checkpoints/best_model.pth \
                   --video path/to/video.mp4 \
                   --output output_video.mp4
```

#### Command-Line Options

```bash
python inference.py --help

Options:
  --model         Path to trained model checkpoint (default: ./checkpoints/best_model.pth)
  --source        Camera source index (default: 0)
  --video         Path to input video file
  --output        Path to save output video
  --threshold     Confidence threshold for fall detection (default: 0.7)
  --model-type    Model type: 'lstm' or 'gru' (default: lstm)
  --device        Device: 'auto', 'cuda', or 'cpu' (default: auto)
```

**Keyboard Controls During Inference:**
- `q` - Quit
- `s` - Save screenshot

### Advanced Configuration

Edit `config.py` for pose-based settings:

```python
# Pose Detection
POSE_MIN_DETECTION_CONFIDENCE = 0.5
POSE_MIN_TRACKING_CONFIDENCE = 0.5
POSE_MODEL_COMPLEXITY = 1  # 0=fast, 1=balanced, 2=accurate

# Temporal Model
POSE_SEQUENCE_LENGTH = 30  # frames in sliding window
POSE_CONFIDENCE_THRESHOLD = 0.7  # fall detection threshold
POSE_FALL_COOLDOWN = 2.0  # seconds between detections

# Model Architecture
POSE_HIDDEN_SIZE = 128
POSE_NUM_LAYERS = 2
POSE_DROPOUT = 0.3
POSE_BIDIRECTIONAL = True
```

## Model Architecture

### LSTM Model

```
Input: (batch_size, 30, 34)  # 30 frames, 17 keypoints * 2 coords
    ↓
Bidirectional LSTM (128 hidden units, 2 layers)
    ↓
Dropout (0.3)
    ↓
Fully Connected (256 → 64)
    ↓
Batch Normalization + ReLU + Dropout
    ↓
Fully Connected (64 → 32)
    ↓
Batch Normalization + ReLU + Dropout
    ↓
Fully Connected (32 → 2)  # NO_FALL, FALL
    ↓
Softmax → Probabilities
```

**Model Size:** ~300K trainable parameters

### GRU Model (Alternative)

Similar architecture but using GRU layers instead of LSTM:
- Faster inference
- Slightly fewer parameters
- Comparable accuracy

## Performance Metrics

The training script reports:
- **Accuracy**: Overall correctness
- **Precision**: Fall predictions that are correct
- **Recall**: Actual falls that are detected
- **F1 Score**: Harmonic mean of precision and recall

**Example Output:**
```
Test Results:
  Accuracy:  0.9250
  Precision: 0.9100
  Recall:    0.9400
  F1 Score:  0.9247

Confusion Matrix:
  True Negatives:  92
  False Positives: 8
  False Negatives: 6
  True Positives:  94
```

## Data Format

Pose sequences are saved as NumPy arrays:

**Shape:** `(sequence_length, num_features)`
- `sequence_length`: 30 frames (1 second at 30fps)
- `num_features`: 34 (17 keypoints × 2 coordinates)

**Keypoints (MediaPipe Pose):**
```python
0: nose
1-2: left/right shoulders
3-4: left/right elbows
5-6: left/right wrists
7-8: left/right hips
9-10: left/right knees
11-12: left/right ankles
13-14: left/right heels
15-16: left/right feet
```

**Example:**
```python
import numpy as np

# Load a sequence
sequence = np.load('fall_sequence_001.npy')
print(sequence.shape)  # (30, 34)

# Access frame 0, keypoint 0 (nose)
x, y = sequence[0, 0:2]
```

## Troubleshooting

### No Pose Detected
- Ensure good lighting
- Person should be fully visible in frame
- Adjust `POSE_MIN_DETECTION_CONFIDENCE` in config.py

### Low Accuracy
- Collect more training data (aim for 200+ samples per class)
- Balance dataset (equal fall and no-fall samples)
- Increase `NUM_EPOCHS` in train.py
- Try data augmentation

### False Positives
- Increase `POSE_CONFIDENCE_THRESHOLD` (e.g., 0.8 or 0.9)
- Collect more diverse no-fall training data
- Add fall cooldown: `POSE_FALL_COOLDOWN = 3.0`

### Slow Inference
- Use `POSE_MODEL_COMPLEXITY = 0` (Lite model)
- Reduce `POSE_SEQUENCE_LENGTH` to 20
- Use GRU instead of LSTM: `MODEL_TYPE = 'gru'`
- Use GPU if available

### CUDA Out of Memory
- Reduce `BATCH_SIZE` in train.py
- Reduce `POSE_HIDDEN_SIZE` or `POSE_NUM_LAYERS`
- Use CPU: `--device cpu`

## Tips for Best Results

### Data Collection
1. **Variety**: Collect falls from different angles and positions
2. **Balance**: Equal number of fall and no-fall samples
3. **Quality**: Ensure pose is always visible
4. **Realism**: Include realistic fall scenarios

### Training
1. **Monitor metrics**: Watch for overfitting (val loss increases)
2. **Early stopping**: Training stops if no improvement for 10 epochs
3. **Learning rate**: Automatically adjusted by scheduler
4. **Checkpointing**: Best model is always saved

### Inference
1. **Threshold tuning**: Start with 0.7, adjust based on results
2. **Cooldown**: Prevents spam of multiple alerts
3. **Buffer status**: Wait for buffer to fill before detection starts

## Comparison: Pose-Based vs YOLO-Based

| Feature | YOLO-Based | Pose-Based (This System) |
|---------|------------|-------------------------|
| Accuracy | Moderate | High |
| False Positives | Common | Rare |
| Temporal Context | No | Yes (30 frames) |
| Body Orientation | Bounding box only | Full skeleton |
| Robustness | Lighting dependent | More robust |
| Speed | Very fast | Fast (25-30 fps) |
| Training Required | Pre-trained | Yes (custom dataset) |

## References

- **MediaPipe Pose**: https://google.github.io/mediapipe/solutions/pose
- **PyTorch**: https://pytorch.org/
- **LSTM Networks**: Understanding temporal sequences

## License

This project is for educational and research purposes.

## Support

For issues and questions:
1. Check this README
2. Review code comments
3. Test with synthetic data first
4. Verify dependencies are installed correctly
