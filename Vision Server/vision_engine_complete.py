"""
Complete Vision Engine
Includes: QR/Barcode Detection, OCR, ROI Processing, Quality Checks
Keeps your existing detection methods intact
"""

import cv2
import numpy as np
from typing import Dict, List, Tuple, Optional
import time


class VisionEngineComplete:
    """
    Complete vision processing engine
    Maintains all existing QR/OCR functionality
    """
    
    def __init__(self, config: Dict = None):
        self.config = config or self._get_default_config()
        self.cv2 = cv2  # Expose cv2 for other modules
        self._qr_available = False
        self._ocr_available = False
        self._init_qr_detector()
        self._init_ocr_engine()
    
    def _get_default_config(self) -> Dict:
        return {
            "qr_detection": {"enabled": True, "min_size": 50},
            "ocr": {"enabled": True, "min_confidence": 60},
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
        """Initialize QR/Barcode detector"""
        try:
            from pyzbar import pyzbar
            self.pyzbar = pyzbar
            self._qr_available = True
            print("  ✓ QR/Barcode detection enabled")
        except ImportError:
            print("  ⚠ QR/Barcode detection disabled (pip install pyzbar)")
            self.pyzbar = None
    
    def _init_ocr_engine(self):
        """Initialize OCR engine"""
        try:
            import pytesseract
            self.pytesseract = pytesseract
            self._ocr_available = True
            print("  ✓ OCR enabled")
        except ImportError:
            print("  ⚠ OCR disabled (pip install pytesseract)")
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
        Detect QR codes and barcodes with bounding boxes
        KEEPS YOUR EXISTING FUNCTIONALITY
        
        Args:
            img: Input image
            roi: Optional ROI {type, coords}
        
        Returns:
            List of detected codes with format, data, bbox
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
        
        # Try OpenCV QRCodeDetector first
        detector = cv2.QRCodeDetector()
        try:
            data, points, _ = detector.detectAndDecode(img)
            if data and points is not None:
                pts = points.reshape(-1, 2).astype(int)
                x, y, bw, bh = cv2.boundingRect(pts)
                results.append({
                    "data": data,
                    "type": "QR",
                    "format": "QR_CODE",
                    "method": "opencv",
                    "bbox_norm": [(x + bw/2)/w, (y + bh/2)/h, bw/w, bh/h],
                    "bbox_pixels": [x, y, bw, bh],
                    "confidence": 1.0
                })
        except Exception as e:
            print(f"QR OpenCV error: {e}")
        
        # Fallback to pyzbar for multiple codes and barcodes
        if self._qr_available:
            try:
                decoded = self.pyzbar.decode(img)
                for qr in decoded:
                    x, y, bw, bh = qr.rect
                    # Check if already detected by OpenCV
                    already_detected = False
                    for r in results:
                        if r['data'] == qr.data.decode("utf-8"):
                            already_detected = True
                            break
                    
                    if not already_detected:
                        results.append({
                            "data": qr.data.decode("utf-8"),
                            "type": qr.type,
                            "format": qr.type,
                            "method": "pyzbar",
                            "bbox_norm": [(x + bw/2)/w, (y + bh/2)/h, bw/w, bh/h],
                            "bbox_pixels": [x, y, bw, bh],
                            "confidence": 0.9
                        })
            except Exception as e:
                print(f"pyzbar error: {e}")
        
        return results
    
    # ==================== OCR TEXT RECOGNITION ====================
    
    def extract_text_simple(self, img: np.ndarray, roi: Dict = None) -> str:
        """
        Extract text from image
        KEEPS YOUR EXISTING FUNCTIONALITY
        
        Args:
            img: Input image
            roi: Optional ROI for text extraction
        
        Returns:
            Extracted text string
        """
        if not self._ocr_available:
            return ""
        
        try:
            # Apply ROI if provided
            if roi:
                img = self._extract_roi(img, roi)
                if img is None:
                    return ""
            
            # Convert to grayscale
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Enhance contrast using OTSU thresholding
            gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
            
            # Extract text
            text = self.pytesseract.image_to_string(gray).strip()
            return text
            
        except Exception as e:
            print(f"OCR error: {e}")
            return ""
    
    def extract_text_detailed(self, img: np.ndarray, roi: Dict = None) -> List[Dict]:
        """
        Extract text with detailed information (coordinates, confidence)
        
        Returns:
            List of detected text blocks with details
        """
        if not self._ocr_available:
            return []
        
        try:
            # Apply ROI if provided
            if roi:
                img = self._extract_roi(img, roi)
                if img is None:
                    return []
            
            # Convert to grayscale
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
            
            # Get detailed data
            data = self.pytesseract.image_to_data(gray, output_type=self.pytesseract.Output.DICT)
            
            results = []
            n_boxes = len(data['text'])
            for i in range(n_boxes):
                if int(data['conf'][i]) > 60:  # Confidence threshold
                    text = data['text'][i].strip()
                    if text:
                        results.append({
                            'text': text,
                            'confidence': int(data['conf'][i]),
                            'left': int(data['left'][i]),
                            'top': int(data['top'][i]),
                            'width': int(data['width'][i]),
                            'height': int(data['height'][i])
                        })
            
            return results
            
        except Exception as e:
            print(f"Detailed OCR error: {e}")
            return []
    
    # ==================== ROI EXTRACTION ====================
    
    def _extract_roi(self, img: np.ndarray, roi: Dict) -> Optional[np.ndarray]:
        """
        Extract ROI from image
        KEEPS YOUR EXISTING FUNCTIONALITY
        
        Args:
            img: Input image
            roi: {type: "rectangle"|"circle"|"polygon", coords: [...]}
        
        Returns:
            Cropped image or None
        """
        if img is None or not roi:
            return None
        
        try:
            h, w = img.shape[:2]
            roi_type = roi.get("type", "rectangle")
            coords = roi.get("coords", [])
            
            if roi_type == "rectangle" and len(coords) >= 4:
                # Rectangle: [x, y, width, height] (normalized 0-1)
                x1 = int(coords[0] * w)
                y1 = int(coords[1] * h)
                x2 = int((coords[0] + coords[2]) * w)
                y2 = int((coords[1] + coords[3]) * h)
                return img[y1:y2, x1:x2]
            
            elif roi_type == "circle" and len(coords) >= 3:
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
                # Polygon: [[x1,y1], [x2,y2], ...]
                points = []
                for i in range(0, len(coords), 2):
                    if isinstance(coords[i], list):
                        # Already paired
                        px = int(coords[i][0] * w)
                        py = int(coords[i][1] * h)
                    else:
                        # Flat list
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
                # No valid ROI - return full image
                return img
        
        except Exception as e:
            print(f"ROI extraction error: {e}")
            return img
    
    # ==================== IMAGE QUALITY ====================
    
    def check_blur(self, img: np.ndarray) -> Dict:
        """
        Check image blur using Laplacian variance
        KEEPS YOUR EXISTING FUNCTIONALITY
        """
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
        """
        Check image brightness
        KEEPS YOUR EXISTING FUNCTIONALITY
        """
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
        """
        Complete quality check
        KEEPS YOUR EXISTING FUNCTIONALITY
        """
        blur_result = self.check_blur(img)
        brightness_result = self.check_brightness(img)
        
        overall_pass = (
            blur_result['status'] == 'PASS' and 
            brightness_result['status'] == 'PASS'
        )
        
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
    
    def resize_image(self, img: np.ndarray, width: int = None, 
                    height: int = None) -> np.ndarray:
        """Resize image maintaining aspect ratio"""
        if img is None:
            return None
        
        h, w = img.shape[:2]
        
        if width and height:
            return cv2.resize(img, (width, height), interpolation=cv2.INTER_AREA)
        elif width:
            ratio = width / w
            new_h = int(h * ratio)
            return cv2.resize(img, (width, new_h), interpolation=cv2.INTER_AREA)
        elif height:
            ratio = height / h
            new_w = int(w * ratio)
            return cv2.resize(img, (new_w, height), interpolation=cv2.INTER_AREA)
        
        return img


if __name__ == "__main__":
    print("Vision Engine Complete - Initialized")
    vision = VisionEngineComplete()
    print("✓ Ready for QR/Barcode, OCR, and Quality checks")