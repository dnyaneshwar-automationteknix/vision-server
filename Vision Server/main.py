"""
Complete QC Vision System with Enhanced Features
- Multi-camera support (Webcam, PC Camera, Pi Camera, Mock)
- Auto-detection of QR, OCR, Colors, Quality
- Manual ROI drawing (Rectangle, Circle, Polygon, Line, Freehand)
- Proper image saving (Original, Annotated, Thumbnail)
- Camera source tracking in database
"""

import sys
import os
import json
import time
import base64
import uuid
import numpy as np
from pathlib import Path
from datetime import datetime

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import all modules
from database import QCDatabase
from config_manager import ConfigManager
from vision_engine_complete import VisionEngineComplete
from color_detection_engine import ColorDetectionEngine
from web_server_complete import WebServerComplete
from enhanced_dashboard_complete import EnhancedDashboardComplete
from camera_handler import CameraHandler


class QCSystemHandler:
    """
    Enhanced QC System Handler with complete camera and detection support
    """
    
    def __init__(self):
        print("=" * 80)
        print("🚀 QC Vision System - Enhanced Production Version")
        print("   Multi-Camera • Auto-Detection • ROI Tools • Image Storage")
        print("=" * 80)
        
        # Initialize configuration
        print("\n⚙️  Loading configuration...")
        self.config = ConfigManager()
        self.config.ensure_paths()
        
        # Initialize database
        print("💾 Initializing database...")
        self.db = QCDatabase("data/qc_production.db")
        self._create_color_detection_tables()
        
        # Initialize camera
        print("📹 Initializing camera...")
        self.camera = CameraHandler(self.config.get_camera_config())
        self._detect_and_configure_cameras()
        
        # Initialize vision engines
        print("🔍 Initializing vision engines...")
        self.vision = VisionEngineComplete(self.config.get_vision_config())
        self.color_engine = ColorDetectionEngine()
        
        # Initialize dashboard
        print("📊 Initializing dashboard...")
        self.dashboard = EnhancedDashboardComplete()
        
        # Setup storage
        self._setup_storage()
        
        # Update system status
        self.dashboard.update_system_status('server_running', True)
        self.dashboard.update_system_status('camera_connected', self.camera.is_open)
        self.dashboard.update_system_status('vision_engine', 'ready')
        self.dashboard.update_system_status('color_detection', 'ready')
        self.dashboard.update_system_status('database', 'connected')
        
        print("✅ System initialized successfully!")
        print()
    
    def _detect_and_configure_cameras(self):
        """Detect available cameras and configure"""
        available = self.camera.detect_available_cameras()
        
        if not available:
            print("⚠ No cameras detected, using mock mode")
            self.config.set_camera_source('mock')
        
        # Try to open configured camera
        if not self.camera.open():
            print("⚠ Failed to open camera, trying fallback...")
            # Try first available camera
            if available:
                fallback = available[0]
                if fallback['type'] == 'mock':
                    self.config.set_camera_source('mock')
                else:
                    self.config.set_camera_source(fallback['id'])
                    if fallback['device_index'] is not None:
                        self.config.set_camera_device_index(fallback['device_index'])
                
                # Retry with fallback
                self.camera = CameraHandler(self.config.get_camera_config())
                if self.camera.open():
                    print(f"✓ Fallback camera opened: {fallback['name']}")
                else:
                    print("✗ All camera options failed")
    
    def _setup_storage(self):
        """Create storage directories"""
        storage = self.config.get('server', 'storage', {})
        for key in ['image_dir', 'thumbnail_dir', 'annotated_dir']:
            path = storage.get(key)
            if path:
                Path(path).mkdir(parents=True, exist_ok=True)
    
    def _create_color_detection_tables(self):
        """Create database tables for color detection"""
        cursor = self.db.conn.cursor()
        
        # Color detection results table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS color_detections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                inspection_id INTEGER,
                detection_type TEXT,
                detection_id TEXT,
                position INTEGER,
                c1_pixel_count INTEGER,
                c1_percentage REAL,
                c1_min_pitch INTEGER,
                c1_max_pitch INTEGER,
                c2_pixel_count INTEGER,
                c2_percentage REAL,
                c2_min_pitch INTEGER,
                c2_max_pitch INTEGER,
                total_pixels INTEGER,
                verdict TEXT,
                pitch_data TEXT,
                coords_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (inspection_id) REFERENCES inspections(id)
            )
        """)
        
        # Bounding boxes configuration
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bounding_boxes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model_id TEXT,
                position INTEGER,
                left INTEGER,
                right INTEGER,
                top INTEGER,
                bottom INTEGER,
                c1_r_from INTEGER,
                c1_g_from INTEGER,
                c1_b_from INTEGER,
                c1_r_to INTEGER,
                c1_g_to INTEGER,
                c1_b_to INTEGER,
                c2_r_from INTEGER,
                c2_g_from INTEGER,
                c2_b_from INTEGER,
                c2_r_to INTEGER,
                c2_g_to INTEGER,
                c2_b_to INTEGER,
                c1_pixel_count_range INTEGER,
                c2_pixel_count_range INTEGER,
                pixel_range REAL,
                greater_less_than TEXT,
                ok_nok TEXT,
                sync_status INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Rings configuration
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS rings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model_id TEXT,
                position INTEGER,
                center_x INTEGER,
                center_y INTEGER,
                inner_radius INTEGER,
                outer_radius INTEGER,
                portion_count INTEGER,
                r_from INTEGER,
                g_from INTEGER,
                b_from INTEGER,
                r_to INTEGER,
                g_to INTEGER,
                b_to INTEGER,
                model_set_point_from INTEGER,
                model_set_point_to INTEGER,
                zoom_ratio REAL DEFAULT 1.0,
                sync_status INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        self.db.conn.commit()
    
    def get_dashboard_state(self):
        """Get current dashboard state"""
        return {
            'statistics': self.dashboard.statistics,
            'system_status': self.dashboard.system_status,
            'recent_inspections': self.dashboard.recent_inspections[:10],
            'current_inspection': self.dashboard.current_inspection,
            'alerts': self.dashboard.alerts,
            'camera_info': self.camera.get_info() if self.camera else {}
        }
    
    def analyze_complete(self, image_base64: str, config: dict) -> dict:
        """
        Complete analysis pipeline with auto-detection and image saving
        """
        try:
            start_time = time.time()
            
            # Decode image
            image_bytes = base64.b64decode(image_base64)
            img = self.vision.load_image_from_bytes(image_bytes)
            
            if img is None:
                return {'error': 'invalid_image'}
            
            # Get auto-detection settings
            auto_detect = self.config.get('vision', 'auto_detection', {})
            
            results = {
                'timestamp': int(start_time),
                'config': config,
                'auto_detection': auto_detect
            }
            
            # Store original image
            results['original_image_b64'] = base64.b64encode(image_bytes).decode('utf-8')
            
            # 1. Quality Check (always run if auto-detection enabled)
            if auto_detect.get('enabled') and auto_detect.get('detect_quality'):
                quality = self.vision.check_image_quality(img)
                results['quality'] = quality
            
            # 2. QR/Barcode Detection (auto or manual)
            if (auto_detect.get('enabled') and auto_detect.get('detect_qr')) or config.get('detect_qr'):
                roi = config.get('roi')
                qr_codes = self.vision.detect_qr_codes(img, roi)
                results['qr_codes'] = qr_codes
            
            # 3. OCR Detection (auto or manual)
            if (auto_detect.get('enabled') and auto_detect.get('detect_ocr')) or config.get('detect_ocr'):
                roi = config.get('roi')
                ocr_text = self.vision.extract_text_simple(img, roi)
                results['ocr_text'] = ocr_text
            
            # 4. Color Detection (auto or manual)
            if (auto_detect.get('enabled') and auto_detect.get('detect_colors')) or config.get('detect_colors'):
                color_results = {}
                
                # Box-based detection
                boxes = config.get('boxes', [])
                if boxes:
                    ratio = config.get('ratio', 1.0)
                    box_results = self.color_engine.detect_colors_in_boxes(img, boxes, ratio)
                    color_results['boxes'] = box_results
                
                # Ring-based detection
                rings = config.get('rings', [])
                if rings:
                    ring_results = self.color_engine.detect_colors_in_rings(img, rings)
                    color_results['rings'] = ring_results
                
                # ROI-based detection
                if config.get('roi') and config.get('target_color'):
                    try:
                        target = config.get('target_color')
                        tol = int(config.get('tolerance', 30))
                        if isinstance(target, str) and target.startswith('#'):
                            r = int(target[1:3], 16)
                            g = int(target[3:5], 16)
                            b = int(target[5:7], 16)
                            color_ranges = [{
                                'name': 'target',
                                'r_from': max(0, r - tol), 'r_to': min(255, r + tol),
                                'g_from': max(0, g - tol), 'g_to': min(255, g + tol),
                                'b_from': max(0, b - tol), 'b_to': min(255, b + tol)
                            }]
                            roi_result = self.color_engine.detect_colors_in_roi(
                                img, config.get('roi'), color_ranges
                            )
                            color_results['roi'] = roi_result
                    except Exception as e:
                        print(f"ROI color detection error: {e}")
                
                results['colors'] = color_results
            
            # 5. Generate visualization
            if config.get('visualize', True):
                viz_img = self._create_visualization(
                    img, results,
                    config.get('boxes'),
                    config.get('rings'),
                    config.get('roi')
                )
                _, buffer = self.vision.cv2.imencode('.jpg', viz_img, [int(self.vision.cv2.IMWRITE_JPEG_QUALITY), 95])
                results['visualization'] = base64.b64encode(buffer).decode('utf-8')
            
            # 6. Calculate processing time and verdict
            results['processing_time'] = round(time.time() - start_time, 3)
            results['overall_verdict'] = self._calculate_overall_verdict(results)
            
            # 7. Save images to disk
            image_paths = self._save_images(results, config)
            results.update(image_paths)
            
            # 8. Save to database with camera info
            inspection_id = self._save_inspection(results, config, image_paths)
            results['inspection_id'] = inspection_id
            
            # 9. Update dashboard
            self._update_dashboard(results, inspection_id)
            
            return results
            
        except Exception as e:
            print(f"Analysis error: {e}")
            import traceback
            traceback.print_exc()
            return {'error': str(e)}
    
    def _save_images(self, results: dict, config: dict) -> dict:
        """
        Save original, annotated, and thumbnail images
        Returns dict with file paths
        """
        paths = {
            'image_path': None,
            'annotated_path': None,
            'thumbnail_path': None
        }
        
        try:
            storage = self.config.get('server', 'storage', {})
            camera_config = self.config.get_camera_config()
            
            # Generate unique filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_id = uuid.uuid4().hex[:8]
            base_filename = f"inspection_{timestamp}_{unique_id}"
            
            # Save original image
            if camera_config.get('save_images') and results.get('original_image_b64'):
                image_dir = storage.get('image_dir', 'data/inspections/images')
                Path(image_dir).mkdir(parents=True, exist_ok=True)
                
                image_path = os.path.join(image_dir, f"{base_filename}.jpg")
                image_bytes = base64.b64decode(results['original_image_b64'])
                
                with open(image_path, 'wb') as f:
                    f.write(image_bytes)
                
                paths['image_path'] = image_path
                print(f"✓ Saved original image: {image_path}")
            
            # Save annotated image
            if camera_config.get('save_annotated') and results.get('visualization'):
                annotated_dir = storage.get('annotated_dir', 'data/inspections/annotated')
                Path(annotated_dir).mkdir(parents=True, exist_ok=True)
                
                annotated_path = os.path.join(annotated_dir, f"{base_filename}_annotated.jpg")
                viz_bytes = base64.b64decode(results['visualization'])
                
                with open(annotated_path, 'wb') as f:
                    f.write(viz_bytes)
                
                paths['annotated_path'] = annotated_path
                print(f"✓ Saved annotated image: {annotated_path}")
            
            # Save thumbnail
            if camera_config.get('save_thumbnails') and results.get('visualization'):
                thumbnail_dir = storage.get('thumbnail_dir', 'data/inspections/thumbnails')
                Path(thumbnail_dir).mkdir(parents=True, exist_ok=True)
                
                thumbnail_path = os.path.join(thumbnail_dir, f"{base_filename}_thumb.jpg")
                
                # Create thumbnail
                viz_bytes = base64.b64decode(results['visualization'])
                arr = np.frombuffer(viz_bytes, dtype=np.uint8)
                img = self.vision.cv2.imdecode(arr, self.vision.cv2.IMREAD_COLOR)
                
                if img is not None:
                    thumb = self.vision.cv2.resize(img, (320, 240))
                    self.vision.cv2.imwrite(thumbnail_path, thumb, [int(self.vision.cv2.IMWRITE_JPEG_QUALITY), 85])
                    paths['thumbnail_path'] = thumbnail_path
                    print(f"✓ Saved thumbnail: {thumbnail_path}")
            
        except Exception as e:
            print(f"Error saving images: {e}")
        
        return paths
    
    def _create_visualization(self, img, results, boxes=None, rings=None, roi=None):
        """Create visualization overlay"""
        viz = img.copy()
        
        # Draw QR codes
        if 'qr_codes' in results and results['qr_codes']:
            for qr in results['qr_codes']:
                if 'bbox_pixels' in qr:
                    x, y, w, h = qr['bbox_pixels']
                    self.vision.cv2.rectangle(viz, (x, y), (x+w, y+h), (0, 255, 0), 2)
                    self.vision.cv2.putText(viz, qr['data'][:20], (x, y-10),
                                          self.vision.cv2.FONT_HERSHEY_SIMPLEX, 
                                          0.5, (0, 255, 0), 2)
        
        # Draw color detection results
        if 'colors' in results:
            all_color_results = []
            if 'boxes' in results['colors']:
                all_color_results.extend(results['colors']['boxes'])
            if 'rings' in results['colors']:
                all_color_results.extend(results['colors']['rings'])
            
            viz = self.color_engine.draw_results_on_image(viz, boxes, rings, all_color_results)
        
        # Draw ROI
        if roi:
            try:
                rtype = roi.get('type', 'rectangle')
                coords = roi.get('coords', [])
                h, w = viz.shape[:2]
                
                if rtype == 'rectangle' and len(coords) >= 4:
                    x = int(coords[0] * w)
                    y = int(coords[1] * h)
                    ww = int(coords[2] * w)
                    hh = int(coords[3] * h)
                    self.vision.cv2.rectangle(viz, (x, y), (x+ww, y+hh), (255, 255, 0), 2)
                
                elif rtype == 'circle' and len(coords) >= 3:
                    cx = int(coords[0] * w)
                    cy = int(coords[1] * h)
                    rad = int(coords[2] * min(w, h))
                    self.vision.cv2.circle(viz, (cx, cy), rad, (255, 255, 0), 2)
                
                elif rtype in ('polygon', 'freehand') and len(coords) >= 6:
                    pts = []
                    for i in range(0, len(coords), 2):
                        px = int(coords[i] * w)
                        py = int(coords[i+1] * h)
                        pts.append([px, py])
                    pts = np.array([pts], dtype=np.int32)
                    self.vision.cv2.polylines(viz, pts, isClosed=True, color=(255, 255, 0), thickness=2)
                
                elif rtype == 'line' and len(coords) >= 4:
                    x1 = int(coords[0] * w)
                    y1 = int(coords[1] * h)
                    x2 = int(coords[2] * w)
                    y2 = int(coords[3] * h)
                    thickness = max(2, int(0.01 * min(w, h)))
                    self.vision.cv2.line(viz, (x1, y1), (x2, y2), (255, 255, 0), thickness)
            except Exception as e:
                print(f"ROI visualization error: {e}")
        
        return viz
    
    def _save_inspection(self, results: dict, config: dict, image_paths: dict) -> int:
        """Save inspection to database with camera info"""
        try:
            camera_info = self.camera.get_info() if self.camera else {}
            
            inspection_id = self.db.add_inspection(
                product_id=config.get('product_id'),
                operator_id=config.get('operator_id'),
                station_id=config.get('station_id', 'WEB'),
                status=results.get('overall_verdict', 'PENDING'),
                qr_data=results.get('qr_codes', [{}])[0].get('data') if results.get('qr_codes') else None,
                ocr_text=results.get('ocr_text'),
                image_path=image_paths.get('image_path'),
                thumbnail_path=image_paths.get('thumbnail_path'),
                annotated_path=image_paths.get('annotated_path'),
                blur_score=results.get('quality', {}).get('blur', {}).get('blur_score'),
                brightness_score=results.get('quality', {}).get('brightness', {}).get('brightness'),
                processing_time=results.get('processing_time'),
                camera_source=camera_info.get('source', 'unknown'),
                camera_device_index=camera_info.get('device_index', 0)
            )
            
            # Save color detection results
            if 'colors' in results:
                self._save_color_detections(inspection_id, results['colors'])
            
            return inspection_id
            
        except Exception as e:
            print(f"Save inspection error: {e}")
            return -1
    
    def _save_color_detections(self, inspection_id: int, color_results: dict):
        """Save color detection results"""
        cursor = self.db.conn.cursor()
        
        # Save box results
        if 'boxes' in color_results:
            for result in color_results['boxes']:
                cursor.execute("""
                    INSERT INTO color_detections 
                    (inspection_id, detection_type, detection_id, position,
                     c1_pixel_count, c1_percentage, c1_min_pitch, c1_max_pitch,
                     c2_pixel_count, c2_percentage, c2_min_pitch, c2_max_pitch,
                     total_pixels, verdict, pitch_data, coords_data)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    inspection_id, 'box', result.get('box_id'), result.get('position'),
                    result.get('c1_pixel_count'), result.get('c1_percentage'),
                    result.get('c1_min_pitch'), result.get('c1_max_pitch'),
                    result.get('c2_pixel_count'), result.get('c2_percentage'),
                    result.get('c2_min_pitch'), result.get('c2_max_pitch'),
                    result.get('total_pixels'), result.get('verdict'),
                    json.dumps({'c1_pitch_list': result.get('c1_pitch_list', []),
                               'c2_pitch_list': result.get('c2_pitch_list', [])}),
                    json.dumps(result.get('box_coords', {}))
                ))
        
        # Save ring results
        if 'rings' in color_results:
            for result in color_results['rings']:
                cursor.execute("""
                    INSERT INTO color_detections 
                    (inspection_id, detection_type, detection_id, position,
                     c1_pixel_count, c1_percentage, total_pixels, verdict, 
                     pitch_data, coords_data)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    inspection_id, 'ring', result.get('ring_id'), result.get('position'),
                    result.get('total_pixels'), result.get('average_pixels'),
                    result.get('total_pixels'), result.get('verdict'),
                    json.dumps({'portion_pixels': result.get('portion_pixels', [])}),
                    json.dumps(result.get('ring_coords', {}))
                ))
        
        self.db.conn.commit()
    
    def _update_dashboard(self, results: dict, inspection_id: int):
        """Update dashboard with results"""
        self.dashboard.add_completed_inspection({
            'inspection_id': inspection_id,
            'product_code': results.get('config', {}).get('product_id', 'UNKNOWN'),
            'status': results.get('overall_verdict', 'PENDING'),
            'qr_data': results.get('qr_codes', [{}])[0].get('data') if results.get('qr_codes') else None,
            'qr_success': len(results.get('qr_codes', [])) > 0,
            'ocr_result': results.get('ocr_text'),
            'ocr_success': bool(results.get('ocr_text')),
            'blur_score': results.get('quality', {}).get('blur', {}).get('blur_score'),
            'processing_time': results.get('processing_time'),
            'color_detection': results.get('colors') is not None
        })
    
    def _calculate_overall_verdict(self, results: dict) -> str:
        """Calculate overall inspection verdict"""
        verdicts = []
        
        # Quality check
        if 'quality' in results:
            if not results['quality'].get('acceptable', True):
                verdicts.append('NOK')
        
        # Color detection verdicts
        if 'colors' in results:
            if 'boxes' in results['colors']:
                for box_result in results['colors']['boxes']:
                    verdicts.append(box_result.get('verdict', 'PENDING'))
            
            if 'rings' in results['colors']:
                for ring_result in results['colors']['rings']:
                    verdicts.append(ring_result.get('verdict', 'PENDING'))
        
        if not verdicts:
            return 'PENDING'
        
        if 'NOK' in verdicts:
            return 'NOK'
        
        return 'OK'
    
    def get_inspection(self, inspection_id: int) -> dict:
        """Get inspection details"""
        try:
            inspection = self.db.get_inspection(inspection_id)
            if not inspection:
                return None
            
            # Load images if they exist
            if inspection.get('annotated_path') and os.path.exists(inspection['annotated_path']):
                with open(inspection['annotated_path'], 'rb') as f:
                    inspection['image_base64'] = base64.b64encode(f.read()).decode('utf-8')
            
            # Get color detection results
            cursor = self.db.conn.cursor()
            cursor.execute("""
                SELECT * FROM color_detections 
                WHERE inspection_id = ?
                ORDER BY position
            """, (inspection_id,))
            
            inspection['color_detections'] = [dict(row) for row in cursor.fetchall()]
            return inspection
            
        except Exception as e:
            print(f"Get inspection error: {e}")
            return None
    
    def get_boxes_for_model(self, model_id: str) -> list:
        """Get bounding boxes configuration"""
        cursor = self.db.conn.cursor()
        cursor.execute("""
            SELECT * FROM bounding_boxes 
            WHERE model_id = ?
            ORDER BY position
        """, (model_id,))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def get_rings_for_model(self, model_id: str) -> list:
        """Get rings configuration"""
        cursor = self.db.conn.cursor()
        cursor.execute("""
            SELECT * FROM rings 
            WHERE model_id = ?
            ORDER BY position
        """, (model_id,))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def save_box(self, box: dict) -> int:
        """Save bounding box configuration"""
        cursor = self.db.conn.cursor()
        
        if box.get('id'):
            cursor.execute("""
                UPDATE bounding_boxes SET
                    left=?, right=?, top=?, bottom=?,
                    c1_r_from=?, c1_g_from=?, c1_b_from=?,
                    c1_r_to=?, c1_g_to=?, c1_b_to=?,
                    c2_r_from=?, c2_g_from=?, c2_b_from=?,
                    c2_r_to=?, c2_g_to=?, c2_b_to=?,
                    c1_pixel_count_range=?, c2_pixel_count_range=?,
                    pixel_range=?, greater_less_than=?, ok_nok=?
                WHERE id=?
            """, (box['left'], box['right'], box['top'], box['bottom'],
                  box['c1_r_from'], box['c1_g_from'], box['c1_b_from'],
                  box['c1_r_to'], box['c1_g_to'], box['c1_b_to'],
                  box['c2_r_from'], box['c2_g_from'], box['c2_b_from'],
                  box['c2_r_to'], box['c2_g_to'], box['c2_b_to'],
                  box['c1_pixel_count_range'], box['c2_pixel_count_range'],
                  box['pixel_range'], box['greater_less_than'], box['ok_nok']))
            box_id = cursor.lastrowid
        
        self.db.conn.commit()
        return box_id
    
    def save_ring(self, ring: dict) -> int:
        """Save ring configuration"""
        cursor = self.db.conn.cursor()
        
        if ring.get('id'):
            cursor.execute("""
                UPDATE rings SET
                    center_x=?, center_y=?, inner_radius=?, outer_radius=?,
                    portion_count=?, r_from=?, g_from=?, b_from=?,
                    r_to=?, g_to=?, b_to=?,
                    model_set_point_from=?, model_set_point_to=?, zoom_ratio=?
                WHERE id=?
            """, (ring['center_x'], ring['center_y'], 
                  ring['inner_radius'], ring['outer_radius'],
                  ring['portion_count'],
                  ring['r_from'], ring['g_from'], ring['b_from'],
                  ring['r_to'], ring['g_to'], ring['b_to'],
                  ring['model_set_point_from'], ring['model_set_point_to'],
                  ring['zoom_ratio'], ring['id']))
            ring_id = ring['id']
        else:
            cursor.execute("""
                INSERT INTO rings
                (model_id, position, center_x, center_y, 
                 inner_radius, outer_radius, portion_count,
                 r_from, g_from, b_from, r_to, g_to, b_to,
                 model_set_point_from, model_set_point_to, zoom_ratio)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (ring['model_id'], ring['position'],
                  ring['center_x'], ring['center_y'],
                  ring['inner_radius'], ring['outer_radius'], ring['portion_count'],
                  ring['r_from'], ring['g_from'], ring['b_from'],
                  ring['r_to'], ring['g_to'], ring['b_to'],
                  ring['model_set_point_from'], ring['model_set_point_to'],
                  ring['zoom_ratio']))
            ring_id = cursor.lastrowid
        
        self.db.conn.commit()
        return ring_id
    
    def stop(self):
        """Cleanup resources"""
        if self.camera:
            self.camera.close()
        self.db.close()


