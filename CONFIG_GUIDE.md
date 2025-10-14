# 🎛️ Configuration Guide

## ✅ FIXED: Configuration Now Works!

Both `app.py` (Web App) and `main.py` (CLI) now read settings from `config.py`.

---

## 📝 Quick Configuration Changes

### Change Confidence Threshold

**File**: `config.py`  
**Line**: `CONFIDENCE_THRESHOLD = 65`

```python
# Lower = Detect more people (including less clear detections)
# Higher = Only detect clear, high-confidence people

CONFIDENCE_THRESHOLD = 65  # Current: Detects persons with 65%+ confidence
CONFIDENCE_THRESHOLD = 50  # More sensitive (may have false positives)
CONFIDENCE_THRESHOLD = 80  # Less sensitive (misses some detections)
```

### Change Fall Sensitivity

**File**: `config.py`  
**Line**: `MIN_CONDITIONS_FOR_FALL = 2`

```python
# Number of conditions that must be met (out of 5)

MIN_CONDITIONS_FOR_FALL = 1  # Very sensitive (many false positives)
MIN_CONDITIONS_FOR_FALL = 2  # Balanced (RECOMMENDED)
MIN_CONDITIONS_FOR_FALL = 3  # Conservative (may miss some falls)
```

### Change Alert Cooldown

**File**: `config.py`  
**Line**: `FALL_COOLDOWN_SECONDS = 3`

```python
# Seconds between repeated fall alerts for same person

FALL_COOLDOWN_SECONDS = 1   # Alert every second (can be annoying)
FALL_COOLDOWN_SECONDS = 3   # Alert every 3 seconds (RECOMMENDED)
FALL_COOLDOWN_SECONDS = 10  # Alert every 10 seconds (may miss events)
```

### Change Detection Ratios

**File**: `config.py`

```python
# Make fall detection MORE SENSITIVE (detect more falls):
LYING_WIDE_RATIO = 1.0        # Was 1.2 (lower = more sensitive)
LYING_WIDE_HEIGHT = 0.50      # Was 0.45 (higher = more sensitive)
VERY_WIDE_RATIO = 1.5         # Was 1.8 (lower = more sensitive)

# Make fall detection LESS SENSITIVE (fewer false positives):
LYING_WIDE_RATIO = 1.5        # Was 1.2 (higher = less sensitive)
LYING_WIDE_HEIGHT = 0.35      # Was 0.45 (lower = less sensitive)
VERY_WIDE_RATIO = 2.0         # Was 1.8 (higher = less sensitive)
```

---

## 🧪 Test Your Configuration

After changing `config.py`, run:

```powershell
python test_config.py
```

This will show all current values to verify your changes.

---

## 🎯 Common Scenarios

### Scenario 1: Too Many False Alarms
**Problem**: System detects falls when person is just sitting/crouching

**Solution**:
```python
MIN_CONDITIONS_FOR_FALL = 3  # Require more conditions
LYING_WIDE_RATIO = 1.5       # Stricter aspect ratio
STANDING_HEIGHT_THRESHOLD = 0.50  # More lenient standing filter
```

### Scenario 2: Missing Real Falls
**Problem**: System doesn't detect when person is actually lying down

**Solution**:
```python
MIN_CONDITIONS_FOR_FALL = 1  # Require fewer conditions
LYING_WIDE_HEIGHT = 0.55     # Allow taller lying poses
VERY_WIDE_RATIO = 1.5        # Easier to trigger wide detection
CONFIDENCE_THRESHOLD = 50    # Detect less confident persons
```

### Scenario 3: Person Stretching Arms Triggers False Alarm
**Problem**: Standing person with stretched arms detected as fallen

**Solution**:
```python
STANDING_HEIGHT_THRESHOLD = 0.50  # Lower threshold (was 0.55)
LYING_WIDE_HEIGHT = 0.35          # Stricter height requirement (was 0.45)
MIN_CONDITIONS_FOR_FALL = 3       # Require more conditions
```

### Scenario 4: Webcam Too Close (Close-up view)
**Problem**: Person fills entire frame, making detection difficult

**Solution**:
```python
LYING_WIDE_HEIGHT = 0.60      # Allow larger height ratios
HORIZONTAL_HEIGHT = 0.50      # Allow larger height for horizontal
WIDE_AREA_COVERAGE = 0.10     # Require less area coverage (was 0.05)
```

### Scenario 5: Camera Far Away (Overhead/Wide view)
**Problem**: Person appears small in frame

**Solution**:
```python
COMPRESSED_HEIGHT = 0.20      # Stricter compression requirement (was 0.30)
WIDE_AREA_COVERAGE = 0.02     # Allow smaller area coverage (was 0.05)
MIN_CONDITIONS_FOR_FALL = 2   # Keep balanced requirement
```

---

## 📊 Understanding the Values

### Aspect Ratio (Width/Height)
- **< 1.0**: Person is taller than wide (standing/sitting)
- **= 1.0**: Person is square (transitioning)
- **> 1.0**: Person is wider than tall (lying down)
- **> 2.0**: Person is very wide (definitely lying)

### Height Ratio (Height/Frame Height)
- **> 0.60**: Person takes up most of frame (likely standing close)
- **0.40-0.60**: Normal standing person
- **0.30-0.40**: Short person, sitting, or lying
- **< 0.30**: Very compressed (likely lying down)

### Area Coverage
- **< 0.05**: Small portion of frame (5%)
- **0.05-0.15**: Medium coverage (5-15%)
- **> 0.15**: Large coverage (person very close or lying)

---

## 🔄 Apply Changes

After editing `config.py`:

1. **For Web App**: Restart the server
   ```powershell
   # Press Ctrl+C to stop
   python app.py
   ```

2. **For CLI App**: Just run it again
   ```powershell
   python main.py
   ```

Changes take effect immediately on restart!

---

## 💾 Backup Your Settings

Before experimenting, save a copy:

```powershell
copy config.py config_backup.py
```

To restore:
```powershell
copy config_backup.py config.py
```

---

## 📝 Default Values (Reference)

If you mess up, here are the working defaults:

```python
CONFIDENCE_THRESHOLD = 65
MIN_CONDITIONS_FOR_FALL = 2
FALL_COOLDOWN_SECONDS = 3

LYING_WIDE_RATIO = 1.2
LYING_WIDE_HEIGHT = 0.45
COMPRESSED_HEIGHT = 0.30
COMPRESSED_RATIO = 0.8
HORIZONTAL_RATIO = 0.9
HORIZONTAL_HEIGHT = 0.4
VERY_WIDE_RATIO = 1.8
VERY_WIDE_HEIGHT = 0.55
STANDING_HEIGHT_THRESHOLD = 0.55
```

---

## 🎓 Pro Tips

1. **Start Conservative**: Begin with strict settings, then relax
2. **Test Each Change**: Modify one value at a time
3. **Document Changes**: Comment your modifications in config.py
4. **Use test_config.py**: Always verify your changes load correctly
5. **Monitor Console**: Watch the debug output to understand detections

---

## ✅ Verification Checklist

Before using in production:

- [ ] Run `python test_config.py` - Config loads correctly
- [ ] Test with known fall video - Detects correctly
- [ ] Test with standing person - No false positives
- [ ] Test with sitting person - No false positives
- [ ] Test with stretching arms - No false positives
- [ ] Adjust confidence threshold for your camera quality
- [ ] Set appropriate cooldown for your use case

---

**Now your `config.py` controls everything!** 🎉

Change values there, restart the app, and you're good to go!
