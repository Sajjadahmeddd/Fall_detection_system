"""
Test script to verify client camera frame processing is working
"""

import sys

def test_app_modifications():
    """Check if app.py has the correct modifications"""
    print("Testing app.py for client camera processing fix...")
    
    with open('app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    checks = {
        'process_frame function exists': 'def process_frame(frame):' in content,
        'processed_frame emission': "'processed_frame'" in content,
        'frame processing in handle_frame': 'processed_frame = process_frame(frame)' in content,
        'base64 encoding of processed frame': 'base64.b64encode(buffer)' in content,
        'emit processed frame': "emit('processed_frame'" in content,
    }
    
    all_passed = True
    for check_name, result in checks.items():
        status = "✅" if result else "❌"
        print(f"  {status} {check_name}")
        if not result:
            all_passed = False
    
    return all_passed

def test_js_modifications():
    """Check if script.js has the correct modifications"""
    print("\nTesting script.js for client camera display fix...")
    
    with open('static/js/script.js', 'r', encoding='utf-8') as f:
        content = f.read()
    
    checks = {
        'processed_frame listener': "socket.on('processed_frame'" in content,
        'videoFeed src update': 'videoFeed.src = frameData' in content,
        'client_camera check': "sourceType.value === 'client_camera'" in content,
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
    print("Client Camera Processing Fix - Verification")
    print("="*60 + "\n")
    
    app_ok = test_app_modifications()
    js_ok = test_js_modifications()
    
    print("\n" + "="*60)
    if app_ok and js_ok:
        print("✅ All checks passed!")
        print("\nThe fix is in place. Now:")
        print("1. Restart the server: python app.py")
        print("2. Access from client device")
        print("3. Select 'Client Camera (Your Device)'")
        print("4. Start Detection")
        print("5. You should now see the processed video with fall detection!")
        return 0
    else:
        print("❌ Some checks failed.")
        return 1

if __name__ == '__main__':
    sys.exit(main())
