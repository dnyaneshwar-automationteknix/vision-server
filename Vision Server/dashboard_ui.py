"""
Complete Dashboard UI Generator
Beautiful, Modern, Responsive Interface
"""


class DashboardUI:
    """Generate all UI pages"""
    
    @staticmethod
    def get_base_styles():
        """Get base CSS styles"""
        return """
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            
            body {
                font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: #fff;
                min-height: 100vh;
            }
            
            .navbar {
                background: rgba(255, 255, 255, 0.15);
                backdrop-filter: blur(10px);
                padding: 15px 30px;
                display: flex;
                justify-content: space-between;
                align-items: center;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            }
            
            .nav-brand {
                font-size: 24px;
                font-weight: 700;
                display: flex;
                align-items: center;
                gap: 10px;
            }
            
            .nav-menu {
                display: flex;
                gap: 5px;
            }
            
            .nav-item {
                padding: 10px 20px;
                border-radius: 8px;
                text-decoration: none;
                color: white;
                transition: all 0.3s;
                cursor: pointer;
                font-weight: 500;
            }
            
            .nav-item:hover {
                background: rgba(255, 255, 255, 0.2);
            }
            
            .nav-item.active {
                background: rgba(255, 255, 255, 0.3);
            }
            
            .container {
                max-width: 1600px;
                margin: 0 auto;
                padding: 20px;
            }
            
            .grid-2 { display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px; }
            .grid-3 { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; }
            .grid-4 { display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; }
            
            .card {
                background: rgba(255, 255, 255, 0.15);
                backdrop-filter: blur(10px);
                border-radius: 15px;
                padding: 25px;
                margin-bottom: 20px;
                box-shadow: 0 8px 32px rgba(0,0,0,0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
            }
            
            .card-header {
                font-size: 20px;
                font-weight: 600;
                margin-bottom: 20px;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            
            .stat-card {
                background: rgba(255, 255, 255, 0.1);
                border-radius: 12px;
                padding: 20px;
                text-align: center;
            }
            
            .stat-value {
                font-size: 36px;
                font-weight: 700;
                margin-bottom: 5px;
            }
            
            .stat-label {
                font-size: 14px;
                opacity: 0.8;
            }
            
            .btn {
                padding: 10px 20px;
                border: none;
                border-radius: 8px;
                cursor: pointer;
                font-size: 14px;
                font-weight: 600;
                transition: all 0.3s;
                text-decoration: none;
                display: inline-block;
            }
            
            .btn-primary { background: #667eea; color: white; }
            .btn-success { background: #00c851; color: white; }
            .btn-danger { background: #ff4444; color: white; }
            .btn-warning { background: #ffbb33; color: white; }
            
            .btn:hover {
                transform: translateY(-2px);
                box-shadow: 0 4px 8px rgba(0,0,0,0.2);
            }
            
            .video-container {
                position: relative;
                background: #000;
                border-radius: 10px;
                overflow: hidden;
                min-height: 400px;
            }
            
            video, img {
                width: 100%;
                height: auto;
                display: block;
                border-radius: 10px;
            }
            
            canvas {
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                cursor: crosshair;
            }
            
            .form-group {
                margin-bottom: 15px;
            }
            
            .form-label {
                display: block;
                margin-bottom: 5px;
                font-weight: 600;
                font-size: 14px;
            }
            
            .form-control {
                width: 100%;
                padding: 10px;
                border: 2px solid rgba(255, 255, 255, 0.3);
                border-radius: 8px;
                background: rgba(255, 255, 255, 0.1);
                color: white;
                font-size: 14px;
            }
            
            .form-control:focus {
                outline: none;
                border-color: rgba(255, 255, 255, 0.6);
            }
            
            .form-control::placeholder {
                color: rgba(255, 255, 255, 0.5);
            }
            
            select.form-control {
                cursor: pointer;
            }
            
            .table {
                width: 100%;
                border-collapse: collapse;
            }
            
            .table th {
                text-align: left;
                padding: 12px;
                background: rgba(255, 255, 255, 0.1);
                font-weight: 600;
                border-bottom: 2px solid rgba(255, 255, 255, 0.2);
            }
            
            .table td {
                padding: 12px;
                border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            }
            
            .table tr:hover {
                background: rgba(255, 255, 255, 0.05);
            }
            
            .badge {
                padding: 5px 12px;
                border-radius: 20px;
                font-size: 12px;
                font-weight: 600;
                display: inline-block;
            }
            
            .badge-success { background: #00c851; color: white; }
            .badge-danger { background: #ff4444; color: white; }
            .badge-warning { background: #ffbb33; color: white; }
            .badge-info { background: #33b5e5; color: white; }
            
            .results-panel {
                max-height: 600px;
                overflow-y: auto;
            }
            
            .result-item {
                background: rgba(255, 255, 255, 0.1);
                padding: 15px;
                border-radius: 8px;
                margin-bottom: 10px;
            }
            
            .result-ok { border-left: 4px solid #00c851; }
            .result-nok { border-left: 4px solid #ff4444; }
            
            .inline-inputs {
                display: grid;
                grid-template-columns: repeat(3, 1fr);
                gap: 10px;
            }
            
            .config-section {
                background: rgba(0, 0, 0, 0.2);
                padding: 15px;
                border-radius: 8px;
                margin-bottom: 15px;
            }
            
            .config-section h3 {
                margin-bottom: 10px;
                font-size: 16px;
            }
            
            @media (max-width: 768px) {
                .grid-2, .grid-3, .grid-4 { grid-template-columns: 1fr; }
                .navbar { flex-direction: column; gap: 15px; }
                .nav-menu { flex-direction: column; width: 100%; }
            }
            
            .spinner {
                border: 3px solid rgba(255,255,255,0.3);
                border-top: 3px solid white;
                border-radius: 50%;
                width: 40px;
                height: 40px;
                animation: spin 1s linear infinite;
                margin: 20px auto;
            }
            
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
        </style>
        """
    
    @staticmethod
    def get_navbar(active_page='dashboard'):
        """Get navigation bar HTML"""
        return f"""
        <nav class="navbar">
            <div class="nav-brand">
                <span>🔍</span>
                <span>QC Vision System</span>
            </div>
            <div class="nav-menu">
                <a href="/dashboard" class="nav-item {'active' if active_page == 'dashboard' else ''}">
                    📊 Dashboard
                </a>
                <a href="/color-detection" class="nav-item {'active' if active_page == 'color-detection' else ''}">
                    🎨 Color Detection
                </a>
                <a href="/inspections" class="nav-item {'active' if active_page == 'inspections' else ''}">
                    🔬 Inspections
                </a>
                <a href="/configuration" class="nav-item {'active' if active_page == 'configuration' else ''}">
                    ⚙️ Configuration
                </a>
                <a href="/reports" class="nav-item {'active' if active_page == 'reports' else ''}">
                    📈 Reports
                </a>
            </div>
        </nav>
        """
    
    @staticmethod
    def generate_dashboard_page(state: dict):
        """Generate main dashboard page"""
        stats = state.get('statistics', {})
        recent = state.get('recent_inspections', [])[:10]
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Dashboard - QC Vision System</title>
            {DashboardUI.get_base_styles()}
        </head>
        <body>
            {DashboardUI.get_navbar('dashboard')}
            
            <div class="container">
                <h1 style="margin-bottom: 20px;">📊 Quality Control Dashboard</h1>
                
                <!-- Statistics -->
                <div class="grid-4">
                    <div class="stat-card" style="border-left: 4px solid #00c851;">
                        <div class="stat-value">{stats.get('ok', 0)}</div>
                        <div class="stat-label">✓ OK</div>
                    </div>
                    <div class="stat-card" style="border-left: 4px solid #ff4444;">
                        <div class="stat-value">{stats.get('nok', 0)}</div>
                        <div class="stat-label">✗ NOK</div>
                    </div>
                    <div class="stat-card" style="border-left: 4px solid #33b5e5;">
                        <div class="stat-value">{stats.get('total', 0)}</div>
                        <div class="stat-label">Total</div>
                    </div>
                    <div class="stat-card" style="border-left: 4px solid #ffbb33;">
                        <div class="stat-value">{stats.get('pass_rate', 0):.1f}%</div>
                        <div class="stat-label">Pass Rate</div>
                    </div>
                </div>
                
                <!-- Quick Actions -->
                <div class="card">
                    <div class="card-header">⚡ Quick Actions</div>
                    <div style="display: flex; gap: 10px; flex-wrap: wrap;">
                        <a href="/color-detection" class="btn btn-primary">🎨 Start Color Detection</a>
                        <a href="/configuration" class="btn btn-success">⚙️ Configure Models</a>
                        <a href="/inspections" class="btn btn-warning">📋 View All Inspections</a>
                        <a href="/reports" class="btn btn-danger">📊 Generate Report</a>
                    </div>
                </div>
                
                <!-- Recent Inspections -->
                <div class="card">
                    <div class="card-header">
                        🔬 Recent Inspections
                        <a href="/inspections" class="btn btn-primary">View All</a>
                    </div>
                    {DashboardUI._generate_inspections_table(recent)}
                </div>
                
                <!-- Detection Statistics -->
                <div class="grid-3">
                    <div class="stat-card">
                        <div class="stat-value">{stats.get('qr_success_count', 0)}</div>
                        <div class="stat-label">QR Detections</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">{stats.get('ocr_success_count', 0)}</div>
                        <div class="stat-label">OCR Extractions</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">{stats.get('color_detection_count', 0)}</div>
                        <div class="stat-label">Color Detections</div>
                    </div>
                </div>
            </div>
            
            <script>
                // Auto-refresh dashboard every 5 seconds
                setInterval(() => {{
                    fetch('/api/state')
                        .then(r => r.json())
                        .then(data => {{
                            // Update stats without full page reload
                            console.log('Dashboard updated', data);
                        }});
                }}, 5000);
            </script>
        </body>
        </html>
        """
        return html
    
    @staticmethod
    def _generate_inspections_table(inspections):
        """Generate inspections table"""
        if not inspections:
            return '<p style="text-align:center; opacity:0.5; padding:40px;">No inspections yet</p>'
        
        rows = ''
        for insp in inspections:
            inspection_id = insp.get('inspection_id', 'N/A')
            time_str = insp.get('formatted_time', 'N/A')
            product = insp.get('product_code', 'Unknown')
            status = insp.get('status', 'PENDING')
            badge_class = 'badge-success' if status == 'OK' else 'badge-danger'
            
            rows += f"""
            <tr onclick="window.location.href='/inspection/{inspection_id}'" style="cursor:pointer;">
                <td>#{inspection_id}</td>
                <td>{time_str}</td>
                <td>{product}</td>
                <td><span class="badge {badge_class}">{status}</span></td>
                <td>
                    {'✓ QR' if insp.get('qr_success') else ''}
                    {'✓ OCR' if insp.get('ocr_success') else ''}
                    {'✓ Color' if insp.get('color_detection') else ''}
                </td>
            </tr>
            """
        
        return f"""
        <table class="table">
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Time</th>
                    <th>Product</th>
                    <th>Status</th>
                    <th>Detections</th>
                </tr>
            </thead>
            <tbody>{rows}</tbody>
        </table>
        """
    
    @staticmethod
    def generate_color_detection_page():
        """Generate color detection page"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Color Detection - QC Vision System</title>
            {DashboardUI.get_base_styles()}
        </head>
        <body>
            {DashboardUI.get_navbar('color-detection')}
            
            <div class="container">
                <h1 style="margin-bottom: 20px;">🎨 Color Detection System</h1>
                
                <div class="grid-2">
                    <!-- Camera Panel -->
                    <div class="card">
                        <div class="card-header">
                            📹 Camera / Image Input
                            <button class="btn btn-success" onclick="captureAndAnalyze()">📸 Capture & Analyze</button>
                        </div>
                        <div style="display: flex; gap: 10px; margin-bottom: 15px;">
                            <button class="btn btn-primary" onclick="startCamera()">📹 Start Camera</button>
                            <input type="file" id="fileInput" accept="image/*" onchange="loadImage(event)" style="display:none;">
                            <button class="btn btn-warning" onclick="document.getElementById('fileInput').click()">📁 Upload</button>
                        </div>
                        <div class="video-container">
                            <video id="liveVideo" autoplay playsinline style="display:none;"></video>
                            <img id="capturedImage" style="display:none;">
                            <canvas id="drawingCanvas"></canvas>
                        </div>
                        <div style="margin-top: 15px;">
                            <label class="form-label">Detection Mode:</label>
                            <select id="detectionMode" class="form-control">
                                <option value="all">All (QR + OCR + Colors)</option>
                                <option value="qr">QR/Barcode Only</option>
                                <option value="ocr">OCR Only</option>
                                <option value="colors">Colors Only</option>
                            </select>
                        </div>
                    </div>
                    
                    <!-- Configuration Panel -->
                    <div class="card">
                        <div class="card-header">⚙️ Detection Configuration</div>
                        <div style="max-height: 500px; overflow-y: auto;">
                            <!-- Model Selection -->
                            <div class="form-group">
                                <label class="form-label">Model ID:</label>
                                <select id="modelId" class="form-control" onchange="loadModelConfig()">
                                    <option value="DEFAULT">DEFAULT</option>
                                    <option value="MODEL_A">MODEL_A</option>
                                    <option value="MODEL_B">MODEL_B</option>
                                </select>
                            </div>
                            
                            <!-- Box Configuration -->
                            <div class="config-section">
                                <h3>📦 Bounding Box</h3>
                                <label class="form-label">Position:</label>
                                <div class="inline-inputs">
                                    <input type="number" id="boxLeft" class="form-control" placeholder="Left" value="100">
                                    <input type="number" id="boxTop" class="form-control" placeholder="Top" value="100">
                                </div>
                                <div class="inline-inputs" style="margin-top: 10px;">
                                    <input type="number" id="boxRight" class="form-control" placeholder="Right" value="300">
                                    <input type="number" id="boxBottom" class="form-control" placeholder="Bottom" value="300">
                                </div>
                                
                                <label class="form-label" style="margin-top: 15px;">C1 RGB From:</label>
                                <div class="inline-inputs">
                                    <input type="number" id="c1RFrom" class="form-control" placeholder="R" value="0" min="0" max="255">
                                    <input type="number" id="c1GFrom" class="form-control" placeholder="G" value="0" min="0" max="255">
                                    <input type="number" id="c1BFrom" class="form-control" placeholder="B" value="0" min="0" max="255">
                                </div>
                                
                                <label class="form-label" style="margin-top: 10px;">C1 RGB To:</label>
                                <div class="inline-inputs">
                                    <input type="number" id="c1RTo" class="form-control" placeholder="R" value="50" min="0" max="255">
                                    <input type="number" id="c1GTo" class="form-control" placeholder="G" value="50" min="0" max="255">
                                    <input type="number" id="c1BTo" class="form-control" placeholder="B" value="50" min="0" max="255">
                                </div>
                                
                                <label class="form-label" style="margin-top: 15px;">C2 RGB From:</label>
                                <div class="inline-inputs">
                                    <input type="number" id="c2RFrom" class="form-control" placeholder="R" value="200" min="0" max="255">
                                    <input type="number" id="c2GFrom" class="form-control" placeholder="G" value="200" min="0" max="255">
                                    <input type="number" id="c2BFrom" class="form-control" placeholder="B" value="200" min="0" max="255">
                                </div>
                                
                                <label class="form-label" style="margin-top: 10px;">C2 RGB To:</label>
                                <div class="inline-inputs">
                                    <input type="number" id="c2RTo" class="form-control" placeholder="R" value="255" min="0" max="255">
                                    <input type="number" id="c2GTo" class="form-control" placeholder="G" value="255" min="0" max="255">
                                    <input type="number" id="c2BTo" class="form-control" placeholder="B" value="255" min="0" max="255">
                                </div>
                                
                                <label class="form-label" style="margin-top: 15px;">Threshold (%):</label>
                                <input type="number" id="pixelRange" class="form-control" value="50" min="0" max="100">
                                
                                <button class="btn btn-success" style="width: 100%; margin-top: 15px;" onclick="saveBoxConfig()">💾 Save Box Config</button>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Results Panel -->
                <div class="card">
                    <div class="card-header">
                        📊 Detection Results
                        <button class="btn btn-warning" onclick="exportResults()">💾 Export JSON</button>
                    </div>
                    <div class="results-panel" id="resultsPanel">
                        <p style="text-align:center; opacity:0.5; padding:40px;">Capture an image to start detection</p>
                    </div>
                </div>
            </div>
            
            <script>
                let video, canvas, ctx;
                let capturedImageData = null;
                let latestResults = null;
                
                window.onload = () => {{
                    video = document.getElementById('liveVideo');
                    canvas = document.getElementById('drawingCanvas');
                    ctx = canvas.getContext('2d');
                }};
                
                async function startCamera() {{
                    try {{
                        const stream = await navigator.mediaDevices.getUserMedia({{video: {{width: 1280, height: 720}}}});
                        video.srcObject = stream;
                        video.style.display = 'block';
                        document.getElementById('capturedImage').style.display = 'none';
                        
                        video.onloadedmetadata = () => {{
                            canvas.width = video.videoWidth;
                            canvas.height = video.videoHeight;
                        }};
                    }} catch(err) {{
                        alert('Camera access denied: ' + err.message);
                    }}
                }}
                
                function loadImage(event) {{
                    const file = event.target.files[0];
                    const reader = new FileReader();
                    reader.onload = (e) => {{
                        capturedImageData = e.target.result;
                        const img = document.getElementById('capturedImage');
                        img.src = capturedImageData;
                        img.style.display = 'block';
                        video.style.display = 'none';
                    }};
                    reader.readAsDataURL(file);
                }}
                
                async function captureAndAnalyze() {{
                    // Capture from video or use loaded image
                    if (video.style.display !== 'none') {{
                        const tempCanvas = document.createElement('canvas');
                        tempCanvas.width = video.videoWidth;
                        tempCanvas.height = video.videoHeight;
                        tempCanvas.getContext('2d').drawImage(video, 0, 0);
                        capturedImageData = tempCanvas.toDataURL('image/jpeg', 0.95);
                        
                        const img = document.getElementById('capturedImage');
                        img.src = capturedImageData;
                        img.style.display = 'block';
                        video.style.display = 'none';
                    }}
                    
                    if (!capturedImageData) {{
                        alert('Please capture or load an image first');
                        return;
                    }}
                    
                    // Show loading
                    document.getElementById('resultsPanel').innerHTML = '<div class="spinner"></div><p style="text-align:center;">Analyzing...</p>';
                    
                    // Prepare detection config
                    const mode = document.getElementById('detectionMode').value;
                    const box = {{
                        id: 1,
                        model_id: document.getElementById('modelId').value,
                        position: 1,
                        left: parseInt(document.getElementById('boxLeft').value),
                        right: parseInt(document.getElementById('boxRight').value),
                        top: parseInt(document.getElementById('boxTop').value),
                        bottom: parseInt(document.getElementById('boxBottom').value),
                        c1_r_from: parseInt(document.getElementById('c1RFrom').value),
                        c1_g_from: parseInt(document.getElementById('c1GFrom').value),
                        c1_b_from: parseInt(document.getElementById('c1BFrom').value),
                        c1_r_to: parseInt(document.getElementById('c1RTo').value),
                        c1_g_to: parseInt(document.getElementById('c1GTo').value),
                        c1_b_to: parseInt(document.getElementById('c1BTo').value),
                        c2_r_from: parseInt(document.getElementById('c2RFrom').value),
                        c2_g_from: parseInt(document.getElementById('c2GFrom').value),
                        c2_b_from: parseInt(document.getElementById('c2BFrom').value),
                        c2_r_to: parseInt(document.getElementById('c2RTo').value),
                        c2_g_to: parseInt(document.getElementById('c2GTo').value),
                        c2_b_to: parseInt(document.getElementById('c2BTo').value),
                        c1_pixel_count_range: 10,
                        c2_pixel_count_range: 10,
                        pixel_range: parseFloat(document.getElementById('pixelRange').value),
                        greater_less_than: 'GREATER_THAN',
                        ok_nok: 'OK'
                    }};
                    
                    try {{
                        const response = await fetch('/api/analyze-complete', {{
                            method: 'POST',
                            headers: {{'Content-Type': 'application/json'}},
                            body: JSON.stringify({{
                                image: capturedImageData.split(',')[1],
                                detect_qr: mode === 'all' || mode === 'qr',
                                detect_ocr: mode === 'all' || mode === 'ocr',
                                detect_colors: mode === 'all' || mode === 'colors',
                                detect_quality: true,
                                boxes: [box],
                                rings: [],
                                visualize: true
                            }})
                        }});
                        
                        const data = await response.json();
                        latestResults = data.result;
                        displayResults(data.result);
                    }} catch(err) {{
                        alert('Detection failed: ' + err.message);
                        document.getElementById('resultsPanel').innerHTML = '<p style="text-align:center; color:#ff4444;">Error: ' + err.message + '</p>';
                    }}
                }}
                
                function displayResults(result) {{
                    let html = '';
                    
                    // Quality
                    if (result.quality) {{
                        const q = result.quality;
                        html += `<div class="result-item">
                            <h3>✨ Image Quality</h3>
                            <p><b>Blur Score:</b> ${{q.blur.blur_score}} (${{q.blur.status}})</p>
                            <p><b>Brightness:</b> ${{q.brightness.brightness}} (${{q.brightness.status}})</p>
                            <p><b>Overall:</b> ${{q.overall_status}}</p>
                        </div>`;
                    }}
                    
                    // QR Codes
                    if (result.qr_codes && result.qr_codes.length > 0) {{
                        html += '<div class="result-item result-ok"><h3>🔍 QR/Barcode Detected</h3>';
                        result.qr_codes.forEach(qr => {{
                            html += `<p><b>${{qr.format}}:</b> ${{qr.data}}</p>`;
                        }});
                        html += '</div>';
                    }}
                    
                    // OCR
                    if (result.ocr_text) {{
                        html += `<div class="result-item result-ok">
                            <h3>📝 OCR Text</h3>
                            <p>${{result.ocr_text}}</p>
                        </div>`;
                    }}
                    
                    // Color Detection
                    if (result.colors && result.colors.boxes) {{
                        result.colors.boxes.forEach(box => {{
                            const isOk = box.verdict === 'OK';
                            html += `<div class="result-item ${{isOk ? 'result-ok' : 'result-nok'}}">
                                <h3>📦 Box ${{box.position}} - ${{box.verdict}}</h3>
                                <p><b>C1 Pixels:</b> ${{box.c1_pixel_count}} (${{box.c1_percentage}}%)</p>
                                <p><b>C2 Pixels:</b> ${{box.c2_pixel_count}} (${{box.c2_percentage}}%)</p>
                                <p><b>Total Area:</b> ${{box.total_pixels}} pixels</p>
                            </div>`;
                        }});
                    }}
                    
                    // Overall Verdict
                    const verdictClass = result.overall_verdict === 'OK' ? 'result-ok' : 'result-nok';
                    html += `<div class="result-item ${{verdictClass}}">
                        <h3>🎯 Overall Verdict: ${{result.overall_verdict}}</h3>
                        <p><b>Processing Time:</b> ${{result.processing_time}}s</p>
                        <p><b>Inspection ID:</b> #${{result.inspection_id}}</p>
                    </div>`;
                    
                    // Visualization
                    if (result.visualization) {{
                        html += `<div class="result-item">
                            <h3>📊 Visualization</h3>
                            <img src="data:image/jpeg;base64,${{result.visualization}}" style="width:100%; border-radius:8px;">
                        </div>`;
                    }}
                    
                    document.getElementById('resultsPanel').innerHTML = html || '<p style="text-align:center; opacity:0.5;">No results</p>';
                }}
                
                async function saveBoxConfig() {{
                    const box = {{
                        model_id: document.getElementById('modelId').value,
                        position: 1,
                        left: parseInt(document.getElementById('boxLeft').value),
                        right: parseInt(document.getElementById('boxRight').value),
                        top: parseInt(document.getElementById('boxTop').value),
                        bottom: parseInt(document.getElementById('boxBottom').value),
                        c1_r_from: parseInt(document.getElementById('c1RFrom').value),
                        c1_g_from: parseInt(document.getElementById('c1GFrom').value),
                        c1_b_from: parseInt(document.getElementById('c1BFrom').value),
                        c1_r_to: parseInt(document.getElementById('c1RTo').value),
                        c1_g_to: parseInt(document.getElementById('c1GTo').value),
                        c1_b_to: parseInt(document.getElementById('c1BTo').value),
                        c2_r_from: parseInt(document.getElementById('c2RFrom').value),
                        c2_g_from: parseInt(document.getElementById('c2GFrom').value),
                        c2_b_from: parseInt(document.getElementById('c2BFrom').value),
                        c2_r_to: parseInt(document.getElementById('c2RTo').value),
                        c2_g_to: parseInt(document.getElementById('c2GTo').value),
                        c2_b_to: parseInt(document.getElementById('c2BTo').value),
                        c1_pixel_count_range: 10,
                        c2_pixel_count_range: 10,
                        pixel_range: parseFloat(document.getElementById('pixelRange').value),
                        greater_less_than: 'GREATER_THAN',
                        ok_nok: 'OK'
                    }};
                    
                    try {{
                        const response = await fetch('/api/save-box', {{
                            method: 'POST',
                            headers: {{'Content-Type': 'application/json'}},
                            body: JSON.stringify({{box: box}})
                        }});
                        
                        const data = await response.json();
                        if (data.success) {{
                            alert('Box configuration saved successfully!');
                        }}
                    }} catch(err) {{
                        alert('Failed to save: ' + err.message);
                    }}
                }}
                
                async function loadModelConfig() {{
                    const modelId = document.getElementById('modelId').value;
                    try {{
                        const response = await fetch('/api/get-boxes', {{
                            method: 'POST',
                            headers: {{'Content-Type': 'application/json'}},
                            body: JSON.stringify({{model_id: modelId}})
                        }});
                        
                        const data = await response.json();
                        if (data.success && data.boxes.length > 0) {{
                            const box = data.boxes[0];
                            document.getElementById('boxLeft').value = box.left;
                            document.getElementById('boxRight').value = box.right;
                            document.getElementById('boxTop').value = box.top;
                            document.getElementById('boxBottom').value = box.bottom;
                            document.getElementById('c1RFrom').value = box.c1_r_from;
                            document.getElementById('c1GFrom').value = box.c1_g_from;
                            document.getElementById('c1BFrom').value = box.c1_b_from;
                            document.getElementById('c1RTo').value = box.c1_r_to;
                            document.getElementById('c1GTo').value = box.c1_g_to;
                            document.getElementById('c1BTo').value = box.c1_b_to;
                            document.getElementById('c2RFrom').value = box.c2_r_from;
                            document.getElementById('c2GFrom').value = box.c2_g_from;
                            document.getElementById('c2BFrom').value = box.c2_b_from;
                            document.getElementById('c2RTo').value = box.c2_r_to;
                            document.getElementById('c2GTo').value = box.c2_g_to;
                            document.getElementById('c2BTo').value = box.c2_b_to;
                            document.getElementById('pixelRange').value = box.pixel_range;
                        }}
                    }} catch(err) {{
                        console.error('Failed to load config:', err);
                    }}
                }}
                
                function exportResults() {{
                    if (!latestResults) {{
                        alert('No results to export');
                        return;
                    }}
                    const blob = new Blob([JSON.stringify(latestResults, null, 2)], {{type: 'application/json'}});
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = `inspection_${{Date.now()}}.json`;
                    a.click();
                }}
            </script>
        </body>
        </html>
        """
        return html
    
    @staticmethod
    def generate_inspections_page(inspections):
        """Generate inspections list page"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Inspections - QC Vision System</title>
            {DashboardUI.get_base_styles()}
        </head>
        <body>
            {DashboardUI.get_navbar('inspections')}
            
            <div class="container">
                <h1 style="margin-bottom: 20px;">🔬 Inspection History</h1>
                
                <div class="card">
                    <div class="card-header">
                        All Inspections
                        <div>
                            <input type="text" id="searchBox" class="form-control" placeholder="Search..." style="width:300px; display:inline-block;">
                            <button class="btn btn-warning" onclick="exportAll()">📥 Export All</button>
                        </div>
                    </div>
                    {DashboardUI._generate_inspections_table(inspections)}
                </div>
            </div>
            
            <script>
                function exportAll() {{
                    window.location.href = '/api/export-inspections';
                }}
            </script>
        </body>
        </html>
        """
        return html
    
    @staticmethod
    def generate_inspection_detail_page(inspection):
        """Generate inspection detail page"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Inspection #{inspection.get('inspection_id')} - QC Vision System</title>
            {DashboardUI.get_base_styles()}
        </head>
        <body>
            {DashboardUI.get_navbar('inspections')}
            
            <div class="container">
                <h1 style="margin-bottom: 20px;">🔍 Inspection #{inspection.get('inspection_id')}</h1>
                
                <div class="grid-2">
                    <div class="card">
                        <div class="card-header">📋 Details</div>
                        <p><b>Status:</b> <span class="badge badge-{'success' if inspection.get('status') == 'OK' else 'danger'}">{inspection.get('status', 'N/A')}</span></p>
                        <p><b>Product:</b> {inspection.get('product_code', 'N/A')}</p>
                        <p><b>Time:</b> {inspection.get('formatted_time', 'N/A')}</p>
                        <p><b>Station:</b> {inspection.get('station_id', 'N/A')}</p>
                        <p><b>QR Data:</b> {inspection.get('qr_data', 'N/A')}</p>
                        <p><b>OCR Text:</b> {inspection.get('ocr_text', 'N/A')}</p>
                        <p><b>Blur Score:</b> {inspection.get('blur_score', 'N/A')}</p>
                        <p><b>Processing Time:</b> {inspection.get('processing_time', 'N/A')}s</p>
                    </div>
                    
                    <div class="card">
                        <div class="card-header">🎨 Color Detection Results</div>
                        {DashboardUI._generate_color_detection_details(inspection.get('color_detections', []))}
                    </div>
                </div>
                
                <div class="card">
                    <div class="card-header">📸 Captured Image</div>
                    <img src="data:image/jpeg;base64,{inspection.get('image_base64', '')}" style="max-width:100%; border-radius:8px;">
                </div>
                
                <button class="btn btn-primary" onclick="window.history.back()">← Back</button>
            </div>
        </body>
        </html>
        """
        return html
    
    @staticmethod
    def _generate_color_detection_details(color_detections):
        """Generate color detection details"""
        if not color_detections:
            return '<p style="opacity:0.5;">No color detection data</p>'
        
        html = ''
        for cd in color_detections:
            verdict_class = 'result-ok' if cd.get('verdict') == 'OK' else 'result-nok'
            html += f"""
            <div class="result-item {verdict_class}">
                <h4>{cd.get('detection_type', 'N/A')} #{cd.get('position', 'N/A')} - {cd.get('verdict', 'N/A')}</h4>
                <p><b>C1 Pixels:</b> {cd.get('c1_pixel_count', 0)} ({cd.get('c1_percentage', 0)}%)</p>
                <p><b>C2 Pixels:</b> {cd.get('c2_pixel_count', 0)} ({cd.get('c2_percentage', 0)}%)</p>
                <p><b>Total:</b> {cd.get('total_pixels', 0)} pixels</p>
            </div>
            """
        return html
    
    @staticmethod
    def generate_configuration_page():
        """Generate configuration page"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Configuration - QC Vision System</title>
            {DashboardUI.get_base_styles()}
        </head>
        <body>
            {DashboardUI.get_navbar('configuration')}
            
            <div class="container">
                <h1 style="margin-bottom: 20px;">⚙️ System Configuration</h1>
                
                <div class="card">
                    <div class="card-header">📦 Bounding Box Models</div>
                    <p>Configure detection zones and RGB ranges for different product models.</p>
                    <button class="btn btn-primary" onclick="window.location.href='/color-detection'">Configure Boxes →</button>
                </div>
                
                <div class="card">
                    <div class="card-header">⭕ Ring Models</div>
                    <p>Configure circular detection zones with portions for color analysis.</p>
                    <button class="btn btn-primary" onclick="alert('Ring configuration coming soon!')">Configure Rings →</button>
                </div>
                
                <div class="card">
                    <div class="card-header">🔍 Vision Settings</div>
                    <div class="form-group">
                        <label class="form-label">QR Detection</label>
                        <select class="form-control">
                            <option>Enabled</option>
                            <option>Disabled</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label class="form-label">OCR Recognition</label>
                        <select class="form-control">
                            <option>Enabled</option>
                            <option>Disabled</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label class="form-label">Blur Threshold</label>
                        <input type="number" class="form-control" value="100">
                    </div>
                    <button class="btn btn-success">Save Settings</button>
                </div>
            </div>
        </body>
        </html>
        """
        return html
    
    @staticmethod
    def generate_reports_page(stats):
        """Generate reports page"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Reports - QC Vision System</title>
            {DashboardUI.get_base_styles()}
        </head>
        <body>
            {DashboardUI.get_navbar('reports')}
            
            <div class="container">
                <h1 style="margin-bottom: 20px;">📈 Reports & Analytics</h1>
                
                <div class="grid-3">
                    <div class="stat-card">
                        <div class="stat-value">{stats.get('total', 0)}</div>
                        <div class="stat-label">Total Inspections</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">{stats.get('pass_rate', 0):.1f}%</div>
                        <div class="stat-label">Pass Rate</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">{stats.get('avg_time', 0):.2f}s</div>
                        <div class="stat-label">Avg Processing Time</div>
                    </div>
                </div>
                
                <div class="card">
                    <div class="card-header">📊 Generate Report</div>
                    <div class="form-group">
                        <label class="form-label">Report Type</label>
                        <select class="form-control">
                            <option>Daily Summary</option>
                            <option>Weekly Summary</option>
                            <option>Monthly Summary</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label class="form-label">Format</label>
                        <select class="form-control">
                            <option>PDF</option>
                            <option>Excel</option>
                            <option>CSV</option>
                        </select>
                    </div>
                    <button class="btn btn-success">Generate Report</button>
                </div>
                
                <div class="card">
                    <div class="card-header">📉 Detection Statistics</div>
                    <div class="grid-3">
                        <div class="stat-card">
                            <div class="stat-value">{stats.get('qr_success_count', 0)}</div>
                            <div class="stat-label">QR Detections</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value">{stats.get('ocr_success_count', 0)}</div>
                            <div class="stat-label">OCR Extractions</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value">{stats.get('color_detection_count', 0)}</div>
                            <div class="stat-label">Color Detections</div>
                        </div>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        return html


if __name__ == "__main__":
    print("Dashboard UI Generator - Ready")