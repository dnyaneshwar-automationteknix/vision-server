"""
QC Vision System - Vision Processing Engine
Core computer vision algorithms for inspection
Works with both real images and test images
No hardware dependency - pure image processing
"""

import cv2
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from pathlib import Path
import time


class VisionEngine:
    """
    Core vision processing engine
    Handles: QR, OCR, Color Detection, Image Quality
    """
    
    def __init__(self, config: Dict = None):
        """
        Initialize vision engine with configuration
        Args:
            config: Vision configuration dictionary
        """
        self.config = config or self._get_default_config()
        
        # Try to load optional libraries
        self._qr_available = False
        self._ocr_available = False
        
        self._init_qr_detector()
        self._init_ocr_engine()
    
    def _get_default_config(self) -> Dict:
        """Default vision configuration"""
        return {
            "qr_detection": {"enabled": True, "min_size": 50},
            "ocr": {"enabled": True, "min_confidence": 60},
            "color_detection": {"enabled": True, "tolerance": 30},
            "image_quality": {
                "blur_threshold": 100,
                "brightness_min": 50,
                "brightness_max": 200
            },
            "preprocessing": {
                "resize_max_width": 1920,
                "resize_max_height": 1080
            }
        }
    
    def _init_qr_detector(self):
        """Initialize QR code detector"""
        try:
            from pyzbar import pyzbar
            self.pyzbar = pyzbar
            self._qr_available = True
            print("✓ QR detection enabled (pyzbar loaded)")
        except ImportError:
            print("⚠ QR detection disabled (pip install pyzbar)")
            self.pyzbar = None
    
    def _init_ocr_engine(self):
        """Initialize OCR engine"""
        try:
            import pytesseract
            self.pytesseract = pytesseract
            self._ocr_available = True
            print("✓ OCR enabled (pytesseract loaded)")
        except ImportError:
            print("⚠ OCR disabled (pip install pytesseract)")
            self.pytesseract = None
    
    # ==================== IMAGE LOADING ====================
    
    def load_image(self, image_path: str) -> Optional[np.ndarray]:
        """
        Load image from file path
        Returns: BGR numpy array or None
        """
        try:
            img = cv2.imread(str("image.jpg"))
            if img is None:
                print(f"✗ Failed to load image: {image_path}")
                return None
            return img
        except Exception as e:
            print(f"✗ Error loading image: {e}")
            return None
    
    def load_image_from_bytes(self, b: bytes):
        arr = np.frombuffer(b, dtype=np.uint8)
        img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if img is None:
            return None
        # ensure BGR color and no alpha
        if img.shape[2] == 4:
            img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
        return img

    
    def preprocess_image(self, img: np.ndarray) -> np.ndarray:
        """Apply preprocessing based on config"""
        if img is None:
            return None
        
        # Resize if too large
        max_w = self.config['preprocessing']['resize_max_width']
        max_h = self.config['preprocessing']['resize_max_height']
        
        h, w = img.shape[:2]
        if w > max_w or h > max_h:
            scale = min(max_w/w, max_h/h)
            new_w = int(w * scale)
            new_h = int(h * scale)
            img = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)
        
        return img
    
    # ==================== QR CODE DETECTION ====================
    
    def detect_qr_codes(self, img: np.ndarray):
        """
        Return list of detected qrcodes:
        [
            {
                'data': 'QR TEXT',
                'type': 'QR',
                'bbox': [x1,y1,x2,y2,x3,y3,x4,y4],
                'bbox_norm': [cx_norm, cy_norm, w_norm, h_norm],
                'confidence': 0.9
            }, ...
        ]
        """
        results = []
        h, w = img.shape[:2]

        # 1) Try OpenCV QRCodeDetector
        qr_decoder = cv2.QRCodeDetector()
        try:
            data, points, _ = qr_decoder.detectAndDecode(img)
            if points is not None and len(data.strip()) > 0:
                pts = points.reshape(-1, 2)
                flat = pts.flatten().tolist()
                # normalized bbox: compute bounding rect
                x, y, bw, bh = cv2.boundingRect(pts.astype(int))
                results.append({
                    'data': data,
                    'type': 'QR',
                    'bbox': [int(xy) for xy in flat],
                    'bbox_norm': [ (x + bw/2) / w, (y + bh/2) / h, bw / w, bh / h ],
                    'confidence': 0.95
                })
                return results  # often single QR, return quickly
        except Exception:
            pass

        # 2) Fallback to pyzbar (if installed)
        try:
            from pyzbar.pyzbar import decode as pyz_decode
            decoded = pyz_decode(img)
            for d in decoded:
                pts = d.polygon
                if len(pts) >= 4:
                    flat = []
                    xs = []
                    ys = []
                    for p in pts:
                        flat.extend([p.x, p.y])
                        xs.append(p.x); ys.append(p.y)
                    x, y, bw, bh = int(min(xs)), int(min(ys)), int(max(xs)-min(xs)), int(max(ys)-min(ys))
                    results.append({
                        'data': d.data.decode('utf-8', errors='ignore'),
                        'type': d.type,
                        'bbox': [int(v) for v in flat],
                        'bbox_norm': [ (x + bw/2) / w, (y + bh/2) / h, bw / w, bh / h ],
                        'confidence': getattr(d, 'quality', 0.8)
                    })
            return results
        except Exception:
            # pyzbar not installed or decode failed
            return results
    
    def draw_qr_codes(self, img: np.ndarray, qr_codes: List[Dict]) -> np.ndarray:
        """Draw QR code bounding boxes on image"""
        img_copy = img.copy()
        
        for qr in qr_codes:
            # Draw rectangle
            rect = qr['rect']
            cv2.rectangle(img_copy, 
                         (rect['x'], rect['y']),
                         (rect['x'] + rect['width'], rect['y'] + rect['height']),
                         (0, 255, 0), 2)
            
            # Draw label
            label = f"QR: {qr['data'][:20]}"
            cv2.putText(img_copy, label,
                       (rect['x'], rect['y'] - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        return img_copy
    
    # ==================== OCR TEXT RECOGNITION ====================
    
    def recognize_text(self, img: np.ndarray, roi: Dict = None) -> List[Dict]:
        """
        Recognize text in image or ROI
        Args:
            img: Input image
            roi: Optional region of interest {x, y, width, height}
        Returns: List of {text, confidence, box}
        """
        if not self._ocr_available or not self.config['ocr']['enabled']:
            return []
        
        try:
            # Extract ROI if specified
            if roi:
                x, y, w, h = roi['x'], roi['y'], roi['width'], roi['height']
                img = img[y:y+h, x:x+w]
            
            # Convert to grayscale
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Apply preprocessing for better OCR
            gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
            
            # Perform OCR
            data = self.pytesseract.image_to_data(gray, output_type=self.pytesseract.Output.DICT)
            
            results = []
            min_conf = self.config['ocr']['min_confidence']
            
            for i in range(len(data['text'])):
                text = data['text'][i].strip()
                conf = int(data['conf'][i])
                
                if text and conf >= min_conf:
                    results.append({
                        'text': text,
                        'confidence': conf,
                        'box': {
                            'x': data['left'][i],
                            'y': data['top'][i],
                            'width': data['width'][i],
                            'height': data['height'][i]
                        }
                    })
            
            return results
        
        except Exception as e:
            print(f"✗ OCR error: {e}")
            return []
    
    def extract_text_simple(self, img: np.ndarray) -> str:
        """Simple text extraction (single string result)"""
        if not self._ocr_available:
            return ""
        
        try:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            text = self.pytesseract.image_to_string(gray).strip()
            return text
        except Exception as e:
            print(f"✗ OCR error: {e}")
            return ""
    
    # ==================== COLOR DETECTION ====================
    
    def detect_color(self, img: np.ndarray, color_ranges: Dict, 
                    roi: Dict = None) -> Dict:
        """
        Detect specific colors in image
        Args:
            img: Input image
            color_ranges: {color_name: [h_min, h_max, s_min, s_max, v_min, v_max]}
            roi: Optional region of interest
        Returns: {color_name: {percentage, area, detected}}
        """
        if not self.config['color_detection']['enabled']:
            return {}
        
        try:
            # Extract ROI if specified
            if roi:
                x, y, w, h = roi['x'], roi['y'], roi['width'], roi['height']
                img = img[y:y+h, x:x+w]
            
            # Convert to HSV
            hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
            
            total_pixels = img.shape[0] * img.shape[1]
            results = {}
            
            for color_name, ranges in color_ranges.items():
                # Create mask for color range
                lower = np.array(ranges[0::2])  # [h_min, s_min, v_min]
                upper = np.array(ranges[1::2])  # [h_max, s_max, v_max]
                
                mask = cv2.inRange(hsv, lower, upper)
                
                # Calculate area
                color_pixels = cv2.countNonZero(mask)
                percentage = (color_pixels / total_pixels) * 100
                
                results[color_name] = {
                    'percentage': round(percentage, 2),
                    'area': color_pixels,
                    'detected': percentage > 1.0  # At least 1% presence
                }
            
            return results
        
        except Exception as e:
            print(f"✗ Color detection error: {e}")
            return {}
    
    def detect_dominant_color(self, img: np.ndarray, k: int = 3) -> List[Tuple]:
        """
        Detect dominant colors using K-means clustering
        Returns: List of (color_bgr, percentage) tuples
        """
        try:
            # Reshape image to 2D array of pixels
            pixels = img.reshape(-1, 3).astype(np.float32)
            
            # K-means clustering
            criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 100, 0.2)
            _, labels, centers = cv2.kmeans(pixels, k, None, criteria, 10, 
                                           cv2.KMEANS_RANDOM_CENTERS)
            
            # Calculate percentages
            unique, counts = np.unique(labels, return_counts=True)
            percentages = (counts / len(labels)) * 100
            
            # Sort by percentage
            dominant_colors = sorted(zip(centers, percentages), 
                                   key=lambda x: x[1], reverse=True)
            
            return [(tuple(map(int, color)), round(pct, 2)) 
                   for color, pct in dominant_colors]
        
        except Exception as e:
            print(f"✗ Dominant color error: {e}")
            return []
    
    # ==================== IMAGE QUALITY CHECKS ====================
    
    def check_blur(self, img: np.ndarray) -> Dict:
        """
        Check image blur using Laplacian variance
        Returns: {blur_score, is_blurry, threshold}
        """
        try:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
            
            threshold = self.config['image_quality']['blur_threshold']
            is_blurry = laplacian_var < threshold
            
            return {
                'blur_score': round(laplacian_var, 2),
                'is_blurry': is_blurry,
                'threshold': threshold,
                'status': 'FAIL' if is_blurry else 'PASS'
            }
        
        except Exception as e:
            print(f"✗ Blur check error: {e}")
            return {'blur_score': 0, 'is_blurry': True, 'status': 'ERROR'}
    
    def check_brightness(self, img: np.ndarray) -> Dict:
        """
        Check image brightness
        Returns: {brightness, is_acceptable, min, max}
        """
        try:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            brightness = np.mean(gray)
            
            min_bright = self.config['image_quality']['brightness_min']
            max_bright = self.config['image_quality']['brightness_max']
            
            is_acceptable = min_bright <= brightness <= max_bright
            
            return {
                'brightness': round(brightness, 2),
                'is_acceptable': is_acceptable,
                'min_threshold': min_bright,
                'max_threshold': max_bright,
                'status': 'PASS' if is_acceptable else 'FAIL'
            }
        
        except Exception as e:
            print(f"✗ Brightness check error: {e}")
            return {'brightness': 0, 'is_acceptable': False, 'status': 'ERROR'}
    
    def check_image_quality(self, img: np.ndarray) -> Dict:
        """
        Complete image quality check
        Returns: Combined quality metrics
        """
        blur_result = self.check_blur(img)
        brightness_result = self.check_brightness(img)
        
        overall_pass = (blur_result['status'] == 'PASS' and 
                       brightness_result['status'] == 'PASS')
        
        return {
            'blur': blur_result,
            'brightness': brightness_result,
            'overall_status': 'PASS' if overall_pass else 'FAIL',
            'acceptable': overall_pass
        }
    
    # ==================== COMPLETE INSPECTION ====================
    
    def inspect_image(self, img: np.ndarray, product_config: Dict = None) -> Dict:
        """
        Perform complete inspection on image
        Args:
            img: Input image
            product_config: Product-specific settings (QR pattern, colors, etc.)
        Returns: Complete inspection results
        """
        start_time = time.time()
        
        if img is None:
            return {'error': 'Invalid image', 'status': 'ERROR'}
        
        # Preprocess
        img = self.preprocess_image(img)
        
        results = {
            'timestamp': time.time(),
            'image_shape': img.shape,
            'processing_steps': {}
        }
        
        # Image quality check
        quality = self.check_image_quality(img)
        results['processing_steps']['quality'] = quality
        results['quality_pass'] = quality['acceptable']
        
        # QR detection
        if self.config['qr_detection']['enabled']:
            qr_codes = self.detect_qr_codes(img)
            results['processing_steps']['qr'] = {
                'detected_count': len(qr_codes),
                'codes': qr_codes
            }
            results['qr_data'] = qr_codes[0]['data'] if qr_codes else None
        
        # OCR
        if self.config['ocr']['enabled']:
            text_results = self.recognize_text(img)
            combined_text = ' '.join([t['text'] for t in text_results])
            results['processing_steps']['ocr'] = {
                'text_blocks': len(text_results),
                'full_text': combined_text,
                'details': text_results
            }
            results['ocr_text'] = combined_text
        
        # Color detection (if product config provided)
        if product_config and 'color_ranges' in product_config:
            colors = self.detect_color(img, product_config['color_ranges'])
            results['processing_steps']['color'] = colors
            
            # Check if expected colors detected
            detected_colors = [c for c, data in colors.items() if data['detected']]
            results['colors_detected'] = detected_colors
        
        # Calculate processing time
        results['processing_time'] = round(time.time() - start_time, 3)
        
        # Overall status
        results['overall_status'] = self._determine_status(results, product_config)
        
        return results
    
    def _determine_status(self, results: Dict, product_config: Dict = None) -> str:
        """Determine overall inspection status"""
        # Quality must pass
        if not results.get('quality_pass', False):
            return 'NOK'
        
        # If no product config, just check quality
        if not product_config:
            return 'OK'
        
        # Check QR if expected
        if product_config.get('qr_pattern'):
            if not results.get('qr_data'):
                return 'NOK'
        
        # Check OCR if expected
        if product_config.get('ocr_expected'):
            ocr_text = results.get('ocr_text', '')
            if product_config['ocr_expected'] not in ocr_text:
                return 'NOK'
        
        # Check colors if expected
        if product_config.get('expected_colors'):
            detected = results.get('colors_detected', [])
            for expected_color in product_config['expected_colors']:
                if expected_color not in detected:
                    return 'NOK'
        
        return 'OK'
    
    # ==================== UTILITY ====================
    
    def save_image(self, img: np.ndarray, output_path: str) -> bool:
        """Save image to file"""
        try:
            cv2.imwrite(str(output_path), img)
            return True
        except Exception as e:
            print(f"✗ Error saving image: {e}")
            return False
    
    def create_thumbnail(self, img: np.ndarray, max_size: int = 200) -> np.ndarray:
        """Create thumbnail of image"""
        h, w = img.shape[:2]
        scale = min(max_size/w, max_size/h)
        new_w = int(w * scale)
        new_h = int(h * scale)
        return cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)


