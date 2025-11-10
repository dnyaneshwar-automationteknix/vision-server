# QC Vision System - Step by Step Guide

## 🎯 What You Have Now

A complete, modular QC vision inspection system that works **WITHOUT hardware** for development and testing.

### ✅ Completed Modules

1. **database.py** - Complete SQLite database system
2. **config_manager.py** - Configuration management  
3. **vision_engine.py** - Computer vision algorithms (QR, OCR, Color, Quality)
4. **communication.py** - HTTP client/server for Pi-Windows communication
5. **example_integration.py** - Complete working example

---

## 📦 Installation

### Minimum Requirements (Works Now)
```bash
pip install opencv-python numpy
```

### Optional Features
```bash
# For QR code detection
pip install pyzbar

# For OCR text recognition
pip install pytesseract
# Also need to install Tesseract: https://github.com/tesseract-ocr/tesseract

# For better OCR (alternative)
pip install easyocr
```

---

## 🚀 Quick Start

### Test 1: Database Only (No Dependencies)
```python
from database import QCDatabase

# Create database
db = QCDatabase("my_qc.db")

# Add product
product_id = db.add_product(
    product_code="PROD-001",
    product_name="Blue Widget",
    qr_pattern="QR-.*",
    ocr_expected="LOT2024",
    color_ranges={"blue": [100, 130, 100, 255, 100, 255]}
)

# Add inspection
inspection_id = db.add_inspection(
    product_id=product_id,
    qr_data="QR-12345",
    status="OK",
    blur_score=0.92
)

# Get statistics
stats = db.get_statistics()
print(f"Total: {stats['total_inspections']}")
print(f"Pass rate: {stats['pass_rate']}%")

db.close()
```

### Test 2: Vision Engine (Needs OpenCV)
```python
from vision_engine import VisionEngine
import cv2

vision = VisionEngine()

# Load test image
img = cv2.imread("test_image.jpg")

# OR create test image
import numpy as np
img = np.zeros((480, 640, 3), dtype=np.uint8)
img[:, :] = (100, 150, 200)  # Solid color

# Inspect
result = vision.inspect_image(img)

print(f"Status: {result['overall_status']}")
print(f"Blur score: {result['processing_steps']['quality']['blur']['blur_score']}")
print(f"Processing time: {result['processing_time']}s")
```

### Test 3: Communication Layer (No Dependencies)
```python
from communication import QCServer, QCClient
import time

# Start server
server = QCServer('localhost', 8080)
server.start(blocking=False)

time.sleep(1)

# Create client
client = QCClient('http://localhost:8080')

# Test connection
if client.ping():
    print("✓ Connected!")
    
    # Send test image
    test_data = b"fake_image_bytes"
    response = client.send_image(test_data, {'product': 'TEST-001'})
    print(response)

server.stop()
```

### Test 4: Complete System
```bash
python example_integration.py
```

This runs:
- ✅ Server on localhost:8080
- ✅ Simulated Pi client
- ✅ 3 test inspections
- ✅ Statistics report

---

## 🔧 Configuration

### Set System Mode

```python
from config_manager import ConfigManager

config = ConfigManager()

# Option 1: Server only (no Pi)
config.set_mode('server_only')

# Option 2: Pi only (no server)
config.set_mode('pi_only')

# Option 3: Both
config.set_mode('both')

# Enable mock camera (for testing without Pi)
config.set('pi', 'mock_mode.enabled', True)

# Set server URL (for real Pi)
config.set('pi', 'network.server_url', 'http://192.168.1.100:8080')
```

### Configuration Files Created

After first run, you'll have:
```
config/
├── pi_config.json       # Raspberry Pi settings
├── server_config.json   # Windows server settings
├── vision_config.json   # CV algorithm parameters
└── system_config.json   # System-wide settings
```

You can edit these directly!

---

## 📁 Project Structure

```
your_project/
├── database.py              # ✅ Database operations
├── config_manager.py        # ✅ Configuration management
├── vision_engine.py         # ✅ Computer vision
├── communication.py         # ✅ Network layer
├── example_integration.py   # ✅ Complete demo
│
├── config/                  # Auto-generated configs
│   ├── pi_config.json
│   ├── server_config.json
│   ├── vision_config.json
│   └── system_config.json
│
├── inspections/             # Auto-generated storage
│   ├── images/              # Full images
│   └── thumbnails/          # Thumbnails
│
├── backups/                 # Database backups
├── logs/                    # System logs
└── test_data/               # Your test images
    └── sample_images/
```

---

## 🎮 Usage Modes

### Mode 1: Development (Current)
**What**: Test everything on one Windows machine  
**How**: Use `server_only` mode with mock camera  
**Benefit**: No hardware needed, fast iteration

```python
config.set_mode('server_only')
config.set('pi', 'mock_mode.enabled', True)
```

