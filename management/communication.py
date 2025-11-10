"""
QC Vision System - Communication Layer
Handles Pi-Server communication via HTTP
Both client (Pi) and server sides in one module
"""

import json
import socket
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import urllib.request
import urllib.error
from typing import Dict, Any, Callable, Optional
import time
from io import BytesIO
import base64


# ==================== CLIENT SIDE (Raspberry Pi) ====================

class QCClient:
    """
    Client for Raspberry Pi to communicate with server
    Sends images and receives processing results
    """
    
    def __init__(self, server_url: str = "http://localhost:8080", 
                 timeout: int = 30, retry_attempts: int = 3):
        """
        Initialize QC client
        Args:
            server_url: Server base URL
            timeout: Request timeout in seconds
            retry_attempts: Number of retry attempts on failure
        """
        self.server_url = server_url.rstrip('/')
        self.timeout = timeout
        self.retry_attempts = retry_attempts
        self.session_id = self._generate_session_id()
    
    def _generate_session_id(self) -> str:
        """Generate unique session ID for this client"""
        import uuid
        return str(uuid.uuid4())[:8]
    
    def send_image(self, image_data: bytes, metadata: Dict = None) -> Dict:
        """
        Send image to server for processing
        Args:
            image_data: Image as bytes (JPEG/PNG)
            metadata: Additional data (product_code, station_id, etc.)
        Returns: Server response dict
        """
        url = f"{self.server_url}/api/process_image"
        
        # Prepare payload
        payload = {
            'session_id': self.session_id,
            'timestamp': time.time(),
            'image': base64.b64encode(image_data).decode('utf-8'),
            'metadata': metadata or {}
        }
        
        return self._post_json(url, payload)
    
    def send_inspection_result(self, inspection_data: Dict) -> Dict:
        """
        Send inspection result to server
        Args:
            inspection_data: Complete inspection data
        Returns: Server response
        """
        url = f"{self.server_url}/api/inspection"
        return self._post_json(url, inspection_data)
    
    def get_product_config(self, product_code: str) -> Optional[Dict]:
        """
        Get product configuration from server
        Args:
            product_code: Product identifier
        Returns: Product config dict or None
        """
        url = f"{self.server_url}/api/product/{product_code}"
        response = self._get_json(url)
        return response.get('data') if response else None
    
    def ping(self) -> bool:
        """
        Check server availability
        Returns: True if server is reachable
        """
        try:
            url = f"{self.server_url}/api/ping"
            response = self._get_json(url, retry=False)
            return response is not None
        except:
            return False
    
    def get_server_status(self) -> Dict:
        """Get server status and statistics"""
        url = f"{self.server_url}/api/status"
        return self._get_json(url) or {}
    
    # ==================== HTTP HELPERS ====================
    
    def _post_json(self, url: str, data: Dict) -> Dict:
        """POST JSON data with retry logic"""
        json_data = json.dumps(data).encode('utf-8')
        
        for attempt in range(self.retry_attempts):
            try:
                req = urllib.request.Request(
                    url,
                    data=json_data,
                    headers={
                        'Content-Type': 'application/json',
                        'User-Agent': f'QC-Client/{self.session_id}'
                    },
                    method='POST'
                )
                
                with urllib.request.urlopen(req, timeout=self.timeout) as response:
                    result = json.loads(response.read().decode('utf-8'))
                    return result
            
            except urllib.error.HTTPError as e:
                print(f"✗ HTTP Error {e.code}: {e.reason}")
                if attempt < self.retry_attempts - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    return {'error': f'HTTP {e.code}', 'message': str(e.reason)}
            
            except urllib.error.URLError as e:
                print(f"✗ Connection error: {e.reason}")
                if attempt < self.retry_attempts - 1:
                    time.sleep(2 ** attempt)
                else:
                    return {'error': 'connection_failed', 'message': str(e.reason)}
            
            except Exception as e:
                print(f"✗ Unexpected error: {e}")
                return {'error': 'unknown', 'message': str(e)}
        
        return {'error': 'max_retries', 'message': 'Failed after all attempts'}
    
    def _get_json(self, url: str, retry: bool = True) -> Optional[Dict]:
        """GET JSON data"""
        attempts = self.retry_attempts if retry else 1
        
        for attempt in range(attempts):
            try:
                req = urllib.request.Request(
                    url,
                    headers={'User-Agent': f'QC-Client/{self.session_id}'}
                )
                
                with urllib.request.urlopen(req, timeout=self.timeout) as response:
                    return json.loads(response.read().decode('utf-8'))
            
            except Exception as e:
                if attempt < attempts - 1:
                    time.sleep(1)
                else:
                    print(f"✗ GET failed: {e}")
                    return None
        
        return None


