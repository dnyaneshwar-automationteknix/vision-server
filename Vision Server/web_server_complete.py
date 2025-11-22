"""
Complete Web Server with All Features
Handles: Dashboard, Color Detection, QR/OCR, Inspections, Configuration
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import base64
import cv2
import numpy as np
from typing import Dict
from urllib.parse import urlparse
import os


class CompleteWebHandler(BaseHTTPRequestHandler):
    """Complete HTTP Request Handler"""
    
    # Class-level shared state
    dashboard_state = None
    system_handler = None
    
    def log_message(self, format, *args):
        """Suppress request logs"""
        pass
    
    def _set_headers(self, content_type='text/html', status=200):
        """Set response headers"""
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Cache-Control', 'no-cache')
        self.end_headers()
    
    def _send_json(self, data: dict, status=200):
        """Send JSON response"""
        self._set_headers('application/json', status)
        self.wfile.write(json.dumps(data, default=str).encode('utf-8'))
    
    def _send_html(self, html: str):
        """Send HTML response"""
        self._set_headers('text/html')
        self.wfile.write(html.encode('utf-8'))
    
    def do_OPTIONS(self):
        """Handle CORS preflight"""
        self._set_headers()
    
    def do_GET(self):
        """Handle GET requests"""
        parsed = urlparse(self.path)
        path = parsed.path
        
        if path == '/' or path == '/dashboard':
            self._serve_dashboard()
        elif path == '/color-detection':
            self._serve_color_detection_page()
        elif path == '/interactive' or path == '/interactive_camera.html':
            # Serve an alternative interactive UI if present in repo root
            print("Serving interactive camera page...")
            try:
                base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                print("Base path:", base_path)
                alt = os.path.join(base_path, 'interactive_camera.html')
                alt2 = os.path.join(base_path, 'interactive_camera.html')
                if os.path.exists(alt):
                    with open(alt, 'r', encoding='utf-8') as f:
                        html = f.read()
                    self._send_html(html)
                    return
                if os.path.exists(alt2):
                    with open(alt2, 'r', encoding='utf-8') as f:
                        html = f.read()
                    self._send_html(html)
                    return
            except Exception:
                pass
        elif path == '/inspections':
            self._serve_inspections_page()
        elif path == '/configuration':
            self._serve_configuration_page()
        elif path == '/reports':
            self._serve_reports_page()
        elif path.startswith('/inspection/'):
            self._serve_inspection_detail(path)
        elif path == '/api/state':
            self._send_json(self.dashboard_state or {})
        elif path == '/api/models':
            self._handle_get_models()
        else:
            self._send_json({'error': 'Not found'}, 404)
    
    def do_POST(self):
        """Handle POST requests"""
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)
        
        try:
            data = json.loads(body.decode('utf-8'))
        except:
            self._send_json({'error': 'Invalid JSON'}, 400)
            return
        
        path = self.path
        
        if path == '/api/analyze-complete':
            self._handle_complete_analysis(data)
        elif path == '/api/save-box':
            self._handle_save_box(data)
        elif path == '/api/save-ring':
            self._handle_save_ring(data)
        elif path == '/api/get-boxes':
            self._handle_get_boxes(data)
        elif path == '/api/get-rings':
            self._handle_get_rings(data)
        else:
            self._send_json({'error': 'Endpoint not found'}, 404)
    
    # ==================== PAGE RENDERING ====================
    
    def _serve_dashboard(self):
        """Serve main dashboard"""
        from dashboard_ui import DashboardUI
        html = DashboardUI.generate_dashboard_page(self.dashboard_state or {})
        self._send_html(html)
    
    def _serve_color_detection_page(self):
        """Serve color detection page"""
        # Prefer the Python-generated UI to avoid relying on static HTML files
        try:
            from dashboard_ui import DashboardUI
            html = DashboardUI.generate_color_detection_page()
            self._send_html(html)
            return
        except Exception:
            pass

        # If generator not available, fall back to shipped interactive HTML if present
        try:
            base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            alt = os.path.join(base_path, 'interactive_camera.html')
            if os.path.exists(alt):
                with open(alt, 'r', encoding='utf-8') as f:
                    html = f.read()
                self._send_html(html)
                return
        except Exception:
            pass

        self._send_html('<h3>Color detection UI not available</h3>')
    
    def _serve_inspections_page(self):
        """Serve inspections list page"""
        from dashboard_ui import DashboardUI
        inspections = []
        if self.system_handler:
            try:
                inspections = self.system_handler.dashboard.recent_inspections
            except:
                pass
        html = DashboardUI.generate_inspections_page(inspections)
        self._send_html(html)
    
    def _serve_configuration_page(self):
        """Serve configuration page"""
        from dashboard_ui import DashboardUI
        html = DashboardUI.generate_configuration_page()
        self._send_html(html)
    
    def _serve_reports_page(self):
        """Serve reports page"""
        from dashboard_ui import DashboardUI
        stats = self.dashboard_state.get('statistics', {}) if self.dashboard_state else {}
        html = DashboardUI.generate_reports_page(stats)
        self._send_html(html)
    
    def _serve_inspection_detail(self, path):
        """Serve inspection detail page"""
        try:
            inspection_id = int(path.split('/')[-1])
            inspection = None
            
            if self.system_handler:
                inspection = self.system_handler.get_inspection(inspection_id)
            
            if not inspection:
                self._send_json({'error': 'Inspection not found'}, 404)
                return
            
            from dashboard_ui import DashboardUI
            html = DashboardUI.generate_inspection_detail_page(inspection)
            self._send_html(html)
            
        except Exception as e:
            print(f"Inspection detail error: {e}")
            self._send_json({'error': str(e)}, 500)
    
    # ==================== API HANDLERS ====================
    
    def _handle_complete_analysis(self, data: dict):
        """Handle complete analysis request"""
        try:
            if not self.system_handler:
                self._send_json({'error': 'System not ready'}, 500)
                return
            
            # Extract configuration
            config = {
                'detect_qr': data.get('detect_qr', True),
                'detect_ocr': data.get('detect_ocr', True),
                'detect_colors': data.get('detect_colors', True),
                'detect_quality': data.get('detect_quality', True),
                'boxes': data.get('boxes', []),
                'rings': data.get('rings', []),
                'roi': data.get('roi'),
                'target_color': data.get('target_color'),
                'tolerance': data.get('tolerance', 30),
                'ratio': data.get('ratio', 1.0),
                'visualize': data.get('visualize', True),
                'product_id': data.get('product_id'),
                'operator_id': data.get('operator_id'),
                'station_id': data.get('station_id', 'WEB')
            }
            
            # Get image
            image_base64 = data.get('image', '')
            if not image_base64:
                self._send_json({'error': 'No image provided'}, 400)
                return
            
            # Remove data URL prefix if present
            if ',' in image_base64:
                image_base64 = image_base64.split(',')[1]
            
            # Perform analysis
            result = self.system_handler.analyze_complete(image_base64, config)
            
            self._send_json({
                'success': True,
                'result': result
            })
            
        except Exception as e:
            print(f"Complete analysis error: {e}")
            import traceback
            traceback.print_exc()
            self._send_json({'error': str(e)}, 500)
    
    def _handle_save_box(self, data: dict):
        """Save bounding box configuration"""
        try:
            if not self.system_handler:
                self._send_json({'error': 'System not ready'}, 500)
                return
            
            box = data.get('box', {})
            box_id = self.system_handler.save_box(box)
            
            self._send_json({
                'success': True,
                'box_id': box_id
            })
            
        except Exception as e:
            print(f"Save box error: {e}")
            self._send_json({'error': str(e)}, 500)
    
    def _handle_save_ring(self, data: dict):
        """Save ring configuration"""
        try:
            if not self.system_handler:
                self._send_json({'error': 'System not ready'}, 500)
                return
            
            ring = data.get('ring', {})
            ring_id = self.system_handler.save_ring(ring)
            
            self._send_json({
                'success': True,
                'ring_id': ring_id
            })
            
        except Exception as e:
            print(f"Save ring error: {e}")
            self._send_json({'error': str(e)}, 500)
    
    def _handle_get_boxes(self, data: dict):
        """Get boxes for model"""
        try:
            if not self.system_handler:
                self._send_json({'error': 'System not ready'}, 500)
                return
            
            model_id = data.get('model_id', 'DEFAULT')
            boxes = self.system_handler.get_boxes_for_model(model_id)
            
            self._send_json({
                'success': True,
                'boxes': boxes
            })
            
        except Exception as e:
            print(f"Get boxes error: {e}")
            self._send_json({'error': str(e)}, 500)
    
    def _handle_get_rings(self, data: dict):
        """Get rings for model"""
        try:
            if not self.system_handler:
                self._send_json({'error': 'System not ready'}, 500)
                return
            
            model_id = data.get('model_id', 'DEFAULT')
            rings = self.system_handler.get_rings_for_model(model_id)
            
            self._send_json({
                'success': True,
                'rings': rings
            })
            
        except Exception as e:
            print(f"Get rings error: {e}")
            self._send_json({'error': str(e)}, 500)
    
    def _handle_get_models(self):
        """Get available models"""
        try:
            # Return default models
            models = ['DEFAULT', 'MODEL_A', 'MODEL_B']
            self._send_json({
                'success': True,
                'models': models
            })
        except Exception as e:
            self._send_json({'error': str(e)}, 500)


class WebServerComplete:
    """Web server wrapper"""
    
    def __init__(self, host='0.0.0.0', port=8081):
        self.host = host
        self.port = port
        self.server = None
    
    def start(self, dashboard_state, system_handler):
        """Start web server"""
        CompleteWebHandler.dashboard_state = dashboard_state
        CompleteWebHandler.system_handler = system_handler
        
        self.server = HTTPServer((self.host, self.port), CompleteWebHandler)
        print(f"✓ Web server: http://localhost:{self.port}/dashboard")
        return self.server
    
    def stop(self):
        """Stop server"""
        if self.server:
            self.server.shutdown()
            self.server.server_close()


if __name__ == "__main__":
    print("Complete Web Server - Ready")