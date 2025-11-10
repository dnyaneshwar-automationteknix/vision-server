"""
Complete Live QC System
Combines: API Server + Dashboard + Vision + Database
Shows everything working in real-time
"""

import time
import cv2
import numpy as np
from pathlib import Path
import threading
from datetime import datetime

# Import our modules
from database import QCDatabase
from config_manager import ConfigManager
from management.vision_engine import VisionEngine
from management.communication import QCServer, QCClient
from web_dashboard import DashboardServer


class LiveQCSystem:
    """
    Complete live QC system
    Integrates all components with real-time dashboard
    """
    
    def __init__(self, config: ConfigManager = None):
        """Initialize complete system"""
        
        print("=" * 70)
        print("🚀 Starting Live QC Vision System")
        print("=" * 70)
        
        # Load or create config
        self.config = config or ConfigManager()
        self.config.set_mode('both')
        
        # Initialize components
        print("\n📦 Initializing components...")
        
        # Database
        db_path = self.config.get('server', 'database.path', 'live_qc.db')
        self.db = QCDatabase(db_path)
        print(f"  ✓ Database: {db_path}")
        
        # Vision Engine
        self.vision = VisionEngine(self.config.get_vision_config())
        print(f"  ✓ Vision Engine: Ready")
        
        # Dashboard Server (port 8081)
        dash_port = self.config.get('web', 'port', 8081)
        self.dashboard = DashboardServer('0.0.0.0', dash_port)
        
        # API Server (port 8080)
        api_port = self.config.get('server', 'api.port', 8080)
        self.api_server = QCServer('0.0.0.0', api_port)
        
        # Setup storage
        self._setup_storage()
        
        # Register API handlers
        self._register_api_handlers()
        
        print(f"  ✓ API Server: Port {api_port}")
        print(f"  ✓ Dashboard: Port {dash_port}")
        
        # Initialize system status
        self._update_system_status()
    
    def _setup_storage(self):
        """Create storage directories"""
        image_dir = Path(self.config.get('server', 'storage.image_dir', 'inspections/images'))
        thumb_dir = Path(self.config.get('server', 'storage.thumbnail_dir', 'inspections/thumbnails'))
        
        image_dir.mkdir(parents=True, exist_ok=True)
        thumb_dir.mkdir(parents=True, exist_ok=True)
        
        self.image_dir = image_dir
        self.thumb_dir = thumb_dir
    
    def _register_api_handlers(self):
        """Register API endpoint handlers"""
        self.api_server.register_handler('process_image', self.handle_process_image)
        self.api_server.register_handler('get_product', self.handle_get_product)
        self.api_server.register_handler('status', self.handle_get_status)
    
    def _update_system_status(self):
        """Update system status on dashboard"""
        self.dashboard.update_system_status('server_running', True)
        self.dashboard.update_system_status('database', 'connected')
        self.dashboard.update_system_status('vision_engine', 'ready')
        self.dashboard.update_system_status('camera_connected', 
                                           self.config.get('pi', 'enabled', False))
    
    # ==================== API HANDLERS ====================
    
    def handle_process_image(self, image_bytes: bytes, metadata: dict) -> dict:
        """
        Process received image
        Updates dashboard in real-time
        """
        try:
            product_code = metadata.get('product_code', 'UNKNOWN')
            station_id = metadata.get('station_id', 'UNKNOWN')
            
            print(f"\n📸 Processing: {product_code} from {station_id}")
            
            # Update dashboard - show we're processing
            self.dashboard.update_current_inspection({
                'product_code': product_code,
                'status': 'PROCESSING',
                'qr_data': '...',
                'ocr_result': '...',
                'blur_score': 0,
                'station_id': station_id
            })
            
            # Update live feed
            self.dashboard.update_live_image(image_bytes)
            
            # Load image
            img = self.vision.load_image_from_bytes(image_bytes)
            if img is None:
                return {'error': 'invalid_image'}
            
            # Get product config
            product = self.db.get_product(product_code)
            product_config = None
            
            if product:
                product_config = {
                    'qr_pattern': product.get('qr_pattern'),
                    'ocr_expected': product.get('ocr_expected'),
                    'color_ranges': product.get('color_ranges')
                }
            
            # Perform vision inspection
            result = self.vision.inspect_image(img, product_config)
            
            # Update dashboard with results
            self.dashboard.update_current_inspection({
                'product_code': product_code,
                'status': result['overall_status'],
                'qr_data': result.get('qr_data', 'N/A'),
                'ocr_result': result.get('ocr_text', 'N/A')[:30],
                'blur_score': result['processing_steps']['quality']['blur']['blur_score'],
                'station_id': station_id
            })
            
            # Save image
            timestamp = int(time.time() * 1000)
            filename = f"insp_{timestamp}.jpg"
            image_path = self.image_dir / filename
            self.vision.save_image(img, str(image_path))
            
            # Save to database
            inspection_id = self.db.add_inspection(
                product_id=product['product_id'] if product else None,
                qr_data=result.get('qr_data'),
                ocr_result=result.get('ocr_text'),
                color_detected=str(result.get('colors_detected', [])),
                image_path=str(image_path),
                status=result['overall_status'],
                blur_score=result['processing_steps']['quality']['blur']['blur_score'],
                brightness_score=result['processing_steps']['quality']['brightness']['brightness'],
                processing_time=result['processing_time'],
                station_id=station_id
            )
            
            # Log
            self.db.log('INFO', 'api', f"Inspection {inspection_id}: {result['overall_status']}")
            
            # Add to dashboard history
            self.dashboard.add_completed_inspection({
                'inspection_id': inspection_id,
                'product_code': product_code,
                'status': result['overall_status'],
                'formatted_time': datetime.now().strftime("%H:%M:%S"),
                'station_id': station_id
            })
            
            print(f"  ✓ Result: {result['overall_status']}")
            print(f"  ✓ Saved: {inspection_id}")
            
            return {
                'inspection_id': inspection_id,
                'status': result['overall_status'],
                'processing_time': result['processing_time'],
                'quality': {
                    'blur': result['processing_steps']['quality']['blur']['blur_score'],
                    'brightness': result['processing_steps']['quality']['brightness']['brightness']
                }
            }
        
        except Exception as e:
            print(f"  ✗ Error: {e}")
            self.db.log('ERROR', 'api', f'Processing failed: {str(e)}')
            return {'error': 'processing_failed', 'message': str(e)}
    
    def handle_get_product(self, product_code: str) -> dict:
        """Get product configuration"""
        return self.db.get_product(product_code)
    
    def handle_get_status(self) -> dict:
        """Get system status"""
        stats = self.db.get_statistics()
        
        return {
            'status': 'running',
            'uptime': time.time(),
            'statistics': stats,
            'components': {
                'api_server': 'running',
                'dashboard': 'running',
                'database': 'connected',
                'vision_engine': 'ready'
            }
        }
    
    # ==================== SERVER CONTROL ====================
    
    def start(self):
        """Start all servers"""
        print("\n🌐 Starting servers...")
        
        # Start API server
        self.api_server.start(blocking=False)
        api_port = self.config.get('server', 'api.port', 8080)
        print(f"  ✓ API Server: http://localhost:{api_port}")
        
        # Start dashboard
        self.dashboard.start(blocking=False)
        dash_port = self.config.get('web', 'port', 8081)
        print(f"  ✓ Dashboard: http://localhost:{dash_port}/dashboard")
        
        print("\n" + "=" * 70)
        print(f"✅ SYSTEM READY")
        print("=" * 70)
        print(f"\n🌐 Open dashboard: http://localhost:{dash_port}/dashboard")
        print(f"📡 API endpoint: http://localhost:{api_port}/api/process_image")
        print("\nPress Ctrl+C to stop")
        print("=" * 70)
    
    def stop(self):
        """Stop all servers"""
        print("\n\n🛑 Shutting down...")
        
        self.api_server.stop()
        self.dashboard.stop()
        self.db.close()
        
        print("✓ System stopped")
    
    def run(self, with_simulator: bool = True):
        """
        Run complete system
        Args:
            with_simulator: Start inspection simulator
        """
        self.start()
        
        if with_simulator:
            # Start simulator in separate thread
            simulator_thread = threading.Thread(
                target=self._run_simulator,
                daemon=True
            )
            simulator_thread.start()
        
        try:
            # Keep running
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()
    
    # ==================== SIMULATOR ====================
    
    def _run_simulator(self):
        """
        Simulate inspections for demo
        Creates fake images and sends them through the system
        """
        print("\n🎬 Simulator started (generating test inspections)")
        
        # Wait for servers to fully start
        time.sleep(2)
        
        # Create client
        api_port = self.config.get('server', 'api.port', 8080)
        client = QCClient(f'http://localhost:{api_port}')
        
        inspection_count = 0
        
        while True:
            try:
                time.sleep(5)  # 5 seconds between inspections
                
                inspection_count += 1
                
                # Create test image
                img = self._generate_test_image(inspection_count)
                
                # Encode image
                success, buffer = cv2.imencode('.jpg', img)
                if not success:
                    continue
                
                image_bytes = buffer.tobytes()
                
                # Send to API
                metadata = {
                    'product_code': f'WIDGET-{(inspection_count % 3) + 1:03d}',
                    'station_id': 'SIMULATOR',
                    'operator': 'auto',
                    'timestamp': time.time()
                }
                
                response = client.send_image(image_bytes, metadata)
                
                if 'error' not in response:
                    print(f"  🤖 Simulated inspection #{inspection_count}: {response.get('status')}")
                
            except Exception as e:
                print(f"  ⚠️ Simulator error: {e}")
                time.sleep(5)
    
    def _generate_test_image(self, count: int) -> np.ndarray:
        """Generate test image with various features"""
        
        # Create base image
        img = np.random.randint(80, 150, (480, 640, 3), dtype=np.uint8)
        
        # Add colored region (simulates product)
        colors = [
            (0, 0, 200),    # Red
            (0, 200, 0),    # Green
            (200, 0, 0)     # Blue
        ]
        color = colors[count % 3]
        cv2.rectangle(img, (150, 150), (490, 330), color, -1)
        
        # Add text (simulates OCR target)
        cv2.putText(img, f"LOT2024-{count:04d}", (180, 240),
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        
        # Add inspection number
        cv2.putText(img, f"Inspection #{count}", (200, 400),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        # Add timestamp
        timestamp = datetime.now().strftime("%H:%M:%S")
        cv2.putText(img, timestamp, (450, 460),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
        
        return img


# ==================== SETUP DATABASE WITH PRODUCTS ====================

def setup_demo_database(db_path: str = 'live_qc.db'):
    """Setup database with demo products"""
    
    print("\n💾 Setting up database...")
    db = QCDatabase(db_path)
    
    # Check if products already exist
    existing = db.list_products()
    if existing:
        print(f"  ℹ️  Database already has {len(existing)} products")
        db.close()
        return
    
    # Add demo products
    products = [
        {
            'product_code': 'WIDGET-001',
            'product_name': 'Red Widget',
            'qr_pattern': 'QR-WIDGET-.*',
            'ocr_expected': 'LOT2024',
            'color_ranges': {
                'red': [0, 10, 100, 255, 100, 255]
            }
        },
        {
            'product_code': 'WIDGET-002',
            'product_name': 'Green Widget',
            'qr_pattern': 'QR-WIDGET-.*',
            'ocr_expected': 'LOT2024',
            'color_ranges': {
                'green': [40, 80, 100, 255, 100, 255]
            }
        },
        {
            'product_code': 'WIDGET-003',
            'product_name': 'Blue Widget',
            'qr_pattern': 'QR-WIDGET-.*',
            'ocr_expected': 'LOT2024',
            'color_ranges': {
                'blue': [100, 130, 100, 255, 100, 255]
            }
        }
    ]
    
    for prod in products:
        db.add_product(
            product_code=prod['product_code'],
            product_name=prod['product_name'],
            qr_pattern=prod['qr_pattern'],
            ocr_expected=prod['ocr_expected'],
            color_ranges=prod['color_ranges']
        )
        print(f"  ✓ Added: {prod['product_code']}")
    
    # Add demo users
    db.add_user('operator1', 'hashed_password', 'OPERATOR')
    db.add_user('supervisor1', 'hashed_password', 'SUPERVISOR')
    
    print(f"  ✓ Added 2 users")
    
    db.close()
    print("  ✓ Database ready")


# ==================== MAIN ====================

def main():
    """Main entry point"""
    
    # Setup database
    setup_demo_database()
    
    # Create system
    system = LiveQCSystem()
    
    # Run with simulator
    system.run(with_simulator=True)


if __name__ == "__main__":
    main()