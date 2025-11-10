"""
Enhanced Dashboard with User-Friendly Interface
Complete UI system with navigation, forms, and interactive controls
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import time
import threading
from urllib.parse import urlparse, parse_qs, unquote
import base64
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path
import hashlib


class EnhancedDashboard:
    """Enhanced dashboard with multi-page interface"""
    
    def __init__(self):
        self.current_inspection = None
        self.recent_inspections = []
        self.max_recent = 50
        self.statistics = {'total': 0, 'ok': 0, 'nok': 0, 'pass_rate': 0.0}
        self.system_status = {
            'server_running': True,
            'camera_connected': False,
            'vision_engine': 'ready',
            'database': 'connected'
        }
        self.current_user = None
        self.alerts = []
        self.lock = threading.Lock()
    
    def add_alert(self, message: str, alert_type: str = 'info'):
        """Add system alert"""
        with self.lock:
            self.alerts.insert(0, {
                'message': message,
                'type': alert_type,
                'timestamp': datetime.now().strftime("%H:%M:%S")
            })
            if len(self.alerts) > 10:
                self.alerts = self.alerts[:10]
    
    def update_system_status(self, component: str, status: str):
        """Update system component status"""
        with self.lock:
            self.system_status[component] = status
            self.system_status['last_update'] = time.time()
    
    def update_current_inspection(self, inspection_data: Dict):
        """Update currently processing inspection"""
        with self.lock:
            self.current_inspection = {
                **inspection_data,
                'timestamp': time.time(),
                'formatted_time': datetime.now().strftime("%H:%M:%S")
            }
            self.system_status['last_update'] = time.time()

    def add_completed_inspection(self, inspection: Dict):
        """Add to recent inspections list and update statistics"""
        with self.lock:
            entry = {
                **inspection,
                'timestamp': time.time(),
                'formatted_time': inspection.get('formatted_time') or datetime.now().strftime("%H:%M:%S")
            }
            self.recent_inspections.insert(0, entry)
            if len(self.recent_inspections) > self.max_recent:
                self.recent_inspections = self.recent_inspections[:self.max_recent]

            # Update basic counters
            self.statistics['total'] += 1
            status = inspection.get('status', '').upper()
            if status == 'OK':
                self.statistics['ok'] += 1
            elif status == 'NOK':
                self.statistics['nok'] += 1
            else:
                self.statistics['pending'] += 1

            # Update pass rate
            total = self.statistics['total']
            if total > 0:
                self.statistics['pass_rate'] = (self.statistics['ok'] / total) * 100

            # Vision metrics: blur and processing time
            blur = inspection.get('blur_score')
            if blur is not None:
                # maintain running average
                n = self.statistics.get('total_blur_samples', 0)
                avg = self.statistics.get('avg_blur', 0.0)
                new_n = n + 1
                new_avg = ((avg * n) + float(blur)) / new_n
                self.statistics['avg_blur'] = new_avg
                self.statistics['total_blur_samples'] = new_n

            proc_time = inspection.get('processing_time')
            if proc_time is not None:
                n = self.statistics.get('total_time_samples', 0)
                avg = self.statistics.get('avg_time', 0.0)
                new_n = n + 1
                new_avg = ((avg * n) + float(proc_time)) / new_n
                self.statistics['avg_time'] = new_avg
                self.statistics['total_time_samples'] = new_n

            # QR and OCR success counters
            if inspection.get('qr_success'):
                self.statistics['qr_success_count'] = self.statistics.get('qr_success_count', 0) + 1
            if inspection.get('ocr_success'):
                self.statistics['ocr_success_count'] = self.statistics.get('ocr_success_count', 0) + 1

            self.system_status['last_update'] = time.time()

class UIGenerator:
    """Pure Python HTML/CSS/JS generator for complete UI"""
    
    @staticmethod
    def generate_base_template(content: str, title: str = "QC Vision", 
                              active_page: str = "dashboard") -> str:
        """Generate base HTML template with navigation"""
        return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - QC Vision System</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        :root {{
            --primary: #667eea;
            --primary-dark: #5568d3;
            --secondary: #764ba2;
            --success: #00c851;
            --danger: #ff4444;
            --warning: #ffbb33;
            --info: #33b5e5;
            --dark: #2c3e50;
            --light: #ecf0f1;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
            color: #fff;
            min-height: 100vh;
        }}
        
        /* Navigation */
        .navbar {{
            background: rgba(255, 255, 255, 0.15);
            backdrop-filter: blur(10px);
            padding: 15px 30px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        
        .nav-brand {{
            font-size: 24px;
            font-weight: 700;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        
        .nav-menu {{
            display: flex;
            gap: 5px;
            color: black;
        }}
        
        .nav-item {{
            padding: 10px 20px;
            border-radius: 8px;
            text-decoration: none;
            color: black;
            transition: all 0.3s;
            cursor: pointer;
            font-weight: 500;
        }}
        
        .nav-item:hover {{
            background: rgba(255, 255, 255, 0.2);
        }}
        
        .nav-item.active {{
            background: rgba(255, 255, 255, 0.3);
            font-weight: 600;
        }}
        
        .nav-user {{
            display: flex;
            align-items: center;
            gap: 15px;
        }}
        
        .user-badge {{
            padding: 8px 15px;
            background: rgba(255, 255, 255, 0.2);
            border-radius: 20px;
            font-size: 14px;
        }}
        
        /* Main Container */
        .main-container {{
            padding: 20px;
            max-width: 1600px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 1);
        }}
        
        /* Cards */
        .card {{
           /* background: rgba(255, 255, 255, 0.15); */
            background: rgba(35, 41, 113);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 25px;
            margin-bottom: 20px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
            border: 1px solid rgba(255, 255, 255, 0.2);
        }}
        
        .card-header {{
            font-size: 20px;
            font-weight: 600;
            margin-bottom: 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        
        /* Buttons */
        .btn {{
            padding: 10px 20px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 600;
            transition: all 0.3s;
            text-decoration: none;
            display: inline-block;
        }}
        
        .btn-primary {{
            background: var(--primary);
            color: white;
        }}
        
        .btn-primary:hover {{
            background: var(--primary-dark);
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        }}
        
        .btn-success {{
            background: var(--success);
            color: white;
        }}
        
        .btn-danger {{
            background: var(--danger);
            color: white;
        }}
        
        .btn-warning {{
            background: var(--warning);
            color: white;
        }}
        
        .btn-secondary {{
            background: rgba(255, 255, 255, 0.2);
            color: white;
        }}
        
        /* Forms */
        .form-group {{
            margin-bottom: 20px;
        }}
        
        .form-label {{
            display: block;
            margin-bottom: 8px;
            font-weight: 600;
            font-size: 14px;
        }}
        
        .form-control {{
            width: 100%;
            padding: 12px;
            border: 2px solid rgba(255, 255, 255, 0.3);
            border-radius: 8px;
            background: rgba(255, 255, 255, 0.1);
            color: white;
            font-size: 14px;
        }}
        
        .form-control:focus {{
            outline: none;
            border-color: rgba(255, 255, 255, 0.6);
            background: rgba(255, 255, 255, 0.15);
        }}
        
        .form-control::placeholder {{
            color: rgba(255, 255, 255, 0.5);
        }}
        
        select.form-control {{
            cursor: pointer;
        }}
        
        /* Grid Layouts */
        .grid-2 {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 20px;
        }}
        
        .grid-3 {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 20px;
        }}
        
        .grid-4 {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 20px;
        }}
        
        /* Tables */
        .table {{
            width: 100%;
            border-collapse: collapse;
        }}
        
        .table th {{
            text-align: left;
            padding: 12px;
            background: rgba(255, 255, 255, 0.1);
            font-weight: 600;
            border-bottom: 2px solid rgba(255, 255, 255, 0.2);
        }}
        
        .table td {{
            padding: 12px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }}
        
        .table tr:hover {{
            background: rgba(255, 255, 255, 0.05);
        }}
        
        /* Status Badges */
        .badge {{
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
            display: inline-block;
        }}
        
        .badge-success {{
            background: var(--success);
            color: white;
        }}
        
        .badge-danger {{
            background: var(--danger);
            color: white;
        }}
        
        .badge-warning {{
            background: var(--warning);
            color: white;
        }}
        
        .badge-info {{
            background: var(--info);
            color: white;
        }}
        
        /* Alerts */
        .alert {{
            padding: 15px 20px;
            border-radius: 10px;
            margin-bottom: 15px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        
        .alert-success {{
            background: rgba(0, 200, 81, 0.2);
            border-left: 4px solid var(--success);
        }}
        
        .alert-danger {{
            background: rgba(255, 68, 68, 0.2);
            border-left: 4px solid var(--danger);
        }}
        
        .alert-warning {{
            background: rgba(255, 187, 51, 0.2);
            border-left: 4px solid var(--warning);
        }}
        
        .alert-info {{
            background: rgba(51, 181, 229, 0.2);
            border-left: 4px solid var(--info);
        }}
        
        /* Modal */
        .modal {{
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.7);
            z-index: 1000;
            align-items: center;
            justify-content: center;
        }}
        
        .modal.show {{
            display: flex;
        }}
        
        .modal-content {{
            background: rgba(255, 255, 255, 0.15);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 30px;
            max-width: 600px;
            width: 90%;
            max-height: 90vh;
            overflow-y: auto;
        }}
        
        .modal-header {{
            font-size: 24px;
            font-weight: 600;
            margin-bottom: 20px;
        }}
        
        .modal-close {{
            float: right;
            font-size: 28px;
            cursor: pointer;
            line-height: 20px;
        }}
        
        /* Stats Cards */
        .stat-card {{
            /* background: rgba(255, 255, 255, 0.1); */
            background: rgba(35, 41, 113);
            border-radius: 12px;
            padding: 20px;
            text-align: center;
            margin-bottom: 20px;
        }}
        
        .stat-value {{
            font-size: 36px;
            font-weight: 700;
            margin-bottom: 5px;
        }}
        
        .stat-label {{
            font-size: 14px;
            opacity: 0.8;
        }}
        
        /* Loading Spinner */
        .spinner {{
            border: 3px solid rgba(255, 255, 255, 0.3);
            border-top: 3px solid white;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 20px auto;
        }}
        
        @keyframes spin {{
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}
        
        /* Responsive */
        @media (max-width: 768px) {{
            .grid-2, .grid-3, .grid-4 {{
                grid-template-columns: 1fr;
            }}
            
            .navbar {{
                flex-direction: column;
                gap: 15px;
            }}
            
            .nav-menu {{
                flex-direction: column;
                width: 100%;
                color: black;
            }}
        }}
    </style>
</head>
<body>
    <!-- Navigation -->
    <nav class="navbar">
        <div class="nav-brand">
            <span>🔍</span>
            <span style="color: black;">Vision System</span>
        </div>
        <div class="nav-menu">
            <a href="/dashboard" class="nav-item {'active' if active_page == 'dashboard' else ''}">
                📊 Dashboard
            </a>
            <a href="/inspections" class="nav-item {'active' if active_page == 'inspections' else ''}">
                🔬 Inspections
            </a>
            <a href="/products" class="nav-item {'active' if active_page == 'products' else ''}">
                📦 Products
            </a>
            <a href="/reports" class="nav-item {'active' if active_page == 'reports' else ''}">
                📈 Reports
            </a>
            <a href="/settings" class="nav-item {'active' if active_page == 'settings' else ''}">
                ⚙️ Settings
            </a>
        </div>
        <div class="nav-user">
            <span class="user-badge">👤 Admin</span>
            <button class="btn btn-secondary" onclick="logout()">Logout</button>
        </div>
    </nav>
    
    <!-- Main Content -->
    <div class="main-container">
        {content}
    </div>
    
    <script>
        function logout() {{
            if(confirm('Are you sure you want to logout?')) {{
                window.location.href = '/login';
            }}
        }}
        
        function showModal(modalId) {{
            document.getElementById(modalId).classList.add('show');
        }}
        
        function hideModal(modalId) {{
            document.getElementById(modalId).classList.remove('show');
        }}
        
        function confirmDelete(id, name) {{
            return confirm('Are you sure you want to delete ' + name + '?');
        }}
    </script>
</body>
</html>
"""
    
    @staticmethod
    def generate_dashboard_page(state: Dict) -> str:
        """Generate main dashboard page with live camera and drawing tools"""
        stats = state.get('statistics', {})
        live_image = state.get('live_image')

        content = f"""
        <!-- Quick Stats -->
        <div class="grid-4">
            <div class="stat-card" style="border-left: 4px solid var(--success);">
                <div class="stat-value">{stats.get('ok', 0)}</div>
                <div class="stat-label">OK Inspections</div>
            </div>
            <div class="stat-card" style="border-left: 4px solid var(--danger);">
                <div class="stat-value">{stats.get('nok', 0)}</div>
                <div class="stat-label">NOK Inspections</div>
            </div>
            <div class="stat-card" style="border-left: 4px solid var(--info);">
                <div class="stat-value">{stats.get('total', 0)}</div>
                <div class="stat-label">Total</div>
            </div>
            <div class="stat-card" style="border-left: 4px solid var(--warning);">
                <div class="stat-value">{stats.get('pass_rate', 0):.1f}%</div>
                <div class="stat-label">Pass Rate</div>
            </div>
        </div>

        <!-- Camera Section -->
        <div class="grid-2">
            <div class="card">
                <div class="card-header">
                    🎥 Live Camera Coverage
                    <select id="shapeTool" class="form-control" style="width:150px;display:inline-block;margin-left:10px;">
                        <option value="rect">Rectangle</option>
                        <option value="circle">Circle</option>
                        <option value="dot">Dot</option>
                        <option value="polygon">Polygon</option>
                    </select>
                </div>
                <div id="cameraArea" style="position:relative;background:black;border-radius:10px;overflow:hidden;">
                    <video id="liveVideo" autoplay playsinline style="width:100%;height:auto;border-radius:10px;"></video>
                    <canvas id="overlayCanvas" style="position:absolute;top:0;left:0;width:100%;height:100%;"></canvas>
                </div>
            </div>

            <div class="card">
                <div class="card-header">
                    📸 Captured Image
                    <button class="btn btn-primary" onclick="captureImage()">Capture</button>
                </div>
                <div style="text-align:center;min-height:400px;display:flex;align-items:center;justify-content:center;background:rgba(0,0,0,0.3);border-radius:10px;">
                    {UIGenerator._generate_live_image(live_image)}
                </div>
            </div>
        </div>

        <script>
            // Initialize camera stream
            async function startCamera() {{
                const video = document.getElementById('liveVideo');
                try {{
                    const stream = await navigator.mediaDevices.getUserMedia({{ video: true }});
                    video.srcObject = stream;
                }} catch (err) {{
                    alert('Camera access denied or not available.');
                }}
            }}
            startCamera();

            // Drawing tools
            const canvas = document.getElementById('overlayCanvas');
            const ctx = canvas.getContext('2d');
            let drawing = false;
            let startX, startY;
            let shape = 'rect';
            document.getElementById('shapeTool').addEventListener('change', e => shape = e.target.value);

            canvas.addEventListener('mousedown', e => {{
                drawing = true;
                startX = e.offsetX;
                startY = e.offsetY;
            }});
            canvas.addEventListener('mouseup', e => {{
                if (!drawing) return;
                drawing = false;
                const endX = e.offsetX;
                const endY = e.offsetY;
                drawShape(startX, startY, endX, endY);
            }});

            function drawShape(x1, y1, x2, y2) {{
                ctx.strokeStyle = '#00ff00';
                ctx.lineWidth = 2;
                if (shape === 'rect') {{
                    ctx.strokeRect(x1, y1, x2 - x1, y2 - y1);
                }} else if (shape === 'circle') {{
                    const radius = Math.hypot(x2 - x1, y2 - y1);
                    ctx.beginPath();
                    ctx.arc(x1, y1, radius, 0, Math.PI * 2);
                    ctx.stroke();
                }} else if (shape === 'dot') {{
                    ctx.fillStyle = '#ff0000';
                    ctx.beginPath();
                    ctx.arc(x1, y1, 5, 0, Math.PI * 2);
                    ctx.fill();
                }}
            }}

            function captureImage() {{
                const video = document.getElementById('liveVideo');
                const tempCanvas = document.createElement('canvas');
                tempCanvas.width = video.videoWidth;
                tempCanvas.height = video.videoHeight;
                tempCanvas.getContext('2d').drawImage(video, 0, 0);
                const dataURL = tempCanvas.toDataURL('image/jpeg');
                alert('Image captured locally. (Server upload can be added)');
            }}
        </script>
        """
        return UIGenerator.generate_base_template(content, "Dashboard", "dashboard")

    
    @staticmethod
    def _generate_live_image(image_base64: Optional[str]) -> str:
        if not image_base64:
            return '<div style="color: rgba(255,255,255,0.5);"><div style="font-size: 64px;">📷</div><div>Waiting for image...</div></div>'
        return f'<img src="data:image/jpeg;base64,{image_base64}" style="max-width: 100%; max-height: 400px; border-radius: 8px;">'
    
    @staticmethod
    def _generate_system_status(status: Dict) -> str:
        components = [
            ('server_running', 'Server', 'Running'),
            ('camera_connected', 'Camera', 'Connected'),
            ('vision_engine', 'Vision Engine', 'Ready'),
            ('database', 'Database', 'Connected')
        ]
        
        html = '<div style="display: grid; gap: 10px;">'
        for key, name, label in components:
            value = status.get(key, False)
            is_ok = value in [True, 'ready', 'connected']
            badge_class = 'badge-success' if is_ok else 'badge-danger'
            badge_text = '✓ OK' if is_ok else '✗ ERROR'
            
            html += f'''
                <div style="display: flex; justify-content: space-between; align-items: center; padding: 10px; background: rgba(255,255,255,0.1); border-radius: 8px;">
                    <span>{name}</span>
                    <span class="badge {badge_class}">{badge_text}</span>
                </div>
            '''
        
        html += '</div>'
        return html
    
    @staticmethod
    def _generate_inspections_table(inspections: List[Dict]) -> str:
        if not inspections:
            return '<div style="text-align: center; padding: 40px; opacity: 0.5;">No inspections yet</div>'
        
        html = '''
        <table class="table">
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Time</th>
                    <th>Product</th>
                    <th>QR Code</th>
                    <th>Status</th>
                    <th>Actions</th>
                </tr>
            </thead>
            <tbody>
        '''
        
        for insp in inspections[:10]:
            inspection_id = insp.get('inspection_id', 'N/A')
            time_str = insp.get('formatted_time', 'N/A')
            product = insp.get('product_code', 'Unknown')
            qr_data = (insp.get('qr_data') or 'N/A')[:20]
            status = insp.get('status', 'PENDING')
            
            badge_class = 'badge-success' if status == 'OK' else 'badge-danger'
            
            html += f'''
                <tr>
                    <td>#{inspection_id}</td>
                    <td>{time_str}</td>
                    <td>{product}</td>
                    <td>{qr_data}</td>
                    <td><span class="badge {badge_class}">{status}</span></td>
                    <td>
                        <button class="btn btn-secondary" onclick="viewDetails({inspection_id})">View</button>
                    </td>
                </tr>
            '''
        
        html += '''
            </tbody>
        </table>
        <script>
            function viewDetails(id) {
                window.location.href = '/inspection/' + id;
            }
        </script>
        '''
        
        return html
    
    @staticmethod
    def generate_products_page(products: List[Dict]) -> str:
        """Generate products management page"""
        content = f'''
        <div class="card">
            <div class="card-header">
                📦 Product Management
                <button class="btn btn-primary" onclick="showModal('addProductModal')">
                    ➕ Add Product
                </button>
            </div>
            
            <table class="table">
                <thead>
                    <tr>
                        <th>Code</th>
                        <th>Name</th>
                        <th>QR Pattern</th>
                        <th>OCR Expected</th>
                        <th>Status</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    {"".join([f'''
                    <tr>
                        <td>{p.get('product_code', 'N/A')}</td>
                        <td>{p.get('product_name', 'N/A')}</td>
                        <td>{p.get('qr_pattern', 'N/A')}</td>
                        <td>{p.get('ocr_expected', 'N/A')}</td>
                        <td><span class="badge badge-success">Active</span></td>
                        <td>
                            <button class="btn btn-secondary" onclick="editProduct({p.get('product_id')})">Edit</button>
                            <button class="btn btn-danger" onclick="if(confirmDelete({p.get('product_id')}, '{p.get('product_name')}')) deleteProduct({p.get('product_id')})">Delete</button>
                        </td>
                    </tr>
                    ''' for p in products])}
                </tbody>
            </table>
        </div>
        
        <!-- Add Product Modal -->
        <div id="addProductModal" class="modal">
            <div class="modal-content">
                <div class="modal-header">
                    <span class="modal-close" onclick="hideModal('addProductModal')">&times;</span>
                    Add New Product
                </div>
                <form action="/api/products/add" method="POST">
                    <div class="form-group">
                        <label class="form-label">Product Code *</label>
                        <input type="text" name="product_code" class="form-control" required placeholder="e.g., WIDGET-001">
                    </div>
                    <div class="form-group">
                        <label class="form-label">Product Name *</label>
                        <input type="text" name="product_name" class="form-control" required placeholder="e.g., Blue Widget">
                    </div>
                    <div class="form-group">
                        <label class="form-label">QR Pattern</label>
                        <input type="text" name="qr_pattern" class="form-control" placeholder="e.g., QR-.*">
                    </div>
                    <div class="form-group">
                        <label class="form-label">Expected OCR Text</label>
                        <input type="text" name="ocr_expected" class="form-control" placeholder="e.g., LOT2024">
                    </div>
                    <div class="form-group">
                        <label class="form-label">Color Detection</label>
                        <select name="color_type" class="form-control">
                            <option value="">None</option>
                            <option value="red">Red</option>
                            <option value="green">Green</option>
                            <option value="blue">Blue</option>
                        </select>
                    </div>
                    <div style="display: flex; gap: 10px;">
                        <button type="submit" class="btn btn-success">Add Product</button>
                        <button type="button" class="btn btn-secondary" onclick="hideModal('addProductModal')">Cancel</button>
                    </div>
                </form>
            </div>
        </div>
        
        <script>
            function editProduct(id) {{
                alert('Edit product #' + id);
            }}
            
            function deleteProduct(id) {{
                window.location.href = '/api/products/delete/' + id;
            }}
        </script>
        '''
        
        return UIGenerator.generate_base_template(content, "Products", "products")
    
    @staticmethod
    def generate_reports_page(stats: Dict) -> str:
        """Generate reports page"""
        content = f'''
        <div class="grid-2">
            <div class="card">
                <div class="card-header">📊 Generate Report</div>
                <form action="/api/reports/generate" method="POST">
                    <div class="form-group">
                        <label class="form-label">Report Type</label>
                        <select name="report_type" class="form-control">
                            <option value="daily">Daily Summary</option>
                            <option value="weekly">Weekly Summary</option>
                            <option value="monthly">Monthly Summary</option>
                            <option value="custom">Custom Range</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label class="form-label">Export Format</label>
                        <select name="format" class="form-control">
                            <option value="pdf">PDF Report</option>
                            <option value="excel">Excel Spreadsheet</option>
                            <option value="csv">CSV Data</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label class="form-label">Start Date</label>
                        <input type="date" name="start_date" class="form-control">
                    </div>
                    <div class="form-group">
                        <label class="form-label">End Date</label>
                        <input type="date" name="end_date" class="form-control">
                    </div>
                    <button type="submit" class="btn btn-primary">Generate Report</button>
                </form>
            </div>
            
            <div class="card">
                <div class="card-header">📈 Statistics Overview</div>
                <div style="display: grid; gap: 15px;">
                    <div class="stat-card">
                        <div class="stat-value">{stats.get('total', 0)}</div>
                        <div class="stat-label">Total Inspections</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">{stats.get('pass_rate', 0):.1f}%</div>
                        <div class="stat-label">Pass Rate</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">{stats.get('ok', 0)}</div>
                        <div class="stat-label">OK Count</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">{stats.get('nok', 0)}</div>
                        <div class="stat-label">NOK Count</div>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="card">
            <div class="card-header">📋 Recent Reports</div>
            <table class="table">
                <thead>
                    <tr>
                        <th>Date</th>
                        <th>Type</th>
                        <th>Format</th>
                        <th>Status</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>{datetime.now().strftime("%Y-%m-%d")}</td>
                        <td>Daily Summary</td>
                        <td>PDF</td>
                        <td><span class="badge badge-success">Ready</span></td>
                        <td><button class="btn btn-primary" onclick="downloadReport(1)">Download</button></td>
                    </tr>
                </tbody>
            </table>
        </div>
        
        <script>
            function downloadReport(id) {{
                window.location.href = '/api/reports/download/' + id;
            }}
        </script>
        '''
        
        return UIGenerator.generate_base_template(content, "Reports", "reports")
    
    @staticmethod
    def generate_settings_page(config: Dict) -> str:
        """Generate settings page"""
        content = '''
        <div class="grid-2">
            <!-- System Settings -->
            <div class="card">
                <div class="card-header">⚙️ System Settings</div>
                <form action="/api/settings/system" method="POST">
                    <div class="form-group">
                        <label class="form-label">System Mode</label>
                        <select name="mode" class="form-control">
                            <option value="server_only">Server Only</option>
                            <option value="pi_only">Pi Only</option>
                            <option value="both">Both (Pi + Server)</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label class="form-label">Auto-Start Inspections</label>
                        <select name="auto_start" class="form-control">
                            <option value="true">Enabled</option>
                            <option value="false">Disabled</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label class="form-label">Log Level</label>
                        <select name="log_level" class="form-control">
                            <option value="DEBUG">Debug</option>
                            <option value="INFO" selected>Info</option>
                            <option value="WARNING">Warning</option>
                            <option value="ERROR">Error</option>
                        </select>
                    </div>
                    <button type="submit" class="btn btn-success">Save Settings</button>
                </form>
            </div>
            
            <!-- Vision Settings -->
            <div class="card">
                <div class="card-header">🔍 Vision Settings</div>
                <form action="/api/settings/vision" method="POST">
                    <div class="form-group">
                        <label class="form-label">QR Detection</label>
                        <select name="qr_enabled" class="form-control">
                            <option value="true" selected>Enabled</option>
                            <option value="false">Disabled</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label class="form-label">OCR Recognition</label>
                        <select name="ocr_enabled" class="form-control">
                            <option value="true" selected>Enabled</option>
                            <option value="false">Disabled</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label class="form-label">Blur Threshold</label>
                        <input type="number" name="blur_threshold" class="form-control" value="100" min="0" max="500">
                    </div>
                    <div class="form-group">
                        <label class="form-label">Brightness Min</label>
                        <input type="number" name="brightness_min" class="form-control" value="50" min="0" max="255">
                    </div>
                    <div class="form-group">
                        <label class="form-label">Brightness Max</label>
                        <input type="number" name="brightness_max" class="form-control" value="200" min="0" max="255">
                    </div>
                    <button type="submit" class="btn btn-success">Save Settings</button>
                </form>
            </div>
            
            <!-- Camera Settings -->
            <div class="card">
                <div class="card-header">📷 Camera Settings</div>
                <form action="/api/settings/camera" method="POST">
                    <div class="form-group">
                        <label class="form-label">Mock Mode (Testing)</label>
                        <select name="mock_mode" class="form-control">
                            <option value="true" selected>Enabled (No Pi Required)</option>
                            <option value="false">Disabled (Use Real Camera)</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label class="form-label">Resolution</label>
                        <select name="resolution" class="form-control">
                            <option value="640x480">640x480</option>
                            <option value="1280x720">1280x720 (HD)</option>
                            <option value="1920x1080" selected>1920x1080 (Full HD)</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label class="form-label">Frame Rate</label>
                        <input type="number" name="framerate" class="form-control" value="30" min="1" max="60">
                    </div>
                    <button type="submit" class="btn btn-success">Save Settings</button>
                </form>
            </div>
            
            <!-- Database Settings -->
            <div class="card">
                <div class="card-header">💾 Database Settings</div>
                <form action="/api/settings/database" method="POST">
                    <div class="form-group">
                        <label class="form-label">Auto Backup</label>
                        <select name="auto_backup" class="form-control">
                            <option value="true" selected>Enabled</option>
                            <option value="false">Disabled</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label class="form-label">Backup Interval (hours)</label>
                        <input type="number" name="backup_interval" class="form-control" value="24" min="1" max="168">
                    </div>
                    <div class="form-group">
                        <label class="form-label">Data Retention (days)</label>
                        <input type="number" name="retention_days" class="form-control" value="90" min="1" max="365">
                    </div>
                    <button type="submit" class="btn btn-success">Save Settings</button>
                </form>
                <hr style="margin: 20px 0; border-color: rgba(255,255,255,0.2);">
                <div style="display: flex; gap: 10px;">
                    <button class="btn btn-warning" onclick="backupNow()">Backup Now</button>
                    <button class="btn btn-danger" onclick="clearOldData()">Clear Old Data</button>
                </div>
            </div>
        </div>
        
        <script>
            function backupNow() {
                if(confirm('Create database backup now?')) {
                    alert('Backup started. You will be notified when complete.');
                }
            }
            
            function clearOldData() {
                if(confirm('This will delete old inspection data. Continue?')) {
                    alert('Old data cleared successfully.');
                }
            }
        </script>
        '''
        
        return UIGenerator.generate_base_template(content, "Settings", "settings")
    
    @staticmethod
    def generate_login_page() -> str:
        """Generate login page"""
        return '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Login - QC Vision System</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .login-container {
            background: rgba(255, 255, 255, 0.15);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 40px;
            width: 400px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
        
        .login-header {
            text-align: center;
            margin-bottom: 30px;
            color: white;
        }
        
        .login-header h1 {
            font-size: 32px;
            margin-bottom: 10px;
        }
        
        .login-header p {
            opacity: 0.8;
        }
        
        .form-group {
            margin-bottom: 20px;
        }
        
        .form-label {
            display: block;
            margin-bottom: 8px;
            color: white;
            font-weight: 600;
        }
        
        .form-control {
            width: 100%;
            padding: 12px;
            border: 2px solid rgba(255, 255, 255, 0.3);
            border-radius: 8px;
            background: rgba(255, 255, 255, 0.1);
            color: white;
            font-size: 16px;
        }
        
        .form-control:focus {
            outline: none;
            border-color: rgba(255, 255, 255, 0.6);
            background: rgba(255, 255, 255, 0.15);
        }
        
        .form-control::placeholder {
            color: rgba(255, 255, 255, 0.5);
        }
        
        .btn-login {
            width: 100%;
            padding: 14px;
            border: none;
            border-radius: 8px;
            background: white;
            color: #667eea;
            font-size: 16px;
            font-weight: 700;
            cursor: pointer;
            transition: all 0.3s;
        }
        
        .btn-login:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        }
        
        .login-footer {
            text-align: center;
            margin-top: 20px;
            color: white;
            opacity: 0.8;
            font-size: 14px;
        }
    </style>
</head>
<body>
    <div class="login-container">
        <div class="login-header">
            <h1>🔍 QC Vision</h1>
            <p>Quality Control System</p>
        </div>
        <form action="/api/login" method="POST">
            <div class="form-group">
                <label class="form-label">Username</label>
                <input type="text" name="username" class="form-control" placeholder="Enter username" required>
            </div>
            <div class="form-group">
                <label class="form-label">Password</label>
                <input type="password" name="password" class="form-control" placeholder="Enter password" required>
            </div>
            <button type="submit" class="btn-login">Login</button>
        </form>
        <div class="login-footer">
            <p>Default: admin / admin</p>
        </div>
    </div>
</body>
</html>
'''
