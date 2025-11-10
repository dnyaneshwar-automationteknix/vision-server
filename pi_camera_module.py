"""
Raspberry Pi Camera Module
Supports both real Pi camera and mock mode for testing
"""

import time
import cv2
import numpy as np
from pathlib import Path
from typing import Optional, Tuple
from datetime import datetime
import threading


class CameraInterface:
    """Base camera interface"""
    
    def capture(self) -> Optional[np.ndarray]:
        """Capture image, returns BGR numpy array"""
        raise NotImplementedError
    
    def start(self):
        """Start camera"""
        pass
    
    def stop(self):
        """Stop camera"""
        pass
    
    def is_available(self) -> bool:
        """Check if camera is available"""
        return False


class PiCamera(CameraInterface):
    """
    Real Raspberry Pi Camera using picamera2
    Only works on Raspberry Pi hardware
    """
    
    def __init__(self, resolution: Tuple[int, int] = (1920, 1080),
                 framerate: int = 30):
        """
        Initialize Pi Camera
        Args:
            resolution: (width, height) tuple
            framerate: frames per second
        """
        self.resolution = resolution
        self.framerate = framerate
        self.camera = None
        self.running = False
        
        try:
            from picamera2 import Picamera2
            self.Picamera2 = Picamera2
            print("✓ picamera2 library available")
        except ImportError:
            print("⚠️ picamera2 not available (not on Pi or not installed)")
            self.Picamera2 = None
    
    def is_available(self) -> bool:
        """Check if Pi camera is available"""
        return self.Picamera2 is not None
    
    def start(self):
        """Start the camera"""
        if not self.is_available():
            print("✗ Cannot start Pi camera - picamera2 not available")
            return False
        
        try:
            self.camera = self.Picamera2()
            
            # Configure camera
            camera_config = self.camera.create_still_configuration(
                main={"size": self.resolution, "format": "RGB888"}
            )
            self.camera.configure(camera_config)
            
            # Start camera
            self.camera.start()
            self.running = True
            
            # Wait for camera to warm up
            time.sleep(2)
            
            print(f"✓ Pi Camera started: {self.resolution[0]}x{self.resolution[1]} @ {self.framerate}fps")
            return True
        
        except Exception as e:
            print(f"✗ Failed to start Pi camera: {e}")
            return False
    
    def stop(self):
        """Stop the camera"""
        if self.camera and self.running:
            self.camera.stop()
            self.camera.close()
            self.running = False
            print("✓ Pi Camera stopped")
    
    def capture(self) -> Optional[np.ndarray]:
        """
        Capture image from Pi camera
        Returns: BGR numpy array or None
        """
        if not self.running:
            print("✗ Camera not running")
            return None
        
        try:
            # Capture RGB image
            rgb_array = self.camera.capture_array()
            
            # Convert RGB to BGR for OpenCV
            bgr_array = cv2.cvtColor(rgb_array, cv2.COLOR_RGB2BGR)
            
            return bgr_array
        
        except Exception as e:
            print(f"✗ Capture failed: {e}")
            return None
    
    def capture_with_preview(self, preview_time: float = 2.0) -> Optional[np.ndarray]:
        """
        Capture with preview (shows camera feed)
        Args:
            preview_time: seconds to show preview before capture
        """
        if not self.running:
            self.start()
        
        print(f"Preview for {preview_time} seconds...")
        time.sleep(preview_time)
        
        return self.capture()


