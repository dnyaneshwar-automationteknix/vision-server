"""
FINAL Web Server with Live Camera Integration
Handles web interface with real-time laptop camera feed
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import base64
from urllib.parse import urlparse, parse_qs
from datetime import datetime
from typing import Dict, List, Optional
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class WebRequestHandler(BaseHTTPRequestHandler):
    """Handle HTTP requests for web interface"""
    
    # Class variables set by main application
    dashboard_state = None
    system_handler = None
    
    def log_message(self, format, *args):
        """Suppress request logs"""
        pass
    
    def do_GET(self):
        """Handle GET requests"""
        parsed = urlparse(self.path)
        path = parsed.path
        
        if path == '/' or path == '/dashboard':
            self._serve_dashboard()
        elif path == '/products':
            self._serve_products()
        elif path == '/inspections':
            self._serve_inspections()
        elif path == '/reports':
            self._serve_reports()
        elif path == '/settings':
            self._serve_settings()
        elif path.startswith('/api/capture'):
            self._handle_capture()
        elif path == '/api/state':
            self._serve_json(self.dashboard_state or {})
        else:
            self.send_error(404)
    
    def do_POST(self):
        """Handle POST requests"""
        parsed = urlparse(self.path)
        path = parsed.path

        try:
            if path == '/api/capture':
                self._handle_capture()
                return

            elif path == '/api/state':
                self._serve_json(self.dashboard_state or {})
                return

            else:
                self.send_error(404)
                return

        except Exception as e:
            print(f"POST error: {e}")
            self.send_error(500, str(e))

    
    # ==================== PAGE RENDERING ====================
    
    def _serve_dashboard(self):
        """Serve main dashboard with live camera"""
        state = self.dashboard_state or {}
        stats = state.get('statistics', {'total': 0, 'ok': 0, 'nok': 0, 'pass_rate': 0.0})
        
        html = self._generate_base_template(f'''
        <!-- Statistics -->
        <div class="grid-4">
            <div class="stat-card ok">
                <div class="stat-value">{stats.get('ok', 0)}</div>
                <div class="stat-label">✓ OK</div>
            </div>
            <div class="stat-card nok">
                <div class="stat-value">{stats.get('nok', 0)}</div>
                <div class="stat-label">✗ NOK</div>
            </div>
            <div class="stat-card total">
                <div class="stat-value">{stats.get('total', 0)}</div>
                <div class="stat-label">Total</div>
            </div>
            <div class="stat-card rate">
                <div class="stat-value">{stats.get('pass_rate', 0):.1f}%</div>
                <div class="stat-label">Pass Rate</div>
            </div>
        </div>
        
        <!-- Mode Selection -->
        <div class="card">
            <div class="card-header">
                🎯 Processing Mode
                <select id="processingMode" class="mode-select" onchange="changeMode(this.value)">
                    <option value="live">Live Feed Only</option>
                    <option value="qr">QR Code Detection</option>
                    <option value="ocr">OCR Text Recognition</option>
                </select>
            </div>
        </div>
        
        <!-- Live Feed Mode -->
        <div id="liveFeedMode" class="mode-container">
            <div class="grid-2">
                <div class="card">
                    <div class="card-header">
                        📹 Live Camera
                        <button class="btn btn-primary" onclick="captureImage()">📸 Capture</button>
                    </div>
                    <div class="video-container">
                        <video id="liveVideo" autoplay playsinline></video>
                        <canvas id="overlayCanvas"></canvas>
                    </div>
                </div>
                
                <div class="card">
                    <div class="card-header">📸 Captured Image</div>
                    <div class="result-container">
                        <img id="capturedImage" src="" alt="No capture yet" />
                        <div id="captureStatus">Waiting for capture...</div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- QR Mode -->
        <div id="qrMode" class="mode-container" style="display:none;">
            <div class="grid-2">
                <div class="card">
                    <div class="card-header">
                        📹 QR Code Scanner
                        <button class="btn btn-success" onclick="toggleQRScanner()">🔍 Start/Stop Scan</button>
                    </div>
                    <div class="video-container">
                        <video id="qrVideo" autoplay playsinline></video>
                        <div id="qrOverlay"></div>
                    </div>
                </div>
                
                <div class="card">
                    <div class="card-header">✅ QR Results</div>
                    <div class="result-container">
                        <div id="qrResults">
                            <div class="result-placeholder">No QR code detected</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- OCR Mode -->
        <div id="ocrMode" class="mode-container" style="display:none;">
            <div class="grid-2">
                <div class="card">
                    <div class="card-header">
                        📹 OCR Scanner
                        <button class="btn btn-success" onclick="processOCR()">🔤 Extract Text</button>
                    </div>
                    <div class="video-container">
                        <video id="ocrVideo" autoplay playsinline></video>
                    </div>
                </div>
                
                <div class="card">
                    <div class="card-header">📝 OCR Results</div>
                    <div class="result-container">
                        <div id="ocrResults">
                            <div class="result-placeholder">No text detected</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Recent Inspections -->
        <div class="card">
            <div class="card-header">📋 Recent Inspections</div>
            {self._generate_inspections_table(state.get('recent_inspections', []))}
        </div>
        
        <script>
            let currentMode = 'live';
            let stream = null;
            
            // Initialize camera
            async function initCamera() {{
                try {{
                    stream = await navigator.mediaDevices.getUserMedia({{ 
                        video: {{ width: 1280, height: 720 }} 
                    }});
                    
                    document.getElementById('liveVideo').srcObject = stream;
                    document.getElementById('qrVideo').srcObject = stream;
                    document.getElementById('ocrVideo').srcObject = stream;
                    
                    console.log('✓ Camera initialized');
                }} catch (err) {{
                    alert('Camera access denied: ' + err.message);
                }}
            }}
            
            // Change processing mode
            function changeMode(mode) {{
                currentMode = mode;
                
                document.getElementById('liveFeedMode').style.display = 'none';
                document.getElementById('qrMode').style.display = 'none';
                document.getElementById('ocrMode').style.display = 'none';
                
                if (mode === 'live') {{
                    document.getElementById('liveFeedMode').style.display = 'block';
                }} else if (mode === 'qr') {{
                    document.getElementById('qrMode').style.display = 'block';
                }} else if (mode === 'ocr') {{
                    document.getElementById('ocrMode').style.display = 'block';
                }}
            }}
            
            // Capture image from live feed
            async function captureImage() {{
                const video = document.getElementById('liveVideo');
                const canvas = document.createElement('canvas');
                canvas.width = video.videoWidth;
                canvas.height = video.videoHeight;
                canvas.getContext('2d').drawImage(video, 0, 0);
                
                const dataURL = canvas.toDataURL('image/jpeg', 0.9);
                document.getElementById('capturedImage').src = dataURL;
                document.getElementById('captureStatus').textContent = 'Captured at ' + new Date().toLocaleTimeString();
                
                try {{
                    const response = await fetch('/api/capture', {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify({{ image: dataURL.split(',')[1], mode: 'capture' }})
                    }});
                    const result = await response.json();
                    console.log('Server response:', result);
                }} catch (err) {{
                    console.error('Upload failed:', err);
                }}
            }}
            
            // --- Continuous QR Scanner ---
            let qrScanRunning = false;
            let qrCooldown = false;
            let lastDetections = [];
            const scanIntervalMs = 150;
            let qrCanvas = document.createElement('canvas');
            
            const qrOverlay = document.getElementById('qrOverlay');
            qrOverlay.style.position = 'absolute';
            qrOverlay.style.top = '0';
            qrOverlay.style.left = '0';
            qrOverlay.style.right = '0';
            qrOverlay.style.bottom = '0';
            qrOverlay.style.pointerEvents = 'none';
            
            const overlayCanvas = document.createElement('canvas');
            overlayCanvas.style.width = '100%';
            overlayCanvas.style.height = '100%';
            overlayCanvas.style.position = 'absolute';
            overlayCanvas.style.top = '0';
            overlayCanvas.style.left = '0';
            overlayCanvas.style.pointerEvents = 'none';
            qrOverlay.appendChild(overlayCanvas);
            const overlayCtx = overlayCanvas.getContext('2d');
            
            let scanLineY = 0;
            let scanDirection = 1;
            
            function resizeOverlayToVideo(video, canvas) {{
                canvas.width = video.videoWidth;
                canvas.height = video.videoHeight;
            }}
            
            async function startQRScanner() {{
                if (qrScanRunning) return;
                const video = document.getElementById('qrVideo');
                resizeOverlayToVideo(video, overlayCanvas);
                qrCanvas.width = Math.max(200, Math.floor(video.videoWidth / 3));
                qrCanvas.height = Math.max(150, Math.floor(video.videoHeight / 3));
                qrScanRunning = true;
                lastDetections = [];
                
                async function scanLoop() {{
                    if (!qrScanRunning) return;
                    overlayCtx.clearRect(0, 0, overlayCanvas.width, overlayCanvas.height);
                    overlayCtx.strokeStyle = 'rgba(0,200,150,0.9)';
                    overlayCtx.lineWidth = 4;
                    const pad = 40;
                    overlayCtx.strokeRect(pad, pad, overlayCanvas.width - pad * 2, overlayCanvas.height - pad * 2);
                    scanLineY += scanDirection * 6;
                    if (scanLineY < pad || scanLineY > overlayCanvas.height - pad) scanDirection *= -1;
                    overlayCtx.beginPath();
                    overlayCtx.moveTo(pad, scanLineY);
                    overlayCtx.lineTo(overlayCanvas.width - pad, scanLineY);
                    overlayCtx.stroke();
                    
                    for (const q of lastDetections) {{
                        if (!q.bbox_norm) continue;
                        const [cx, cy, nw, nh] = q.bbox_norm;
                        const x = (cx - nw / 2) * overlayCanvas.width;
                        const y = (cy - nh / 2) * overlayCanvas.height;
                        const w = nw * overlayCanvas.width;
                        const h = nh * overlayCanvas.height;
                        overlayCtx.strokeStyle = 'rgba(0,255,0,0.9)';
                        overlayCtx.lineWidth = 3;
                        overlayCtx.strokeRect(x, y, w, h);
                        overlayCtx.fillStyle = 'rgba(0,0,0,0.5)';
                        overlayCtx.fillRect(x, y - 28, Math.min(300, w), 24);
                        overlayCtx.fillStyle = 'white';
                        overlayCtx.font = '16px sans-serif';
                        overlayCtx.fillText((q.data || '').slice(0, 30), x + 6, y - 10);
                    }}
                    
                    if (!qrCooldown) {{
                        try {{
                            const ctx = qrCanvas.getContext('2d');
                            ctx.drawImage(video, 0, 0, qrCanvas.width, qrCanvas.height);
                            const dataURL = qrCanvas.toDataURL('image/jpeg', 0.7);
                            qrCooldown = true;
                            fetch('/api/capture', {{
                                method: 'POST',
                                headers: {{ 'Content-Type': 'application/json' }},
                                body: JSON.stringify({{ image: dataURL.split(',')[1], mode: 'qr' }})
                            }}).then(r => r.json()).then(res => {{
                                qrCooldown = false;
                                if (res && res.qr_codes && res.qr_codes.length > 0) {{
                                    lastDetections = res.qr_codes;
                                    let html = '<div class="result-success">';
                                    res.qr_codes.forEach((qr, i) => {{
                                        html += `<div class="result-item"><h3>QR ${'{'}i + 1{'}'}</h3><div class="result-data">${'{'}qr.data{'}'}</div><div class="result-meta">Type: ${'{'}qr.type || 'QR'{'}'}</div></div>`;
                                    }});
                                    html += '</div>';
                                    document.getElementById('qrResults').innerHTML = html;
                                }}
                            }}).catch(e => {{
                                qrCooldown = false;
                                console.error('QR scan post failed', e);
                            }});
                        }} catch (e) {{
                            qrCooldown = false;
                            console.error('QR scan error', e);
                        }}
                    }}
                    setTimeout(scanLoop, scanIntervalMs);
                }}
                scanLoop();
            }}
            
            function toggleQRScanner() {{
                if (!qrScanRunning) {{
                    startQRScanner();
                    document.getElementById('qrResults').innerHTML = '<div class="result-placeholder">Scanning for QR — hold camera steady.</div>';
                    return;
                }}
                qrScanRunning = false;
                lastDetections = [];
                overlayCtx.clearRect(0, 0, overlayCanvas.width, overlayCanvas.height);
                document.getElementById('qrResults').innerHTML = '<div class="result-placeholder">No QR code detected</div>';
            }}
            
            // OCR Process
            async function processOCR() {{
                const video = document.getElementById('ocrVideo');
                const canvas = document.createElement('canvas');
                canvas.width = video.videoWidth;
                canvas.height = video.videoHeight;
                canvas.getContext('2d').drawImage(video, 0, 0);
                
                const dataURL = canvas.toDataURL('image/jpeg', 0.9);
                try {{
                    const response = await fetch('/api/capture', {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify({{ image: dataURL.split(',')[1], mode: 'ocr' }})
                    }});
                    const result = await response.json();
                    if (result.ocr_text) {{
                        document.getElementById('ocrResults').innerHTML = `<div class="result-success"><h3>Extracted Text:</h3><div class="result-data">${'{'}result.ocr_text{'}'}</div><div class="result-meta">Confidence: ${'{'}result.confidence || 'N/A'{'}'}</div></div>`;
                    }} else {{
                        document.getElementById('ocrResults').innerHTML = '<div class="result-error">No text detected</div>';
                    }}
                }} catch (err) {{
                    document.getElementById('ocrResults').innerHTML = '<div class="result-error">Processing failed</div>';
                }}
            }}
            
            window.onload = () => initCamera();
            
            setInterval(() => {{
                fetch('/api/state').then(r => r.json()).then(data => {{
                    if (data.statistics) {{
                        document.querySelector('.stat-card.ok .stat-value').textContent = data.statistics.ok || 0;
                        document.querySelector('.stat-card.nok .stat-value').textContent = data.statistics.nok || 0;
                        document.querySelector('.stat-card.total .stat-value').textContent = data.statistics.total || 0;
                        document.querySelector('.stat-card.rate .stat-value').textContent = (data.statistics.pass_rate || 0).toFixed(1) + '%';
                    }}
                }}).catch(err => console.error('Stats update failed:', err));
            }}, 3000);
        </script>
        
        <style>
            .mode-select {{
                padding: 8px 15px;
                border-radius: 8px;
                background: rgba(255, 255, 255, 0.2);
                border: none;
                color: black;
                font-weight: 600;
                cursor: pointer;
            }}
            .video-container {{ position: relative; background: #000; border-radius: 10px; overflow: hidden; min-height: 400px; }}
            .video-container video {{ width: 100%; height: auto; display: block; }}
            #overlayCanvas, #qrOverlay {{ position: absolute; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none; }}
            .result-container {{ min-height: 400px; display: flex; align-items: center; justify-content: center; background: rgba(0,0,0,0.3); border-radius: 10px; padding: 20px; }}
            #capturedImage {{ max-width: 100%; max-height: 400px; border-radius: 8px; }}
            #captureStatus {{ margin-top: 10px; text-align: center; opacity: 0.8; }}
            .result-placeholder {{ text-align: center; opacity: 0.5; font-size: 18px; }}
            .result-success {{ background: rgba(0,200,81,0.2); padding: 20px; border-radius: 10px; border-left: 4px solid #00c851; }}
            .result-error {{ background: rgba(255,68,68,0.2); padding: 20px; border-radius: 10px; border-left: 4px solid #ff4444; text-align: center; }}
            .result-item {{ margin-bottom: 15px; padding-bottom: 15px; border-bottom: 1px solid rgba(255,255,255,0.2); }}
            .result-item:last-child {{ border-bottom: none; }}
            .result-item h3 {{ margin-bottom: 10px; font-size: 16px; }}
            .result-data {{ font-size: 18px; font-weight: 600; margin: 10px 0; padding: 10px; background: rgba(255,255,255,0.1); border-radius: 5px; word-break: break-all; }}
            .result-meta {{ font-size: 14px; opacity: 0.8; margin-top: 5px; }}
            .stat-card.ok {{ border-left: 4px solid #00c851; }}
            .stat-card.nok {{ border-left: 4px solid #ff4444; }}
            .stat-card.total {{ border-left: 4px solid #33b5e5; }}
            .stat-card.rate {{ border-left: 4px solid #ffbb33; }}
        </style>
        ''', "Dashboard", "dashboard")
        
        self._send_html(html)
    
    def _serve_products(self):
        """Serve products page"""
        products = []
        if self.system_handler:
            products = self.system_handler.get_products()
        
        html = self._generate_products_page(products)
        self._send_html(html)
    
    def _serve_inspections(self):
        """Serve inspections list"""
        inspections = []
        if self.system_handler:
            inspections = self.system_handler.get_inspections()
        
        content = f'''
        <div class="card">
            <div class="card-header">🔬 All Inspections</div>
            {self._generate_inspections_table(inspections)}
        </div>
        '''
        
        html = self._generate_base_template(content, "Inspections", "inspections")
        self._send_html(html)
    
    def _serve_reports(self):
        """Serve reports page"""
        stats = {}
        if self.dashboard_state:
            stats = self.dashboard_state.get('statistics', {})
        
        html = self._generate_reports_page(stats)
        self._send_html(html)
    
    def _serve_settings(self):
        """Serve settings page"""
        html = self._generate_settings_page({})
        self._send_html(html)
    
    # ==================== API HANDLERS ====================
    
    def _handle_capture(self):
        """Handle image capture and processing"""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            data = json.loads(body.decode('utf-8'))
            
            image_base64 = data.get('image', '')
            mode = data.get('mode', 'capture')
            
            if self.system_handler:
                result = self.system_handler.process_capture(image_base64, mode)
                self._serve_json(result)
            else:
                self._serve_json({'error': 'system_not_ready'})
        
        except Exception as e:
            print(f"Capture error: {e}")
            self._serve_json({'error': str(e)}, 500)
    
    def _handle_add_product(self):
        """Handle add product"""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            params = parse_qs(body)
            
            if self.system_handler:
                product_data = {
                    'product_code': params.get('product_code', [''])[0],
                    'product_name': params.get('product_name', [''])[0],
                    'qr_pattern': params.get('qr_pattern', [''])[0],
                    'ocr_expected': params.get('ocr_expected', [''])[0]
                }
                self.system_handler.add_product(product_data)
            
            self.send_response(302)
            self.send_header('Location', '/products')
            self.end_headers()
        except Exception as e:
            print(f"Add product error: {e}")
            self.send_error(500)
    
    def _handle_generate_report(self):
        """Handle report generation"""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            params = parse_qs(body)
            
            format_type = params.get('format', ['csv'])[0]
            
            if self.system_handler:
                report_data = self.system_handler.generate_report(format_type)
                
                if format_type == 'csv':
                    filename = f"qc_report_{datetime.now().strftime('%Y%m%d')}.csv"
                    content_type = 'text/csv'
                elif format_type == 'excel':
                    filename = f"qc_report_{datetime.now().strftime('%Y%m%d')}.xlsx"
                    content_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                else:
                    filename = f"qc_report_{datetime.now().strftime('%Y%m%d')}.pdf"
                    content_type = 'application/pdf'
                
                self.send_response(200)
                self.send_header('Content-Type', content_type)
                self.send_header('Content-Disposition', f'attachment; filename="{filename}"')
                self.send_header('Content-Length', str(len(report_data)))
                self.end_headers()
                self.wfile.write(report_data)
            else:
                self.send_error(500)
        except Exception as e:
            print(f"Report generation error: {e}")
            self.send_error(500)
    
    def _handle_settings(self):
        """Handle settings update"""
        self.send_response(302)
        self.send_header('Location', '/settings')
        self.end_headers()
    
    # ==================== HELPERS ====================
    
    def _send_html(self, html: str):
        """Send HTML response"""
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Cache-Control', 'no-cache')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))
    
    def _serve_json(self, data: dict, status: int = 200):
        """Send JSON response"""
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Cache-Control', 'no-cache')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))
    
    def _generate_base_template(self, content: str, title: str, active: str) -> str:
        """Generate base HTML template - same as enhanced_dashboard.py"""
        # Import from enhanced_dashboard
        try:
            from enhanced_dashboard import UIGenerator
            return UIGenerator.generate_base_template(content, title, active)
        except:
            # Fallback basic template
            return f"<html><body>{content}</body></html>"
    
    def _generate_inspections_table(self, inspections: List[Dict]) -> str:
        """Generate inspections table"""
        try:
            from enhanced_dashboard import UIGenerator
            return UIGenerator._generate_inspections_table(inspections)
        except:
            return "<p>No inspections</p>"
    
    def _generate_products_page(self, products: List[Dict]) -> str:
        """Generate products page"""
        try:
            from enhanced_dashboard import UIGenerator
            return UIGenerator.generate_products_page(products)
        except:
            return "<html><body><p>Products page</p></body></html>"
    
    def _generate_reports_page(self, stats: Dict) -> str:
        """Generate reports page"""
        try:
            from enhanced_dashboard import UIGenerator
            return UIGenerator.generate_reports_page(stats)
        except:
            return "<html><body><p>Reports page</p></body></html>"
    
    def _generate_settings_page(self, config: Dict) -> str:
        """Generate settings page"""
        try:
            from enhanced_dashboard import UIGenerator
            return UIGenerator.generate_settings_page(config)
        except:
            return "<html><body><p>Settings page</p></body></html>"


class WebServer:
    """Web server wrapper"""
    
    def __init__(self, host='0.0.0.0', port=8081):
        self.host = host
        self.port = port
        self.server = None
    
    def start(self, dashboard_state, system_handler):
        """Start web server"""
        WebRequestHandler.dashboard_state = dashboard_state
        WebRequestHandler.system_handler = system_handler
        
        self.server = HTTPServer((self.host, self.port), WebRequestHandler)
        print(f"✓ Web server: http://localhost:{self.port}/dashboard")
        return self.server
    
    def stop(self):
        """Stop server"""
        if self.server:
            self.server.shutdown()
            self.server.server_close()