### Mode 2: Pi Testing
**What**: Test Pi capture, send to local server  
**How**: Run Pi client on Pi, server on Windows (same network)  

**On Windows:**
```python
# server.py
from example_integration import QCServerApplication
from config_manager import ConfigManager

config = ConfigManager()
config.set('server', 'api.host', '0.0.0.0')  # Listen on all interfaces
config.set('server', 'api.port', 8080)

server = QCServerApplication(config)
server.start()

input("Press Enter to stop...")
server.stop()
```

**On Raspberry Pi:**
```python
# client.py
from example_integration import QCClientApplication
from config_manager import ConfigManager

config = ConfigManager()
config.set('pi', 'enabled', True)
config.set('pi', 'mock_mode.enabled', False)  # Use real camera
config.set('pi', 'network.server_url', 'http://192.168.1.100:8080')  # Your Windows IP

client = QCClientApplication(config)

# Capture and send
result = client.capture_and_send(product_code="WIDGET-001")
print(result)
```

### Mode 3: Production
**What**: Pi captures → Windows processes → Database stores  
**How**: Both components running independently

---

## 🧪 Testing Individual Components

### Test Each Module Separately:

```bash
# Test database
python -c "from database import QCDatabase; db = QCDatabase('test.db'); print('✓ Database works')"

# Test configuration
python -c "from config_manager import ConfigManager; c = ConfigManager(); print('✓ Config works')"

# Test vision (needs OpenCV)
python -c "from vision_engine import VisionEngine; v = VisionEngine(); print('✓ Vision works')"

# Test communication
python -c "from communication import QCServer; s = QCServer(); print('✓ Communication works')"

# Test complete integration
python example_integration.py
```

### Test Specific Features:

```bash
# Test vision only
python example_integration.py vision

# Test communication only
python example_integration.py comm

# Test database only
python example_integration.py db
```

---

## 🔍 What Each Module Does

### database.py
- SQLite operations
- Products, Inspections, Defects, Users
- Statistics and reporting
- Backup functionality
- **No external dependencies**

### config_manager.py
- JSON-based configuration
- Separate configs for Pi and Server
- Mode selection (pi_only/server_only/both)
- Validation
- **No external dependencies**

### vision_engine.py
- QR code detection (pyzbar)
- OCR text recognition (pytesseract)
- Color detection (OpenCV)
- Image quality checks (blur, brightness)
- **Dependencies: opencv-python, optional: pyzbar, pytesseract**

### communication.py
- HTTP client (for Pi)
- HTTP server (for Windows)
- Image transfer via base64
- Retry logic and error handling
- **No external dependencies (uses stdlib)**

---

## 📝 Next Steps

Now you can:

1. **✅ Test all modules** - They work independently
2. **✅ Run complete demo** - `python example_integration.py`
3. **⏳ Add real camera** - When you get Pi hardware
4. **⏳ Build web interface** - For visualization (next module)
5. **⏳ Add more vision features** - Shape detection, measurements, etc.

---

## 🤔 Common Questions

### Q: Can I run this without a Raspberry Pi?
**A:** Yes! Use `mock_mode` to test everything on Windows.

### Q: Can I run Pi and Server on same machine?
**A:** Yes! Just use `localhost` as server URL.

### Q: Do I need all vision libraries?
**A:** No! System works with just OpenCV. QR and OCR are optional.

### Q: How do I switch to real Pi camera?
**A:** Change one config: `config.set('pi', 'mock_mode.enabled', False)`

### Q: Can I use this with IP cameras?
**A:** Yes! Modify `capture_and_send()` to read from IP camera stream.

---

## 🐛 Troubleshooting

### "Port already in use"
```python
# Change port
config.set('server', 'api.port', 8081)
```

### "Cannot connect to server"
- Check firewall
- Use correct IP address (not localhost if on different machines)
- Ensure server is running

### "Import error: No module named..."
```bash
pip install opencv-python numpy
```

### "OCR not working"
- Install Tesseract executable (not just pip package)
- Or disable OCR: `config.set('vision', 'ocr.enabled', False)`

---

## 📞 Architecture Summary

```
┌─────────────────┐         HTTP          ┌──────────────────┐
│  Raspberry Pi   │ ──────────────────>  │ Windows Server   │
│  (Client)       │    POST /process     │  (Receiver)      │
│                 │       + image        │                  │
│  - Camera       │ <────────────────    │  - Vision Engine │
│  - Mock Mode    │    JSON response     │  - Database      │
│  - Local Cache  │                      │  - Web Interface │
└─────────────────┘                      └──────────────────┘
```

**Key Points:**
- ✅ Both can run on same machine for testing
- ✅ All configs are separate and selectable
- ✅ No shared state - pure HTTP communication
- ✅ Works offline (local network only)

---

## 🎉 You're Ready!

Start with:
```bash
python example_integration.py
```

This will show you the complete workflow working end-to-end with test data!