class MockCamera(CameraInterface):
    """
    Mock camera for testing without Pi hardware
    Generates test images or loads from directory
    """
    
    def __init__(self, resolution: Tuple[int, int] = (1920, 1080),
                 test_images_dir: str = None):
        """
        Initialize mock camera
        Args:
            resolution: (width, height) for generated images
            test_images_dir: Directory with test images (optional)
        """
        self.resolution = resolution
        self.test_images_dir = Path(test_images_dir) if test_images_dir else None
        self.test_images = []
        self.current_index = 0
        self.running = False
        
        if self.test_images_dir and self.test_images_dir.exists():
            # Load test images
            for ext in ['*.jpg', '*.jpeg', '*.png']:
                self.test_images.extend(self.test_images_dir.glob(ext))
            
            if self.test_images:
                print(f"✓ Mock camera: Found {len(self.test_images)} test images")
        
        if not self.test_images:
            print("✓ Mock camera: Will generate synthetic images")
    
    def is_available(self) -> bool:
        """Mock camera is always available"""
        return True
    
    def start(self):
        """Start mock camera"""
        self.running = True
        print(f"✓ Mock camera started: {self.resolution[0]}x{self.resolution[1]}")
        return True
    
    def stop(self):
        """Stop mock camera"""
        self.running = False
        print("✓ Mock camera stopped")
    
    def capture(self) -> Optional[np.ndarray]:
        """
        Capture mock image
        Returns: BGR numpy array
        """
        if not self.running:
            self.start()
        
        # If we have test images, use them
        if self.test_images:
            return self._load_test_image()
        else:
            return self._generate_test_image()
    
    def _load_test_image(self) -> np.ndarray:
        """Load image from test directory"""
        img_path = self.test_images[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.test_images)
        
        img = cv2.imread(str(img_path))
        
        # Resize to target resolution
        if img is not None:
            img = cv2.resize(img, self.resolution)
        
        return img
    
    def _generate_test_image(self) -> np.ndarray:
        """Generate synthetic test image"""
        # Create base image with noise
        img = np.random.randint(80, 120, 
                               (self.resolution[1], self.resolution[0], 3), 
                               dtype=np.uint8)
        
        # Add product region (colored rectangle)
        colors = [(0, 0, 200), (0, 200, 0), (200, 0, 0), (200, 200, 0)]
        color = colors[self.current_index % len(colors)]
        
        x1, y1 = self.resolution[0] // 4, self.resolution[1] // 4
        x2, y2 = 3 * self.resolution[0] // 4, 3 * self.resolution[1] // 4
        
        cv2.rectangle(img, (x1, y1), (x2, y2), color, -1)
        
        # Add text (simulates product label)
        timestamp = datetime.now().strftime("%H:%M:%S")
        cv2.putText(img, f"MOCK PRODUCT", 
                   (x1 + 50, y1 + 100),
                   cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 255), 3)
        
        cv2.putText(img, f"LOT2024-{self.current_index:04d}", 
                   (x1 + 50, y1 + 160),
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        
        cv2.putText(img, timestamp, 
                   (x1 + 50, y2 - 50),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (200, 200, 200), 2)
        
        # Add QR code placeholder
        qr_size = 150
        qr_x = x2 - qr_size - 50
        qr_y = y1 + 50
        cv2.rectangle(img, (qr_x, qr_y), (qr_x + qr_size, qr_y + qr_size), 
                     (255, 255, 255), -1)
        cv2.putText(img, "QR", (qr_x + 45, qr_y + 90),
                   cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 0), 3)
        
        self.current_index += 1
        
        return img


class USBCamera(CameraInterface):
    """
    USB/Webcam support
    Works on any system with OpenCV
    """
    
    def __init__(self, camera_index: int = 0, 
                 resolution: Tuple[int, int] = (1920, 1080)):
        """
        Initialize USB camera
        Args:
            camera_index: Camera device index (0 for default)
            resolution: Target resolution
        """
        self.camera_index = camera_index
        self.resolution = resolution
        self.cap = None
        self.running = False
    
    def is_available(self) -> bool:
        """Check if USB camera is available"""
        cap = cv2.VideoCapture(self.camera_index)
        available = cap.isOpened()
        cap.release()
        return available
    
    def start(self):
        """Start USB camera"""
        self.cap = cv2.VideoCapture(self.camera_index)
        
        if not self.cap.isOpened():
            print(f"✗ Failed to open USB camera {self.camera_index}")
            return False
        
        # Set resolution
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.resolution[0])
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.resolution[1])
        
        self.running = True
        print(f"✓ USB camera started: Camera {self.camera_index}")
        return True
    
    def stop(self):
        """Stop USB camera"""
        if self.cap:
            self.cap.release()
            self.running = False
            print("✓ USB camera stopped")
    
    def capture(self) -> Optional[np.ndarray]:
        """
        Capture from USB camera
        Returns: BGR numpy array or None
        """
        if not self.running:
            if not self.start():
                return None
        
        ret, frame = self.cap.read()
        
        if ret:
            return frame
        else:
            print("✗ Failed to capture from USB camera")
            return None


