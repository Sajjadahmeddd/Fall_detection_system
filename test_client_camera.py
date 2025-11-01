"""
Quick Test Script for Client Camera Mode

This script verifies that the new client camera mode additions are properly configured.
"""

import sys
import os

def test_imports():
    """Test that all required imports are available"""
    print("Testing imports...")
    try:
        import flask
        import flask_socketio
        import cv2
        import numpy as np
        import base64
        from ultralytics import YOLO
        print("✅ All imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_app_file():
    """Test that app.py has the required modifications"""
    print("\nTesting app.py modifications...")
    
    with open('app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    checks = {
        'base64 import': 'import base64' in content,
        'numpy import': 'import numpy' in content,
        'use_client_camera variable': 'use_client_camera' in content,
        'latest_frame variable': 'latest_frame' in content,
        'frame_lock variable': 'frame_lock' in content,
        'handle_frame function': '@socketio.on(\'frame\')' in content,
        'client_camera type support': 'client_camera' in content,
        'max_http_buffer_size': 'max_http_buffer_size' in content,
    }
    
    all_passed = True
    for check_name, result in checks.items():
        status = "✅" if result else "❌"
        print(f"  {status} {check_name}")
        if not result:
            all_passed = False
    
    return all_passed

def test_html_file():
    """Test that index.html has the required modifications"""
    print("\nTesting index.html modifications...")
    
    with open('templates/index.html', 'r', encoding='utf-8') as f:
        content = f.read()
    
    checks = {
        'client_camera option': 'client_camera' in content.lower(),
        'Client Camera text': 'Client Camera' in content,
    }
    
    all_passed = True
    for check_name, result in checks.items():
        status = "✅" if result else "❌"
        print(f"  {status} {check_name}")
        if not result:
            all_passed = False
    
    return all_passed

def test_js_file():
    """Test that script.js has the required modifications"""
    print("\nTesting script.js modifications...")
    
    with open('static/js/script.js', 'r', encoding='utf-8') as f:
        content = f.read()
    
    checks = {
        'clientStream variable': 'clientStream' in content,
        'clientVideo variable': 'clientVideo' in content,
        'canvasElement variable': 'canvasElement' in content,
        'startClientCamera function': 'startClientCamera' in content,
        'stopClientCamera function': 'stopClientCamera' in content,
        'startFrameStreaming function': 'startFrameStreaming' in content,
        'captureAndSendFrame function': 'captureAndSendFrame' in content,
        'getUserMedia call': 'getUserMedia' in content,
        'socket.emit frame': "socket.emit('frame'" in content,
        'client_camera case': 'client_camera' in content,
    }
    
    all_passed = True
    for check_name, result in checks.items():
        status = "✅" if result else "❌"
        print(f"  {status} {check_name}")
        if not result:
            all_passed = False
    
    return all_passed

def main():
    print("="*60)
    print("Fall Detector 2.0 - Client Camera Mode Test")
    print("="*60)
    
    results = []
    
    results.append(("Imports", test_imports()))
    results.append(("app.py", test_app_file()))
    results.append(("index.html", test_html_file()))
    results.append(("script.js", test_js_file()))
    
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    
    all_passed = True
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
        if not result:
            all_passed = False
    
    print("="*60)
    
    if all_passed:
        print("\n🎉 All tests passed! Client Camera Mode is ready to use.")
        print("\nTo start the server:")
        print("  python app.py")
        print("\nThen access the web interface and select 'Client Camera (Your Device)'")
        return 0
    else:
        print("\n⚠️  Some tests failed. Please review the errors above.")
        return 1

if __name__ == '__main__':
    sys.exit(main())
