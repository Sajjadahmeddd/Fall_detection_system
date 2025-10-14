"""
Quick test script to verify config.py is being loaded correctly
"""
import config

print("="*60)
print("CONFIG.PY SETTINGS TEST")
print("="*60)
print("\n📊 Current Configuration Values:\n")

print(f"✓ CONFIDENCE_THRESHOLD: {config.CONFIDENCE_THRESHOLD}%")
print(f"✓ MIN_CONDITIONS_FOR_FALL: {config.MIN_CONDITIONS_FOR_FALL}/5")
print(f"✓ FALL_COOLDOWN_SECONDS: {config.FALL_COOLDOWN_SECONDS}s")
print(f"✓ MAX_ALERT_HISTORY: {config.MAX_ALERT_HISTORY}")
print(f"\n📐 Fall Detection Thresholds:\n")
print(f"  - LYING_WIDE_RATIO: {config.LYING_WIDE_RATIO}")
print(f"  - LYING_WIDE_HEIGHT: {config.LYING_WIDE_HEIGHT}")
print(f"  - COMPRESSED_HEIGHT: {config.COMPRESSED_HEIGHT}")
print(f"  - COMPRESSED_RATIO: {config.COMPRESSED_RATIO}")
print(f"  - HORIZONTAL_RATIO: {config.HORIZONTAL_RATIO}")
print(f"  - HORIZONTAL_HEIGHT: {config.HORIZONTAL_HEIGHT}")
print(f"  - VERY_WIDE_RATIO: {config.VERY_WIDE_RATIO}")
print(f"  - VERY_WIDE_HEIGHT: {config.VERY_WIDE_HEIGHT}")
print(f"  - STANDING_HEIGHT_THRESHOLD: {config.STANDING_HEIGHT_THRESHOLD}")

print(f"\n🎥 Video Settings:\n")
print(f"  - DEFAULT_FRAME_WIDTH: {config.DEFAULT_FRAME_WIDTH}")
print(f"  - DEFAULT_FRAME_HEIGHT: {config.DEFAULT_FRAME_HEIGHT}")
print(f"  - WEBCAM_WIDTH: {config.WEBCAM_WIDTH}")
print(f"  - WEBCAM_HEIGHT: {config.WEBCAM_HEIGHT}")

print(f"\n🤖 Model Settings:\n")
print(f"  - MODEL_PATH: {config.MODEL_PATH}")
print(f"  - CLASSES_FILE: {config.CLASSES_FILE}")

print("\n" + "="*60)
print("✅ Config file loaded successfully!")
print("="*60)
print("\nNOTE: Changing values in config.py will affect:")
print("  - app.py (Web Application)")
print("  - main.py (CLI Application)")
print("="*60)
