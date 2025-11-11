"""
FINAL QC Vision System - Main Application
Production-ready with live laptop camera integration
"""

import sys
import os
import threading
import time
import base64
from pathlib import Path

# Setup paths
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import core modules
from database import QCDatabase
from config_manager import ConfigManager
from management.vision_engine import VisionEngine
from server.web_server import WebServer
from enhanced_dashboard import EnhancedDashboard


class SystemHandler:
    """Handles system operations"""
    
    def __init__(self):
        print("=" * 70)
        print("🚀 QC Vision System - FINAL Production Version")
        print("=" * 70)
        
        # Initialize configuration
        print("\n⚙️  Loading configuration...")
        self.config = ConfigManager()
        
        # Initialize database
        print("💾 Initializing database...")
        self.db = QCDatabase("data/qc_production.db")
        
        # Initialize vision engine
        print("🔍 Initializing vision engine...")
        self.vision = VisionEngine(self.config.get_vision_config())
        
        # Initialize dashboard state
        self.dashboard = EnhancedDashboard()
        
        # Setup storage
        self._setup_storage()
        
        # Update system status
        self.dashboard.update_system_status('server_running', True)
        self.dashboard.update_system_status('camera_connected', True)
        self.dashboard.update_system_status('vision_engine', 'ready')
        self.dashboard.update_system_status('database', 'connected')
        
        print("✅ System initialized successfully!")
    
    def _setup_storage(self):
        """Create storage directories"""
        dirs = ['data/inspections', 'data/reports', 'data/logs', 'config']
        for d in dirs:
            Path(d).mkdir(parents=True, exist_ok=True)
    
    def get_dashboard_state(self):
        """Get current dashboard state"""
        return {
            'statistics': self.dashboard.statistics,
            'system_status': self.dashboard.system_status,
            'recent_inspections': self.dashboard.recent_inspections[:10],
            'current_inspection': self.dashboard.current_inspection
        }
    
    def process_capture(self, image_base64: str, mode: str, roi: dict = None) -> dict:
        """
        Process captured image with ROI support
        Args:
            image_base64: Base64 encoded image
            mode: 'capture', 'qr', 'ocr', or 'color'
            roi: Optional ROI definition {type, coords}
        """
        try:
            # Decode image
            image_bytes = base64.b64decode(image_base64)
            img = self.vision.load_image_from_bytes(image_bytes)
            
            if img is None:
                return {'error': 'invalid_image'}
            
            result = {}
            
            if mode == 'qr':
                # QR detection with ROI
                qr_codes = self.vision.detect_qr_codes(img, roi)
                result = {
                    'mode': 'qr',
                    'qr_codes': qr_codes,
                    'count': len(qr_codes)
                }
                
                # Save to database
                if qr_codes:
                    timestamp = int(time.time())
                    filename = f"qr_{timestamp}.jpg"
                    image_path = Path('data/inspections') / filename
                    self.vision.save_image(img, str(image_path))
                    
                    # Save inspection to database
                    inspection_id = self.db.add_inspection(
                        product_id=None,
                        qr_data=qr_codes[0]['data'],
                        status='OK',
                        image_path=str(image_path),
                        station_id='QR-SCANNER'
                    )
                    
                    result['inspection_id'] = inspection_id
                    
                    # Log to dashboard
                    self.dashboard.add_completed_inspection({
                        'inspection_id': inspection_id,
                        'product_code': 'QR-SCAN',
                        'status': 'OK',
                        'qr_data': qr_codes[0]['data'],
                        'qr_success': True
                    })
            
            elif mode == 'ocr':
                # OCR detection only
                ocr_text = self.vision.extract_text_simple(img)
                result = {
                    'mode': 'ocr',
                    'ocr_text': ocr_text,
                    'confidence': 'N/A'
                }
                
                # Log to dashboard
                if ocr_text:
                    self.dashboard.add_completed_inspection({
                        'inspection_id': int(time.time()),
                        'product_code': 'OCR-SCAN',
                        'status': 'OK',
                        'ocr_result': ocr_text[:50],
                        'ocr_success': True
                    })
            
            else:  # mode == 'capture'
                # Full inspection
                quality = self.vision.check_image_quality(img)
                result = {
                    'mode': 'capture',
                    'quality': quality,
                    'blur_score': quality['blur']['blur_score'],
                    'brightness': quality['brightness']['brightness']
                }
                
                # Save image
                timestamp = int(time.time())
                filename = f"insp_{timestamp}.jpg"
                image_path = Path('data/inspections') / filename
                self.vision.save_image(img, str(image_path))
                
                # Save to database
                inspection_id = self.db.add_inspection(
                    product_id=None,
                    status='OK' if quality['acceptable'] else 'NOK',
                    blur_score=quality['blur']['blur_score'],
                    brightness_score=quality['brightness']['brightness'],
                    image_path=str(image_path)
                )
                
                result['inspection_id'] = inspection_id
                
                # Log to dashboard
                self.dashboard.add_completed_inspection({
                    'inspection_id': inspection_id,
                    'product_code': 'MANUAL-CAPTURE',
                    'status': 'OK' if quality['acceptable'] else 'NOK',
                    'blur_score': quality['blur']['blur_score']
                })
            
            return result
        
        except Exception as e:
            print(f"Processing error: {e}")
            return {'error': str(e)}
    
    def get_products(self):
        """Get all products"""
        return self.db.list_products()
    
    def get_inspections(self):
        """Get all inspections"""
        return self.db.get_inspections(limit=100)
    
    def add_product(self, product_data: dict):
        """Add new product"""
        self.db.add_product(
            product_code=product_data['product_code'],
            product_name=product_data['product_name'],
            qr_pattern=product_data.get('qr_pattern'),
            ocr_expected=product_data.get('ocr_expected')
        )
    
    def generate_report(self, format_type: str) -> bytes:
        """Generate report"""
        try:
            from report_generator import ReportGenerator
            generator = ReportGenerator(self.db)
            
            if format_type == 'csv':
                return generator.generate_csv_report().encode('utf-8')
            elif format_type == 'excel':
                return generator.generate_excel_report()
            else:  # pdf
                return generator.generate_pdf_report()
        except Exception as e:
            print(f"Report generation error: {e}")
            return b"Report generation failed"
    
    def stop(self):
        """Cleanup"""
        self.db.close()


def main():
    """Main entry point"""
    
    # Create system handler
    system = SystemHandler()
    
    # Create web server
    web_server = WebServer(host='0.0.0.0', port=8081)
    
    print("\n🌐 Starting web server...")
    server = web_server.start(system.get_dashboard_state(), system)
    
    print("\n" + "=" * 70)
    print("✅ SYSTEM ONLINE")
    print("=" * 70)
    print(f"\n🌐 Open browser: http://localhost:8081/dashboard")
    print("\n📹 Features:")
    print("  • Live laptop camera feed")
    print("  • QR code detection")
    print("  • OCR text recognition")
    print("  • Image quality analysis")
    print("\nPress Ctrl+C to stop")
    print("=" * 70)
    
    try:
        # Run server
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down...")
        web_server.stop()
        system.stop()
        print("✅ System stopped cleanly")


if __name__ == "__main__":
    main()