# ==================== TEST/DEMO ====================

if __name__ == "__main__":
    print("=" * 60)
    print("Vision Engine - Testing Module")
    print("=" * 60)
    
    # Initialize vision engine
    vision = VisionEngine()
    img = vision.load_image("image.jpg")
    print("✓ Loaded test image 'image.jpg'")
    print(f"   Image shape: {img.shape}")
    # Test with a solid color image (no real image needed)
    print("\n📸 Creating test image...")
    test_img = np.zeros((480, 640, 3), dtype=np.uint8)
    test_img[:, :] = (100, 150, 200)  # BGR color
    
    # Quality checks
    print("\n🔍 Running quality checks...")
    quality = vision.check_image_quality(test_img)
    print(f"   Blur: {quality['blur']['blur_score']} - {quality['blur']['status']}")
    print(f"   Brightness: {quality['brightness']['brightness']} - {quality['brightness']['status']}")
    print(f"   Overall: {quality['overall_status']}")
    
    # Dominant color
    print("\n🎨 Detecting dominant colors...")
    colors = vision.detect_dominant_color(test_img, k=3)
    for i, (color, pct) in enumerate(colors):
        print(f"   Color {i+1}: BGR{color} - {pct}%")
    
    # Complete inspection
    print("\n✅ Running complete inspection...")
    result = vision.inspect_image(test_img)
    print(f"   Status: {result['overall_status']}")
    print(f"   Processing time: {result['processing_time']}s")
    print(f"   Quality pass: {result['quality_pass']}")
    
    print("\n✓ Vision engine test complete!")
    print("\nTo test with real images:")

    print("   img = vision.load_image('path/to/image.jpg')")
    print("   result = vision.inspect_image(img)")