# ==================== SERVER SIDE (Windows) ====================

class QCRequestHandler(BaseHTTPRequestHandler):
    """HTTP request handler for QC server"""
    
    # Class variable to store callback functions
    handlers = {}
    
    def log_message(self, format, *args):
        """Override to customize logging"""
        print(f"[{self.client_address[0]}] {format % args}")
    
    def _send_json(self, data: Dict, status: int = 200):
        """Send JSON response"""
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))
    
    def _read_json(self) -> Optional[Dict]:
        """Read JSON from request body"""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            return json.loads(body.decode('utf-8'))
        except Exception as e:
            print(f"✗ Error reading JSON: {e}")
            return None
    
    def do_GET(self):
        """Handle GET requests"""
        parsed = urlparse(self.path)
        path = parsed.path
        
        # Route to appropriate handler
        if path == '/api/ping':
            self._handle_ping()
        
        elif path == '/api/status':
            self._handle_status()
        
        elif path.startswith('/api/product/'):
            product_code = path.split('/')[-1]
            self._handle_get_product(product_code)
        
        else:
            self._send_json({'error': 'not_found'}, 404)
    
    def do_POST(self):
        """Handle POST requests"""
        parsed = urlparse(self.path)
        path = parsed.path
        
        if path == '/api/process_image':
            self._handle_process_image()
        
        elif path == '/api/inspection':
            self._handle_inspection()
        
        else:
            self._send_json({'error': 'not_found'}, 404)
    
    def do_OPTIONS(self):
        """Handle OPTIONS for CORS"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    # ==================== ENDPOINT HANDLERS ====================
    
    def _handle_ping(self):
        """Handle ping request"""
        self._send_json({
            'status': 'ok',
            'timestamp': time.time(),
            'server': 'QC-Vision-Server'
        })
    
    def _handle_status(self):
        """Handle status request"""
        handler = self.handlers.get('status')
        if handler:
            status_data = handler()
            self._send_json(status_data)
        else:
            self._send_json({
                'status': 'running',
                'timestamp': time.time()
            })
    
    def _handle_get_product(self, product_code: str):
        """Handle get product config"""
        handler = self.handlers.get('get_product')
        if handler:
            product = handler(product_code)
            if product:
                self._send_json({'status': 'ok', 'data': product})
            else:
                self._send_json({'error': 'not_found'}, 404)
        else:
            self._send_json({'error': 'not_implemented'}, 501)
    
    def _handle_process_image(self):
        """Handle image processing request"""
        data = self._read_json()
        if not data:
            self._send_json({'error': 'invalid_json'}, 400)
            return
        
        # Extract image
        try:
            image_base64 = data.get('image', '')
            image_bytes = base64.b64decode(image_base64)
            metadata = data.get('metadata', {})
            
            # Call handler if registered
            handler = self.handlers.get('process_image')
            if handler:
                result = handler(image_bytes, metadata)
                self._send_json({'status': 'ok', 'result': result})
            else:
                self._send_json({
                    'status': 'ok',
                    'message': 'Image received',
                    'size': len(image_bytes),
                    'metadata': metadata
                })
        
        except Exception as e:
            self._send_json({'error': 'processing_failed', 'message': str(e)}, 500)
    
    def _handle_inspection(self):
        """Handle inspection result submission"""
        data = self._read_json()
        if not data:
            self._send_json({'error': 'invalid_json'}, 400)
            return
        
        handler = self.handlers.get('inspection')
        if handler:
            result = handler(data)
            self._send_json({'status': 'ok', 'result': result})
        else:
            self._send_json({'status': 'ok', 'message': 'Inspection received'})


class QCServer:
    """
    HTTP server for QC system
    Receives images from Pi and serves web interface
    """
    
    def __init__(self, host: str = '0.0.0.0', port: int = 8080):
        """
        Initialize QC server
        Args:
            host: Server host (0.0.0.0 for all interfaces)
            port: Server port
        """
        self.host = host
        self.port = port
        self.server = None
        self.server_thread = None
        self.running = False
        
        # Statistics
        self.stats = {
            'start_time': None,
            'requests_received': 0,
            'images_processed': 0,
            'errors': 0
        }
    
    def register_handler(self, endpoint: str, callback: Callable):
        """
        Register callback for specific endpoint
        Args:
            endpoint: 'process_image', 'inspection', 'get_product', 'status'
            callback: Function to handle the request
        """
        QCRequestHandler.handlers[endpoint] = callback
        print(f"✓ Registered handler for: {endpoint}")
    
    def start(self, blocking: bool = False):
        """
        Start the server
        Args:
            blocking: If True, blocks until server stops
        """
        try:
            self.server = HTTPServer((self.host, self.port), QCRequestHandler)
            self.stats['start_time'] = time.time()
            self.running = True
            
            print(f"✓ QC Server started on http://{self.host}:{self.port}")
            
            if blocking:
                self.server.serve_forever()
            else:
                self.server_thread = threading.Thread(
                    target=self.server.serve_forever,
                    daemon=True
                )
                self.server_thread.start()
                print("✓ Server running in background thread")
        
        except OSError as e:
            print(f"✗ Failed to start server: {e}")
            if "Address already in use" in str(e):
                print(f"  Port {self.port} is already in use. Try a different port.")
            raise
    
    def stop(self):
        """Stop the server"""
        if self.server:
            self.running = False
            self.server.shutdown()
            self.server.server_close()
            print("✓ Server stopped")
    
    def get_stats(self) -> Dict:
        """Get server statistics"""
        uptime = time.time() - self.stats['start_time'] if self.stats['start_time'] else 0
        return {
            **self.stats,
            'uptime_seconds': round(uptime, 2),
            'running': self.running
        }
    
    def __enter__(self):
        """Context manager entry"""
        self.start(blocking=False)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.stop()


# ==================== UTILITY FUNCTIONS ====================

def find_available_port(start_port: int = 8080, max_attempts: int = 100) -> int:
    """Find available port starting from start_port"""
    for port in range(start_port, start_port + max_attempts):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('', port))
                return port
        except OSError:
            continue
    raise RuntimeError(f"No available ports found in range {start_port}-{start_port+max_attempts}")


# ==================== TEST/DEMO ====================

if __name__ == "__main__":
    print("=" * 60)
    print("Communication Layer - Test")
    print("=" * 60)
    
    # Test 1: Start server
    print("\n🌐 Starting server...")
    
    def handle_process_image(image_bytes: bytes, metadata: Dict) -> Dict:
        """Example image processing handler"""
        print(f"   📸 Received image: {len(image_bytes)} bytes")
        print(f"   📋 Metadata: {metadata}")
        return {
            'processed': True,
            'image_size': len(image_bytes),
            'status': 'OK'
        }
    
    def handle_status() -> Dict:
        """Example status handler"""
        return {
            'status': 'running',
            'version': '1.0',
            'uptime': 123.45
        }
    
    # Start server
    server = QCServer(host='localhost', port=8080)
    server.register_handler('process_image', handle_process_image)
    server.register_handler('status', handle_status)
    server.start(blocking=False)
    
    # Wait for server to start
    time.sleep(1)
    
    # Test 2: Client communication
    print("\n📡 Testing client...")
    client = QCClient(server_url="http://localhost:8080")
    
    # Ping test
    print("\n   Testing ping...")
    if client.ping():
        print("   ✓ Server is reachable")
    else:
        print("   ✗ Server not reachable")
    
    # Status test
    print("\n   Testing status...")
    status = client.get_server_status()
    print(f"   Status: {status}")
    
    # Image send test
    print("\n   Testing image send...")
    test_image = b"fake_image_data_12345"
    metadata = {
        'product_code': 'TEST-001',
        'station_id': 'STATION-1',
        'operator': 'test_user'
    }
    
    response = client.send_image(test_image, metadata)
    print(f"   Response: {response}")
    
    # Test 3: Server stats
    print("\n📊 Server statistics:")
    stats = server.get_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    # Cleanup
    print("\n🛑 Stopping server...")
    server.stop()
    
    print("\n✓ Communication layer test complete!")
    print("\nUsage examples:")
    print("  # Server side:")
    print("  server = QCServer('0.0.0.0', 8080)")
    print("  server.register_handler('process_image', my_handler)")
    print("  server.start()")
    print()
    print("  # Client side (Pi):")
    print("  client = QCClient('http://192.168.1.100:8080')")
    print("  response = client.send_image(image_data, metadata)")