class CameraManager:
    """
    Manages different camera types
    Auto-selects best available camera
    """
    
    def __init__(self, config: dict = None):
        """
        Initialize camera manager
        Args:
            config: Camera configuration dictionary
        """
        self.config = config or {}
        self.camera = None
        self.camera_type = None
    
    def get_camera(self) -> CameraInterface:
        """
        Get appropriate camera based on availability and config
        Returns: Camera interface instance
        """
        # Check if mock mode is enabled
        if self.config.get('mock_mode', {}).get('enabled', False):
            print("📷 Using Mock Camera (testing mode)")
            test_dir = self.config.get('mock_mode', {}).get('sample_images_dir')
            resolution = tuple(self.config.get('camera', {}).get('resolution', [1920, 1080]))
            self.camera = MockCamera(resolution=resolution, test_images_dir=test_dir)
            self.camera_type = 'mock'
            return self.camera
        
        # Try Pi Camera first
        resolution = tuple(self.config.get('camera', {}).get('resolution', [1920, 1080]))
        framerate = self.config.get('camera', {}).get('framerate', 30)
        
        pi_cam = PiCamera(resolution=resolution, framerate=framerate)
        if pi_cam.is_available():
            print("📷 Using Raspberry Pi Camera")
            self.camera = pi_cam
            self.camera_type = 'pi'
            return self.camera
        
        # Try USB camera
        usb_cam = USBCamera(resolution=resolution)
        if usb_cam.is_available():
            print("📷 Using USB Camera")
            self.camera = usb_cam
            self.camera_type = 'usb'
            return self.camera
        
        # Fallback to mock
        print("📷 No hardware camera found, using Mock Camera")
        self.camera = MockCamera(resolution=resolution)
        self.camera_type = 'mock'
        return self.camera
    
    def start(self):
        """Start selected camera"""
        if not self.camera:
            self.get_camera()
        return self.camera.start()
    
    def stop(self):
        """Stop camera"""
        if self.camera:
            self.camera.stop()
    
    def capture(self) -> Optional[np.ndarray]:
        """Capture image"""
        if not self.camera:
            self.get_camera()
            self.start()
        return self.camera.capture()
    
    def get_camera_type(self) -> str:
        """Get current camera type"""
        return self.camera_type


# ==================== CONTINUOUS CAPTURE MODE ====================

class ContinuousCaptureThread:
    """
    Background thread for continuous image capture
    Useful for live monitoring
    """
    
    def __init__(self, camera: CameraInterface, callback, interval: float = 1.0):
        """
        Args:
            camera: Camera interface
            callback: Function to call with each captured image
            interval: Seconds between captures
        """
        self.camera = camera
        self.callback = callback
        self.interval = interval
        self.running = False
        self.thread = None
    
    def start(self):
        """Start continuous capture"""
        if self.running:
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.thread.start()
        print("✓ Continuous capture started")
    
    def stop(self):
        """Stop continuous capture"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)
        print("✓ Continuous capture stopped")
    
    def _capture_loop(self):
        """Capture loop running in thread"""
        while self.running:
            try:
                img = self.camera.capture()
                if img is not None:
                    self.callback(img)
            except Exception as e:
                print(f"✗ Capture error: {e}")
            
            time.sleep(self.interval)


# ==================== TEST/DEMO ====================

if __name__ == "__main__":
    print("=" * 60)
    print("Camera Module - Test")
    print("=" * 60)
    
    # Test camera manager
    print("\n📷 Testing Camera Manager...")
    
    config = {
        'mock_mode': {'enabled': True},
        'camera': {'resolution': [1280, 720], 'framerate': 30}
    }
    
    manager = CameraManager(config)
    camera = manager.get_camera()
    
    print(f"   Camera type: {manager.get_camera_type()}")
    
    # Start and capture
    camera.start()
    
    print("\n📸 Capturing 3 test images...")
    for i in range(3):
        img = camera.capture()
        if img is not None:
            print(f"   ✓ Image {i+1}: {img.shape}")
            
            # Save test image
            output_dir = Path("test_captures")
            output_dir.mkdir(exist_ok=True)
            filename = output_dir / f"test_{i+1}.jpg"
            cv2.imwrite(str(filename), img)
            print(f"     Saved: {filename}")
        
        time.sleep(1)
    
    camera.stop()
    
    print("\n✓ Camera test complete!")
    print("\nCamera types available:")
    print("  - Mock Camera: Always available (testing)")
    print("  - Pi Camera: Requires picamera2 on Raspberry Pi")
    print("  - USB Camera: Any USB webcam")