"""
QC Vision System - Startup Script
Handles all imports and initialization properly
"""

import sys
import os

# Ensure all files are in the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 80)
print("🚀 QC Vision System - Starting Up...")
print("=" * 80)

# Check dependencies
print("\n📦 Checking dependencies...")
missing_deps = []

try:
    import cv2
    print("  ✓ OpenCV")
except ImportError:
    missing_deps.append("opencv-python")
    print("  ✗ OpenCV (pip install opencv-python)")

try:
    import numpy
    print("  ✓ NumPy")
except ImportError:
    missing_deps.append("numpy")
    print("  ✗ NumPy (pip install numpy)")

try:
    from pyzbar import pyzbar
    print("  ✓ pyzbar (QR/Barcode)")
except ImportError:
    print("  ⚠ pyzbar (optional - pip install pyzbar)")

try:
    import pytesseract
    print("  ✓ pytesseract (OCR)")
except ImportError:
    print("  ⚠ pytesseract (optional - pip install pytesseract)")

if missing_deps:
    print(f"\n❌ Missing required dependencies: {', '.join(missing_deps)}")
    print(f"Install with: pip install {' '.join(missing_deps)}")
    sys.exit(1)

# Import system modules
print("\n📥 Loading modules...")
try:
    from database import QCDatabase
    print("  ✓ Database")
except Exception as e:
    print(f"  ✗ Database: {e}")
    sys.exit(1)

try:
    from config_manager import ConfigManager
    print("  ✓ Config Manager")
except Exception as e:
    print(f"  ✗ Config Manager: {e}")
    sys.exit(1)

try:
    from vision_engine_complete import VisionEngineComplete
    print("  ✓ Vision Engine")
except Exception as e:
    print(f"  ✗ Vision Engine: {e}")
    sys.exit(1)

try:
    from color_detection_engine import ColorDetectionEngine
    print("  ✓ Color Detection Engine")
except Exception as e:
    print(f"  ✗ Color Detection Engine: {e}")
    sys.exit(1)

try:
    from web_server_complete import WebServerComplete
    print("  ✓ Web Server")
except Exception as e:
    print(f"  ✗ Web Server: {e}")
    sys.exit(1)

try:
    from enhanced_dashboard_complete import EnhancedDashboardComplete
    print("  ✓ Dashboard")
except Exception as e:
    print(f"  ✗ Dashboard: {e}")
    sys.exit(1)

try:
    from camera_handler import CameraHandler
    print("  ✓ Camera Handler")
except Exception as e:
    print(f"  ✗ Camera Handler: {e}")
    sys.exit(1)

# Import main system
try:
    from main import QCSystemHandler
    print("  ✓ QC System Handler")
except Exception as e:
    print(f"  ✗ QC System Handler: {e}")
    sys.exit(1)

print("\n✅ All modules loaded successfully!")

# Initialize system
print("\n🔧 Initializing system...")
try:
    system = QCSystemHandler()
    print("✓ System initialized")
except Exception as e:
    print(f"✗ System initialization failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Start web server
print("\n🌐 Starting web server...")
try:
    web_server = WebServerComplete(host='0.0.0.0', port=8081)
    server = web_server.start(system.get_dashboard_state(), system)
    print("✓ Web server started")
except Exception as e:
    print(f"✗ Web server failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Display information
print("\n" + "=" * 80)
print("✅ QC VISION SYSTEM ONLINE")
print("=" * 80)

print(f"\n🌐 Web Interface:")
print(f"   Dashboard:        http://localhost:8081/dashboard")
print(f"   Interactive UI:   http://localhost:8081/interactive")
print(f"   Camera Settings:  http://localhost:8081/settings")
print(f"   Inspections:      http://localhost:8081/inspections")
print(f"   Reports:          http://localhost:8081/reports")

# Camera info
camera_info = system.camera.get_info() if system.camera else {}
print(f"\n📹 Camera:")
print(f"   Source: {camera_info.get('source', 'unknown')}")
print(f"   Type: {camera_info.get('type', 'unknown')}")
if camera_info.get('device_index') is not None:
    print(f"   Device Index: {camera_info.get('device_index')}")
print(f"   Status: {'✓ Connected' if camera_info.get('is_open') else '✗ Disconnected'}")

# Configuration
config = system.config
vision_config = config.get_vision_config()
auto_detect = vision_config.get('auto_detection', {})

print(f"\n⚙️ Configuration:")
print(f"   Auto-Detection: {'✓ Enabled' if auto_detect.get('enabled') else '✗ Disabled'}")
if auto_detect.get('enabled'):
    print(f"     • QR/Barcode: {'✓' if auto_detect.get('detect_qr') else '✗'}")
    print(f"     • OCR: {'✓' if auto_detect.get('detect_ocr') else '✗'}")
    print(f"     • Colors: {'✓' if auto_detect.get('detect_colors') else '✗'}")
    print(f"     • Quality: {'✓' if auto_detect.get('detect_quality') else '✗'}")

camera_config = config.get_camera_config()
print(f"   Image Saving:")
print(f"     • Original: {'✓' if camera_config.get('save_images') else '✗'}")
print(f"     • Thumbnails: {'✓' if camera_config.get('save_thumbnails') else '✗'}")
print(f"     • Annotated: {'✓' if camera_config.get('save_annotated') else '✗'}")

# Storage
server_config = config.get_server_config()
storage = server_config.get('storage', {})
print(f"\n💾 Storage:")
print(f"   Images:     {storage.get('image_dir', 'N/A')}")
print(f"   Thumbnails: {storage.get('thumbnail_dir', 'N/A')}")
print(f"   Annotated:  {storage.get('annotated_dir', 'N/A')}")

print(f"\n✨ Features:")
print(f"  ✓ Multi-camera support (Webcam, PC Camera, Pi Camera, Mock)")
print(f"  ✓ Auto-detection (QR, OCR, Colors, Quality)")
print(f"  ✓ Manual ROI drawing (Rectangle, Circle, Polygon, Line, Freehand)")
print(f"  ✓ Complete image saving (Original, Annotated, Thumbnails)")
print(f"  ✓ Camera source tracking in database")

print(f"\n🔑 Quick Start:")
print(f"  1. Open http://localhost:8081/dashboard in your browser")
print(f"  2. Go to Settings to configure camera")
print(f"  3. Use Interactive UI for live detection")
print(f"  4. Draw ROI on camera feed")
print(f"  5. Click Analyze to detect QR/OCR/Colors")

print("\nPress Ctrl+C to stop")
print("=" * 80 + "\n")

# Run server
try:
    server.serve_forever()
except KeyboardInterrupt:
    print("\n\n🛑 Shutting down...")
    web_server.stop()
    system.stop()
    print("✅ System stopped cleanly")
    sys.exit(0)