"""
COMPLETE Vision Engine with ROI Selection & Color Detection
"""

import cv2
import numpy as np
from typing import Dict, List, Tuple, Optional
import time


class VisionEngine:
    """Complete vision processing with ROI and color detection"""
    
    def __init__(self, config: Dict = None):
        self.config = config or self._get_default_config()
        self._qr_available = False
        self._ocr_available = False
        self._init_qr_detector()
        self._init_ocr_engine()
    
    def _get_default_config(self) -> Dict:
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
        try:
            from pyzbar import pyzbar
            self.pyzbar = pyzbar
            self._qr_available = True
            print("✓ QR detection enabled")
        except ImportError:
            print("⚠ QR detection disabled (pip install pyzbar)")
            self.pyzbar = None
    
    def _init_ocr_engine(self):
        try:
            import pytesseract
            self.pytesseract = pytesseract
            self._ocr_available = True
            print("✓ OCR enabled")
        except ImportError:
            print("⚠ OCR disabled (pip install pytesseract)")
            self.pytesseract = None
    
    def load_image_from_bytes(self, image_bytes: bytes) -> Optional[np.ndarray]:
        """Load image from bytes"""
        try:
            arr = np.frombuffer(image_bytes, dtype=np.uint8)
            img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
            if img is not None and len(img.shape) == 3 and img.shape[2] == 4:
                img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
            return img
        except Exception as e:
            print(f"Error loading image: {e}")
            return None
    
    def preprocess_image(self, img: np.ndarray) -> np.ndarray:
        """Resize if too large"""
        if img is None:
            return None
        max_w = self.config['preprocessing']['resize_max_width']
        max_h = self.config['preprocessing']['resize_max_height']
        h, w = img.shape[:2]
        if w > max_w or h > max_h:
            scale = min(max_w/w, max_h/h)
            new_w, new_h = int(w * scale), int(h * scale)
            img = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)
        return img
    
    # ==================== QR CODE DETECTION ====================
    
    def detect_qr_codes(self, img: np.ndarray, roi: Dict = None) -> List[Dict]:
        """
        Detect QR codes with bounding boxes
        Args:
            img: Input image
            roi: Optional ROI {type, coords} for detection area
        Returns: List of {data, type, bbox_norm, bbox_pixels}
        """
        if img is None or not hasattr(img, "shape"):
            return []
        
        # Apply ROI if provided
        if roi:
            img = self._extract_roi(img, roi)
            if img is None:
                return []
        
        results = []
        h, w = img.shape[:2]
        
        # Try OpenCV QRCodeDetector
        detector = cv2.QRCodeDetector()
        try:
            data, points, _ = detector.detectAndDecode(img)
            if data and points is not None:
                pts = points.reshape(-1, 2).astype(int)
                x, y, bw, bh = cv2.boundingRect(pts)
                results.append({
                    "data": data,
                    "type": "QR",
                    "bbox_norm": [(x + bw/2)/w, (y + bh/2)/h, bw/w, bh/h],
                    "bbox_pixels": [x, y, bw, bh]
                })
        except Exception as e:
            print(f"QR OpenCV error: {e}")
        
        # Fallback to pyzbar
        if not results and self._qr_available:
            try:
                decoded = self.pyzbar.decode(img)
                for qr in decoded:
                    x, y, bw, bh = qr.rect
                    results.append({
                        "data": qr.data.decode("utf-8"),
                        "type": qr.type,
                        "bbox_norm": [(x + bw/2)/w, (y + bh/2)/h, bw/w, bh/h],
                        "bbox_pixels": [x, y, bw, bh]
                    })
            except Exception as e:
                print(f"pyzbar error: {e}")
        
        return results
    
    # ==================== OCR TEXT RECOGNITION ====================
    
    def extract_text_simple(self, img: np.ndarray, roi: Dict = None) -> str:
        """
        Extract text from image or ROI
        Args:
            img: Input image
            roi: Optional ROI for text extraction
        """
        if not self._ocr_available:
            return ""
        
        try:
            # Apply ROI if provided
            if roi:
                img = self._extract_roi(img, roi)
                if img is None:
                    return ""
            
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            # Enhance contrast
            gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
            text = self.pytesseract.image_to_string(gray).strip()
            return text
        except Exception as e:
            print(f"OCR error: {e}")
            return ""
    
    # ==================== COLOR DETECTION ====================
    
    def detect_color_in_roi(self, img: np.ndarray, roi: Dict, 
                           color_name: str = "auto") -> Dict:
        """
        Detect color in selected ROI
        Args:
            img: Input image
            roi: ROI definition {type, coords}
            color_name: Target color or 'auto' for dominant
        Returns: Color analysis results
        """
        if img is None or not roi:
            return {"error": "Invalid input"}
        
        # Extract ROI
        roi_img = self._extract_roi(img, roi)
        if roi_img is None:
            return {"error": "Failed to extract ROI"}
        
        try:
            # Convert to HSV
            hsv = cv2.cvtColor(roi_img, cv2.COLOR_BGR2HSV)
            
            if color_name == "auto":
                # Detect dominant color
                dominant = self._get_dominant_color(roi_img)
                return {
                    "mode": "dominant",
                    "color_rgb": dominant["rgb"],
                    "color_name": dominant["name"],
                    "percentage": 100.0,
                    "roi_info": roi
                }
            else:
                # Detect specific color
                color_ranges = self._get_color_ranges(color_name)
                if not color_ranges:
                    return {"error": f"Unknown color: {color_name}"}
                
                lower = np.array(color_ranges["lower"])
                upper = np.array(color_ranges["upper"])
                mask = cv2.inRange(hsv, lower, upper)
                
                total_pixels = roi_img.shape[0] * roi_img.shape[1]
                color_pixels = cv2.countNonZero(mask)
                percentage = (color_pixels / total_pixels) * 100
                
                return {
                    "mode": "specific",
                    "color_name": color_name,
                    "percentage": round(percentage, 2),
                    "detected": percentage > 5.0,  # At least 5%
                    "roi_info": roi
                }
        
        except Exception as e:
            print(f"Color detection error: {e}")
            return {"error": str(e)}
    
    def _get_dominant_color(self, img: np.ndarray) -> Dict:
        """Get dominant color using k-means"""
        try:
            pixels = img.reshape(-1, 3).astype(np.float32)
            criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 100, 0.2)
            _, _, centers = cv2.kmeans(pixels, 1, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
            
            dominant_bgr = centers[0].astype(int)
            dominant_rgb = (int(dominant_bgr[2]), int(dominant_bgr[1]), int(dominant_bgr[0]))
            
            # Classify color
            color_name = self._classify_color(dominant_rgb)
            
            return {
                "rgb": dominant_rgb,
                "bgr": tuple(dominant_bgr),
                "name": color_name
            }
        except Exception as e:
            print(f"Dominant color error: {e}")
            return {"rgb": (0, 0, 0), "name": "unknown"}
    
    def _classify_color(self, rgb: Tuple[int, int, int]) -> str:
        """Classify RGB color into name"""
        r, g, b = rgb
        
        # Simple classification
        if r > 200 and g < 100 and b < 100:
            return "red"
        elif r < 100 and g > 200 and b < 100:
            return "green"
        elif r < 100 and g < 100 and b > 200:
            return "blue"
        elif r > 200 and g > 200 and b < 100:
            return "yellow"
        elif r > 200 and g < 150 and b > 200:
            return "magenta"
        elif r < 100 and g > 200 and b > 200:
            return "cyan"
        elif r > 200 and g > 200 and b > 200:
            return "white"
        elif r < 50 and g < 50 and b < 50:
            return "black"
        else:
            return "mixed"
    
    def _get_color_ranges(self, color_name: str) -> Optional[Dict]:
        """Get HSV ranges for color detection"""
        ranges = {
            "red": {"lower": [0, 100, 100], "upper": [10, 255, 255]},
            "green": {"lower": [40, 100, 100], "upper": [80, 255, 255]},
            "blue": {"lower": [100, 100, 100], "upper": [130, 255, 255]},
            "yellow": {"lower": [20, 100, 100], "upper": [40, 255, 255]},
            "cyan": {"lower": [80, 100, 100], "upper": [100, 255, 255]},
            "magenta": {"lower": [140, 100, 100], "upper": [170, 255, 255]},
            "white": {"lower": [0, 0, 200], "upper": [180, 30, 255]},
            "black": {"lower": [0, 0, 0], "upper": [180, 255, 30]}
        }
        return ranges.get(color_name.lower())
    
    # ==================== ROI EXTRACTION ====================
    
    def _extract_roi(self, img: np.ndarray, roi: Dict) -> Optional[np.ndarray]:
        """
        Extract ROI from image
        Args:
            img: Input image
            roi: {type: "rect"|"circle"|"polygon", coords: [...]}
        """
        if img is None or not roi:
            return None
        
        try:
            h, w = img.shape[:2]
            roi_type = roi.get("type", "rect")
            coords = roi.get("coords", [])
            
            if roi_type == "rect" and len(coords) == 4:
                # Rectangle: [x, y, width, height] (normalized 0-1)
                x1 = int(coords[0] * w)
                y1 = int(coords[1] * h)
                x2 = int((coords[0] + coords[2]) * w)
                y2 = int((coords[1] + coords[3]) * h)
                return img[y1:y2, x1:x2]
            
            elif roi_type == "circle" and len(coords) == 3:
                # Circle: [cx, cy, radius] (normalized)
                cx = int(coords[0] * w)
                cy = int(coords[1] * h)
                radius = int(coords[2] * min(w, h))
                
                mask = np.zeros((h, w), dtype=np.uint8)
                cv2.circle(mask, (cx, cy), radius, 255, -1)
                result = cv2.bitwise_and(img, img, mask=mask)
                
                # Crop to circle bounds
                x1 = max(0, cx - radius)
                y1 = max(0, cy - radius)
                x2 = min(w, cx + radius)
                y2 = min(h, cy + radius)
                return result[y1:y2, x1:x2]
            
            elif roi_type == "polygon" and len(coords) >= 6:
                # Polygon: [x1, y1, x2, y2, x3, y3, ...]
                points = []
                for i in range(0, len(coords), 2):
                    px = int(coords[i] * w)
                    py = int(coords[i+1] * h)
                    points.append([px, py])
                
                points = np.array([points], dtype=np.int32)
                mask = np.zeros((h, w), dtype=np.uint8)
                cv2.fillPoly(mask, points, 255)
                result = cv2.bitwise_and(img, img, mask=mask)
                
                # Crop to bounding box
                x, y, bw, bh = cv2.boundingRect(points)
                return result[y:y+bh, x:x+bw]
            
            else:
                # No ROI or invalid - return full image
                return img
        
        except Exception as e:
            print(f"ROI extraction error: {e}")
            return img
    
    # ==================== IMAGE QUALITY ====================
    
    def check_blur(self, img: np.ndarray) -> Dict:
        """Check image blur"""
        try:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
            threshold = self.config['image_quality']['blur_threshold']
            return {
                'blur_score': round(laplacian_var, 2),
                'is_blurry': laplacian_var < threshold,
                'threshold': threshold,
                'status': 'FAIL' if laplacian_var < threshold else 'PASS'
            }
        except Exception as e:
            print(f"Blur check error: {e}")
            return {'blur_score': 0, 'is_blurry': True, 'status': 'ERROR'}
    
    def check_brightness(self, img: np.ndarray) -> Dict:
        """Check image brightness"""
        try:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            brightness = np.mean(gray)
            min_b = self.config['image_quality']['brightness_min']
            max_b = self.config['image_quality']['brightness_max']
            is_ok = min_b <= brightness <= max_b
            return {
                'brightness': round(brightness, 2),
                'is_acceptable': is_ok,
                'min_threshold': min_b,
                'max_threshold': max_b,
                'status': 'PASS' if is_ok else 'FAIL'
            }
        except Exception as e:
            print(f"Brightness check error: {e}")
            return {'brightness': 0, 'is_acceptable': False, 'status': 'ERROR'}
    
    def check_image_quality(self, img: np.ndarray) -> Dict:
        """Complete quality check"""
        blur_result = self.check_blur(img)
        brightness_result = self.check_brightness(img)
        overall_pass = (blur_result['status'] == 'PASS' and brightness_result['status'] == 'PASS')
        return {
            'blur': blur_result,
            'brightness': brightness_result,
            'overall_status': 'PASS' if overall_pass else 'FAIL',
            'acceptable': overall_pass
        }
    
    # ==================== UTILITY ====================
    
    def save_image(self, img: np.ndarray, output_path: str) -> bool:
        """Save image to file"""
        try:
            cv2.imwrite(str(output_path), img)
            return True
        except Exception as e:
            print(f"Save error: {e}")
            return False


# ==================== TEST ====================
if __name__ == "__main__":
    print("Vision Engine - Complete Test")
    vision = VisionEngine()
    print("✓ Initialized")