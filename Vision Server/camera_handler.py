"""
Universal Camera Handler
Supports: Webcam, PC Camera, Pi Camera, Mock Camera
Auto-detection and fallback mechanisms
"""

import cv2
import numpy as np
from typing import Optional, Tuple, List
import time
from pathlib import Path


class CameraHandler:
    """
    Universal camera handler with auto-detection
    """
    
    def __init__(self, config: dict = None):
        self.config = config or {}
        self.camera = None
        self.camera_source = self.config.get('source', 'webcam')
        self.device_index = self.config.get('device_index', 0)
        self.resolution = self.config.get('resolution', {'width': 1280, 'height': 720})
        self.is_open = False
        self.last_frame = None
        
        # Pi camera specific
        self.pi_camera = None
        self.use_pi_camera = False
        
    def detect_available_cameras(self) -> List[dict]:
        """
        Auto-detect available cameras
        Returns list of available camera sources
        """
        available = []
        
        # Check for Pi camera
        try:
            from picamera2 import Picamera2
            Picamera2.global_camera_info()
            available.append({
                'id': 'pi_camera',
                'name': 'Raspberry Pi Camera',
                'type': 'pi',
                'device_index': None
            })
            print("✓ Pi Camera detected")
        except:
            pass
        
        # Check for USB/PC cameras (indices 0-3)
        for idx in range(4):
            try:
                cap = cv2.VideoCapture(idx)
                if cap.isOpened():
                    ret, _ = cap.read()
                    if ret:
                        available.append({
                            'id': f'camera_{idx}',
                            'name': f'Camera {idx}' + (' (Default)' if idx == 0 else ''),
                            'type': 'usb' if idx > 0 else 'pc',
                            'device_index': idx
                        })
                        print(f"✓ Camera detected at index {idx}")
                cap.release()
            except:
                pass
        
        if not available:
            print("⚠ No cameras detected, using mock mode")
            available.append({
                'id': 'mock',
                'name': 'Mock Camera (Test Images)',
                'type': 'mock',
                'device_index': None
            })
        
        return available
    
    def open(self) -> bool:
        """
        Open camera based on configuration
        Returns True if successful
        """
        try:
            if self.camera_source == 'pi_camera':
                return self._open_pi_camera()
            elif self.camera_source in ['webcam', 'pc_camera']:
                return self._open_cv_camera()
            elif self.camera_source == 'mock':
                return self._open_mock_camera()
            else:
                # Default to PC camera
                return self._open_cv_camera()
        except Exception as e:
            print(f"Error opening camera: {e}")
            return False
    
    def _open_cv_camera(self) -> bool:
        """Open OpenCV camera (webcam/PC camera)"""
        try:
            self.camera = cv2.VideoCapture(self.device_index)
            
            if not self.camera.isOpened():
                print(f"Failed to open camera at index {self.device_index}")
                return False
            
            # Set resolution
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.resolution['width'])
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.resolution['height'])
            
            # Set other properties if available
            if 'framerate' in self.config:
                self.camera.set(cv2.CAP_PROP_FPS, self.config['framerate'])
            
            if 'brightness' in self.config:
                self.camera.set(cv2.CAP_PROP_BRIGHTNESS, self.config['brightness'] / 255.0)
            
            if 'contrast' in self.config:
                self.camera.set(cv2.CAP_PROP_CONTRAST, self.config['contrast'] / 255.0)
            
            # Test read
            ret, frame = self.camera.read()
            if not ret:
                print("Failed to read from camera")
                self.camera.release()
                return False
            
            self.is_open = True
            print(f"✓ Camera opened: {self.camera_source} (index {self.device_index})")
            return True
            
        except Exception as e:
            print(f"Error opening CV camera: {e}")
            return False
    
    def _open_pi_camera(self) -> bool:
        """Open Raspberry Pi camera"""
        try:
            from picamera2 import Picamera2
            
            self.pi_camera = Picamera2()
            
            # Configure camera
            config = self.pi_camera.create_still_configuration(
                main={"size": (self.resolution['width'], self.resolution['height'])}
            )
            self.pi_camera.configure(config)
            
            # Start camera
            self.pi_camera.start()
            time.sleep(2)  # Allow camera to warm up
            
            self.use_pi_camera = True
            self.is_open = True
            print("✓ Pi Camera opened")
            return True
            
        except ImportError:
            print("⚠ picamera2 not installed. Run: pip install picamera2")
            return False
        except Exception as e:
            print(f"Error opening Pi camera: {e}")
            return False
    
    def _open_mock_camera(self) -> bool:
        """Open mock camera (returns test images)"""
        self.is_open = True
        print("✓ Mock camera active")
        return True
    
    def read(self) -> Tuple[bool, Optional[np.ndarray]]:
        """
        Read frame from camera
        Returns (success, frame)
        """
        if not self.is_open:
            return False, None
        
        try:
            if self.use_pi_camera:
                return self._read_pi_camera()
            elif self.camera_source == 'mock':
                return self._read_mock_camera()
            else:
                return self._read_cv_camera()
        except Exception as e:
            print(f"Error reading frame: {e}")
            return False, None
    
    def _read_cv_camera(self) -> Tuple[bool, Optional[np.ndarray]]:
        """Read from OpenCV camera"""
        if self.camera is None or not self.camera.isOpened():
            return False, None
        
        ret, frame = self.camera.read()
        
        if ret:
            # Apply transformations
            if self.config.get('flip_horizontal'):
                frame = cv2.flip(frame, 1)
            if self.config.get('flip_vertical'):
                frame = cv2.flip(frame, 0)
            if self.config.get('rotation'):
                frame = self._rotate_frame(frame, self.config['rotation'])
            
            self.last_frame = frame
        
        return ret, frame
    
    def _read_pi_camera(self) -> Tuple[bool, Optional[np.ndarray]]:
        """Read from Pi camera"""
        if self.pi_camera is None:
            return False, None
        
        try:
            frame = self.pi_camera.capture_array()
            
            # Convert RGB to BGR for OpenCV compatibility
            if len(frame.shape) == 3 and frame.shape[2] == 3:
                frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            
            # Apply transformations
            if self.config.get('flip_horizontal'):
                frame = cv2.flip(frame, 1)
            if self.config.get('flip_vertical'):
                frame = cv2.flip(frame, 0)
            if self.config.get('rotation'):
                frame = self._rotate_frame(frame, self.config['rotation'])
            
            self.last_frame = frame
            return True, frame
            
        except Exception as e:
            print(f"Error reading Pi camera: {e}")
            return False, None
    
    def _read_mock_camera(self) -> Tuple[bool, Optional[np.ndarray]]:
        """Read from mock camera (test images)"""
        # Create a test pattern
        width = self.resolution['width']
        height = self.resolution['height']
        
        # Create colored test pattern
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        
        # Draw gradient
        for i in range(width):
            color = int((i / width) * 255)
            frame[:, i] = [color, 255 - color, 128]
        
        # Add timestamp
        timestamp = time.strftime("%H:%M:%S")
        cv2.putText(frame, f"MOCK CAMERA - {timestamp}", 
                   (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 
                   1.0, (255, 255, 255), 2)
        
        # Add test QR code region
        cv2.rectangle(frame, (100, 100), (300, 300), (0, 255, 0), 2)
        cv2.putText(frame, "QR CODE HERE", (120, 210), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        self.last_frame = frame
        return True, frame
    
    def _rotate_frame(self, frame: np.ndarray, angle: int) -> np.ndarray:
        """Rotate frame by angle (90, 180, 270)"""
        if angle == 90:
            return cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
        elif angle == 180:
            return cv2.rotate(frame, cv2.ROTATE_180)
        elif angle == 270:
            return cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)
        return frame
    
    def capture(self) -> Optional[np.ndarray]:
        """
        Capture a single frame
        Returns frame or None
        """
        ret, frame = self.read()
        return frame if ret else None
    
    def get_frame_size(self) -> Tuple[int, int]:
        """Get current frame size (width, height)"""
        if self.last_frame is not None:
            h, w = self.last_frame.shape[:2]
            return (w, h)
        return (self.resolution['width'], self.resolution['height'])
    
    def set_property(self, property_name: str, value: any):
        """Set camera property"""
        if self.camera and self.camera.isOpened():
            prop_map = {
                'brightness': cv2.CAP_PROP_BRIGHTNESS,
                'contrast': cv2.CAP_PROP_CONTRAST,
                'saturation': cv2.CAP_PROP_SATURATION,
                'hue': cv2.CAP_PROP_HUE,
                'gain': cv2.CAP_PROP_GAIN,
                'exposure': cv2.CAP_PROP_EXPOSURE
            }
            
            if property_name in prop_map:
                self.camera.set(prop_map[property_name], value)
    
    def get_info(self) -> dict:
        """Get camera information"""
        return {
            'source': self.camera_source,
            'device_index': self.device_index,
            'is_open': self.is_open,
            'resolution': self.resolution,
            'current_size': self.get_frame_size(),
            'type': 'pi' if self.use_pi_camera else 'cv' if self.camera else 'mock'
        }
    
    def close(self):
        """Close camera and release resources"""
        if self.camera:
            self.camera.release()
            self.camera = None
        
        if self.pi_camera:
            try:
                self.pi_camera.stop()
                self.pi_camera.close()
            except:
                pass
            self.pi_camera = None
        
        self.is_open = False
        print("✓ Camera closed")
    
    def __del__(self):
        """Cleanup on deletion"""
        self.close()


# ==================== USAGE EXAMPLE ====================

def test_camera():
    """Test camera handler"""
    from config_manager import ConfigManager
    
    config = ConfigManager()
    camera_config = config.get_camera_config()
    
    print("\n" + "="*60)
    print("Camera Handler Test")
    print("="*60)
    
    # Detect available cameras
    handler = CameraHandler(camera_config)
    available = handler.detect_available_cameras()
    
    print(f"\n📹 Available Cameras: {len(available)}")
    for cam in available:
        print(f"  - {cam['name']} ({cam['type']})")
    
    # Open camera
    print(f"\n🔌 Opening camera: {camera_config['source']}")
    if handler.open():
        print("✓ Camera opened successfully")
        
        # Capture test frame
        frame = handler.capture()
        if frame is not None:
            print(f"✓ Captured frame: {frame.shape}")
            
            # Save test image
            test_path = "test_capture.jpg"
            cv2.imwrite(test_path, frame)
            print(f"✓ Saved test image: {test_path}")
        
        # Get camera info
        info = handler.get_info()
        print(f"\n📊 Camera Info:")
        for key, value in info.items():
            print(f"  {key}: {value}")
        
        handler.close()
    else:
        print("✗ Failed to open camera")
    
    print("="*60)


if __name__ == "__main__":
    test_camera()