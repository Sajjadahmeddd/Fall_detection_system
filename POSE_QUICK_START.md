# Quick Start Guide - Pose-Based Fall Detection

## 5-Minute Setup and Demo

### Step 1: Install Dependencies (2 minutes)

```bash
pip install -r requirements.txt
```

### Step 2: Train on Synthetic Data (1 minute)

```bash
python train.py
```

This will:
- Create synthetic dataset automatically
- Train LSTM model for 50 epochs (with early stopping)
- Save best model to `./checkpoints/best_model.pth`

**Expected Output:**
```
Creating synthetic dataset...
Loaded 200 fall sequences
Loaded 200 no_fall sequences
Training...
Best Validation Accuracy: 0.92+ (Epoch ~15-25)
```

### Step 3: Run Real-Time Detection (2 minutes)

```bash
python inference.py
```

**Controls:**
- `q` - Quit
- `s` - Save screenshot

## Test Individual Modules

### Test Pose Extraction
```bash
python pose_extractor.py
```
- Shows webcam with pose skeleton overlay
- Press 's' to save 30-frame sequences
- Buffer indicator shows readiness

### Test Model Architecture
```bash
python model.py
```
- Validates LSTM and GRU models
- Shows parameter counts
- Tests forward pass

### Test Dataset Loader
```bash
python dataset_loader.py
```
- Creates synthetic dataset
- Tests data loading pipeline
- Shows batch iterations

## Common Commands

### Train with Custom Settings
```bash
# Edit train.py to change:
# - BATCH_SIZE
# - NUM_EPOCHS
# - LEARNING_RATE
# - MODEL_TYPE ('lstm' or 'gru')

python train.py
```

### Run Inference with Options
```bash
# From webcam with custom threshold
python inference.py --threshold 0.8

# Process video file
python inference.py --video input.mp4 --output output.mp4

# Use CPU instead of GPU
python inference.py --device cpu

# Use GRU model
python inference.py --model-type gru
```

## Expected Results

### Training Metrics (Synthetic Data)
- **Accuracy**: 90-95%
- **Training Time**: 2-5 minutes (CPU), <1 minute (GPU)
- **Convergence**: ~15-25 epochs

### Inference Performance
- **FPS**: 25-30 fps (CPU), 60+ fps (GPU)
- **Latency**: 1 second (30-frame buffer)
- **Detection Accuracy**: High on synthetic data

## Next Steps

1. **Collect Real Data**: Use `pose_extractor.py` to record real fall sequences
2. **Organize Data**: Place in `data/my_dataset/fall/` and `data/my_dataset/no_fall/`
3. **Retrain**: Modify `DATA_DIR` in `train.py` and run training
4. **Deploy**: Use trained model for real-world inference

## Troubleshooting Quick Fixes

| Issue | Solution |
|-------|----------|
| "No module named 'mediapipe'" | `pip install mediapipe` |
| "No module named 'torch'" | `pip install torch` |
| "Model not found" | Run `python train.py` first |
| "No pose detected" | Ensure good lighting, person fully visible |
| Slow inference | Use `--device cpu` or reduce `POSE_MODEL_COMPLEXITY` |

## File Locations

After training, check:
- **Model**: `./checkpoints/best_model.pth`
- **Plots**: `./checkpoints/training_curves.png`, `confusion_matrix.png`
- **History**: `./checkpoints/training_history.json`
- **Data**: `./data/synthetic_fall_dataset/` (auto-created)

## Minimum Working Example

```python
# minimal_example.py
import cv2
import torch
from pose_extractor import PoseExtractor, PoseSequenceBuffer
from model import get_model

# Initialize
extractor = PoseExtractor()
buffer = PoseSequenceBuffer(30)
model = get_model('lstm', input_size=34)
checkpoint = torch.load('checkpoints/best_model.pth')
model.load_state_dict(checkpoint['model_state_dict'])
model.eval()

# Process frame
cap = cv2.VideoCapture(0)
while True:
    ret, frame = cap.read()
    keypoints = extractor.extract_and_normalize(frame)
    
    if keypoints is not None:
        buffer.add_frame(keypoints)
        
        if buffer.is_full():
            sequence = torch.FloatTensor(buffer.get_flattened_sequence()).unsqueeze(0)
            with torch.no_grad():
                output = model(sequence)
                fall_prob = torch.softmax(output, dim=1)[0, 1].item()
                
            if fall_prob > 0.7:
                print(f"FALL DETECTED! Confidence: {fall_prob:.2%}")
    
    cv2.imshow('Fall Detection', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
```

Save as `minimal_example.py` and run:
```bash
python minimal_example.py
```

## Performance Optimization

### For Speed
```python
# In config.py
POSE_MODEL_COMPLEXITY = 0  # Lite model
POSE_SEQUENCE_LENGTH = 20  # Shorter sequence
MODEL_TYPE = 'gru'  # Faster than LSTM
```

### For Accuracy
```python
# In config.py
POSE_MODEL_COMPLEXITY = 2  # Heavy model
POSE_SEQUENCE_LENGTH = 40  # Longer context
POSE_CONFIDENCE_THRESHOLD = 0.8  # Higher threshold
```

## Getting Help

1. **Check logs**: Training and inference print detailed information
2. **Test modules**: Each .py file has `if __name__ == "__main__"` test code
3. **Read comments**: Code has extensive inline documentation
4. **Synthetic data**: Always test with synthetic data first

---

**Ready to start?** Run `python train.py` now!