def main():
    """Main entry point"""
    
    # Create system handler
    system = QCSystemHandler()
    
    # Create and start web server
    web_server = WebServerComplete(host='0.0.0.0', port=8081)
    
    print("🌐 Starting web server...")
    server = web_server.start(system.get_dashboard_state(), system)
    
    print("\n" + "=" * 80)
    print("✅ QC VISION SYSTEM ONLINE - ENHANCED VERSION")
    print("=" * 80)
    print(f"\n🌐 Web Interface:")
    print(f"   Dashboard:        http://localhost:8081/dashboard")
    print(f"   Color Detection:  http://localhost:8081/color-detection")
    print(f"   Interactive UI:   http://localhost:8081/interactive")
    print(f"   Inspections:      http://localhost:8081/inspections")
    print(f"   Reports:          http://localhost:8081/reports")
    
    # Display camera info
    camera_info = system.camera.get_info() if system.camera else {}
    print(f"\n📹 Camera:")
    print(f"   Source: {camera_info.get('source', 'unknown')}")
    print(f"   Type: {camera_info.get('type', 'unknown')}")
    if camera_info.get('device_index') is not None:
        print(f"   Device Index: {camera_info.get('device_index')}")
    print(f"   Status: {'✓ Connected' if camera_info.get('is_open') else '✗ Disconnected'}")
    
    print("\n✨ Features:")
    print("  ✓ Multi-camera support (Webcam, PC Camera, Pi Camera, Mock)")
    print("  ✓ Auto-detection (QR, OCR, Colors, Quality)")
    print("  ✓ Manual ROI drawing (Rectangle, Circle, Polygon, Line, Freehand)")
    print("  ✓ Image saving (Original, Annotated, Thumbnail)")
    print("  ✓ Camera source tracking in database")
    print("  ✓ Real-time dashboard with statistics")
    
    print("\n⚙️  Configuration:")
    print("  To change camera source:")
    print("    - Edit config/camera_config.json")
    print("    - Or use API: POST /api/set-camera")
    
    print("\n💾 Storage:")
    server_config = system.config.get_server_config()
    storage = server_config.get('storage', {})
    print(f"   Images:     {storage.get('image_dir', 'N/A')}")
    print(f"   Thumbnails: {storage.get('thumbnail_dir', 'N/A')}")
    print(f"   Annotated:  {storage.get('annotated_dir', 'N/A')}")
    
    print("\n🔑 Quick Start:")
    print("  1. Open http://localhost:8081/interactive in your browser")
    print("  2. Allow camera access when prompted")
    print("  3. Draw ROI on image (Rectangle/Circle/Polygon/Freehand)")
    print("  4. Click 'Analyze' to run detection")
    print("  5. View results and saved images")
    
    print("\nPress Ctrl+C to stop")
    print("=" * 80 + "\n")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down...")
        web_server.stop()
        system.stop()
        print("✅ System stopped cleanly")


if __name__ == "__main__":
    main()