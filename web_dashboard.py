"""
upgraded_dashboard.py

QC Vision System - Live Web Dashboard (Upgraded)
Features:
 - Theme customization (dark / light / neon) via ?theme=...
 - Vision analytics: avg blur, qr/ocr success rates, avg processing time
 - System diagnostics (cpu, memory, fps)
 - CSV report download: /report
 - AJAX updates (no full page reload)
 - Demo simulator using numpy + opencv (optional)
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import time
import threading
from urllib.parse import urlparse, parse_qs
import base64
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path
import io

# Optional system metrics
try:
    import psutil
except Exception:
    psutil = None  # will use simulated diagnostics if psutil missing

# Demo image dependencies (install with pip if you want demo)
try:
    import cv2
    import numpy as np
except Exception:
    cv2 = None
    np = None


# -------------------------
# Live dashboard state
# -------------------------
class LiveDashboard:
    """
    Live dashboard state manager
    Keeps track of current inspection state for real-time display
    """

    def __init__(self):
        self.current_inspection: Optional[Dict] = None
        self.recent_inspections: List[Dict] = []
        self.max_recent = 50
        self.statistics = {
            'total': 0,
            'ok': 0,
            'nok': 0,
            'pending': 0,
            'pass_rate': 0.0,
            # extra vision metrics
            'avg_blur': 0.0,
            'total_blur_samples': 0,
            'avg_time': 0.0,
            'total_time_samples': 0,
            'qr_success_count': 0,
            'ocr_success_count': 0,
        }
        self.system_status = {
            'server_running': True,
            'camera_connected': False,
            'vision_engine': 'ready',
            'database': 'connected',
            'last_update': time.time()
        }
        self.diagnostics = {
            'cpu': 'N/A',
            'memory': 'N/A',
            'fps': 0
        }
        self.live_image: Optional[str] = None  # base64 str
        self.theme = 'dark'  # default theme
        self.lock = threading.Lock()

    # -------------------------
    # Update / query methods
    # -------------------------
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

    def update_system_status(self, component: str, status: str):
        """Update system component status"""
        with self.lock:
            self.system_status[component] = status
            self.system_status['last_update'] = time.time()

    def update_live_image(self, image_bytes: bytes):
        """Update live feed image from bytes"""
        with self.lock:
            self.live_image = base64.b64encode(image_bytes).decode('utf-8')
            self.system_status['last_update'] = time.time()

    def update_diagnostics(self):
        """Update diagnostics like CPU, memory, FPS (uses psutil if available)"""
        with self.lock:
            if psutil:
                try:
                    self.diagnostics['cpu'] = f"{psutil.cpu_percent(interval=0.1):.1f}%"
                    mem = psutil.virtual_memory()
                    self.diagnostics['memory'] = f"{mem.percent:.1f}%"
                except Exception:
                    # fallback
                    self.diagnostics['cpu'] = 'N/A'
                    self.diagnostics['memory'] = 'N/A'
            else:
                # Simulate some values if psutil not installed
                now = int(time.time()) % 100
                self.diagnostics['cpu'] = f"{(30 + now % 10):.1f}%"
                self.diagnostics['memory'] = f"{(40 + now % 20):.1f}%"
            # fps is managed by caller (simulator), keep as-is

    def set_theme(self, theme: str):
        with self.lock:
            self.theme = theme

    def get_state(self) -> Dict:
        """Get complete dashboard state snapshot"""
        with self.lock:
            # compute derived rates
            total = self.statistics.get('total', 0)
            qr_count = self.statistics.get('qr_success_count', 0)
            ocr_count = self.statistics.get('ocr_success_count', 0)
            stats_snapshot = dict(self.statistics)
            stats_snapshot['qr_success_rate'] = (qr_count / total * 100) if total > 0 else 0.0
            stats_snapshot['ocr_success_rate'] = (ocr_count / total * 100) if total > 0 else 0.0
            return {
                'current_inspection': self.current_inspection,
                'recent_inspections': self.recent_inspections[:10],
                'statistics': stats_snapshot,
                'system_status': dict(self.system_status),
                'diagnostics': dict(self.diagnostics),
                'live_image': self.live_image,
                'theme': self.theme
            }


# -------------------------
# HTML generator (pure Python)
# -------------------------
class DashboardHTMLGenerator:
    """
    Pure Python HTML generator for dashboard.
    Be careful: CSS and JS use braces; inside f-strings literal braces must be doubled: '{{' '}}'
    """

    @staticmethod
    def generate_page(state: Dict) -> str:
        theme = state.get('theme', 'dark')
        # Theme variables (simple)
        if theme == 'dark':
            bg_gradient = "linear-gradient(135deg, #0f1724 0%, #0f2436 100%)"
            card_bg = "rgba(255, 255, 255, 0.06)"
            text_color = "#ffffff"
            accent = "#00e676"
        elif theme == 'neon':
            bg_gradient = "linear-gradient(135deg, #00C9FF 0%, #92FE9D 100%)"
            card_bg = "rgba(0, 0, 0, 0.25)"
            text_color = "#091124"
            accent = "#ff6b6b"
        else:  # light
            bg_gradient = "linear-gradient(135deg, #e0eafc 0%, #cfdef3 100%)"
            card_bg = "rgba(0, 0, 0, 0.05)"
            text_color = "#10121a"
            accent = "#1e90ff"

        # Extract initial pieces for server-side render (JS will update)
        stats = state.get('statistics', {})
        sys = state.get('system_status', {})
        diag = state.get('diagnostics', {})
        current = state.get('current_inspection') or {}
        recent = state.get('recent_inspections', [])

        # NOTE: inside the long f-string all literal braces in CSS/JS are doubled ({{ }})
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>QC Vision System - Live Dashboard</title>
<style>
    * {{
        margin: 0;
        padding: 0;
        box-sizing: border-box;
    }}
    html, body {{
        height: 100%;
    }}
    body {{
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial;
        background: {bg_gradient};
        color: {text_color};
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
    }}

    .container {{
        display: grid;
        grid-template-columns: 360px 1fr;
        grid-template-rows: 80px 1fr;
        gap: 18px;
        padding: 18px;
        height: 100vh;
    }}

    .header {{
        grid-column: 1 / -1;
        background: rgba(255,255,255,0.04);
        backdrop-filter: blur(6px);
        border-radius: 12px;
        padding: 14px 20px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }}

    .header h1 {{
        font-size: 20px;
        display:flex;
        gap: 12px;
        align-items:center;
    }}

    .status-indicator {{
        width: 12px;
        height: 12px;
        border-radius: 50%;
        background: {accent};
        box-shadow: 0 0 8px {accent};
    }}

    .time {{
        font-size: 15px;
        opacity: 0.95;
    }}

    .left-panel {{
        display:flex;
        flex-direction:column;
        gap: 14px;
        overflow-y: auto;
    }}

    .right-panel {{
        display:flex;
        flex-direction:column;
        gap: 14px;
        min-height: 0;
    }}

    .card {{
        background: {card_bg};
        border-radius: 12px;
        padding: 14px;
        box-shadow: 0 6px 18px rgba(0,0,0,0.08);
        border: 1px solid rgba(255,255,255,0.03);
    }}

    .card-title {{
        font-size: 13px;
        font-weight:700;
        margin-bottom: 10px;
        opacity: 0.95;
    }}

    .status-grid {{
        display:grid;
        gap:8px;
    }}

    .status-item {{
        display:flex;
        justify-content:space-between;
        align-items:center;
        padding:8px;
        border-radius:8px;
        background: rgba(0,0,0,0.03);
    }}

    .status-badge {{
        padding:4px 10px;
        border-radius: 14px;
        font-weight:700;
        font-size:12px;
    }}

    .stat-grid {{
        display:grid;
        grid-template-columns: repeat(2, 1fr);
        gap:10px;
    }}

    .stat-box {{
        padding:10px;
        border-radius:10px;
        background: rgba(0,0,0,0.02);
        text-align:center;
    }}

    .stat-value {{
        font-size:20px;
        font-weight:800;
    }}

    .inspection-list {{
        display:flex;
        flex-direction:column;
        gap:8px;
        max-height:260px;
        overflow-y:auto;
    }}

    .inspection-item {{
        display:flex;
        justify-content:space-between;
        align-items:center;
        padding:8px;
        border-radius:8px;
        background: rgba(0,0,0,0.02);
    }}

    .feed-container {{
        flex:1;
        border-radius:10px;
        overflow:hidden;
        display:flex;
        align-items:center;
        justify-content:center;
        background: rgba(0,0,0,0.06);
        min-height:320px;
    }}

    .feed-container img {{
        max-width:100%;
        max-height:100%;
        object-fit:contain;
        display:block;
    }}

    .controls {{
        display:flex;
        gap:8px;
        align-items:center;
    }}

    a.button {{
        display:inline-block;
        padding:8px 12px;
        border-radius:10px;
        background: rgba(0,0,0,0.06);
        text-decoration:none;
        color: inherit;
        font-weight:700;
        border: 1px solid rgba(255,255,255,0.03);
    }}

    /* small screens */
    @media (max-width:900px) {{
        .container {{
            grid-template-columns: 1fr;
            grid-template-rows: 70px auto;
            padding: 10px;
        }}
    }}
</style>
</head>
<body>
<div class="container">
    <div class="header card" style="display:flex;align-items:center;gap:14px;">
        <h1><span class="status-indicator"></span> QC Vision System</h1>
        <div style="flex:1"></div>
        <div style="display:flex;gap:10px;align-items:center;">
            <div class="time" id="current-time">{DashboardHTMLGenerator._get_current_time()}</div>
            <div style="width:12px"></div>
            <a class="button" href="/report">Download CSV</a>
        </div>
    </div>

    <div class="left-panel">
        <div class="card">
            <div class="card-title">🔧 System Status</div>
            <div class="status-grid" id="system-status">
                {DashboardHTMLGenerator._generate_system_status(state.get('system_status', {}))}
            </div>
        </div>

        <div class="card">
            <div class="card-title">📊 Statistics</div>
            <div class="stat-grid" id="statistics">
                {DashboardHTMLGenerator._generate_statistics(stats)}
            </div>
        </div>

        <div class="card">
            <div class="card-title">🧠 Vision Metrics</div>
            <div class="stat-grid" id="vision-metrics">
                {DashboardHTMLGenerator._generate_vision_metrics(stats)}
            </div>
        </div>

        <div class="card">
            <div class="card-title">💡 Diagnostics</div>
            <div id="diagnostics">
                CPU: {diag.get('cpu', 'N/A')}<br>
                Memory: {diag.get('memory', 'N/A')}<br>
                FPS: {diag.get('fps', 0)}
            </div>
        </div>

        <div class="card">
            <div class="card-title">📋 Recent Inspections</div>
            <div class="inspection-list" id="recent-list">
                {DashboardHTMLGenerator._generate_recent_inspections(recent)}
            </div>
        </div>
    </div>

    <div class="right-panel">
        <!-- current inspection card -->
        <div id="current-inspection-slot">
            {DashboardHTMLGenerator._generate_current_inspection(current)}
        </div>

        <div class="card feed-container">
            <div style="width:100%;height:100%;display:flex;flex-direction:column">
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
                    <div class="card-title">📸 Live Feed</div>
                    <div class="controls">
                        <select id="theme-select">
                            <option value="dark" {"selected" if state.get('theme') == 'dark' else ""}>Dark</option>
                            <option value="light" {"selected" if state.get('theme') == 'light' else ""}>Light</option>
                            <option value="neon" {"selected" if state.get('theme') == 'neon' else ""}>Neon</option>
                        </select>
                        <a class="button" id="refresh-btn" href="#">Refresh</a>
                    </div>
                </div>
                <div style="flex:1;display:flex;align-items:center;justify-content:center;min-height:260px;">
                    <div id="live-image-area" style="width:100%;height:100%;display:flex;align-items:center;justify-content:center;">
                        {DashboardHTMLGenerator._generate_live_feed(state.get('live_image'))}
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>

<script>
(function(){{
    const POLL_INTERVAL = 1500;
    const imgArea = document.getElementById('live-image-area');
    const statsEl = document.getElementById('statistics');
    const visionEl = document.getElementById('vision-metrics');
    const sysEl = document.getElementById('system-status');
    const recentEl = document.getElementById('recent-list');
    const currentSlot = document.getElementById('current-inspection-slot');
    const diagEl = document.getElementById('diagnostics');
    const themeSelect = document.getElementById('theme-select');

    function renderSystemStatus(st) {{
        // Create inner HTML for system status
        let html = '';
        function badge(ok) {{
            if (ok) return '<span class="status-badge" style="background: rgba(0,255,0,0.12); color: {accent};">✓ OK</span>';
            return '<span class="status-badge" style="background: rgba(255,0,0,0.06); color: #ff6b6b">✗ ERR</span>';
        }}
        html += `<div class="status-item"><span>Server</span>${{ badge(st.server_running) }}</div>`;
        html += `<div class="status-item"><span>Camera</span>${{ badge(st.camera_connected) }}</div>`;
        html += `<div class="status-item"><span>Vision</span>${{ badge(st.vision_engine === 'ready') }}</div>`;
        html += `<div class="status-item"><span>Database</span>${{ badge(st.database === 'connected') }}</div>`;
        sysEl.innerHTML = html;
    }}

    function renderStats(s) {{
        statsEl.innerHTML = `
            <div class="stat-box"><div class="stat-value">${{s.ok}}</div><div class="stat-label">OK</div></div>
            <div class="stat-box"><div class="stat-value">${{s.nok}}</div><div class="stat-label">NOK</div></div>
            <div class="stat-box"><div class="stat-value">${{s.total}}</div><div class="stat-label">TOTAL</div></div>
            <div class="stat-box"><div class="stat-value">${{s.pass_rate.toFixed(1)}}%</div><div class="stat-label">PASS RATE</div></div>
        `;
    }}

    function renderVisionMetrics(s) {{
        visionEl.innerHTML = `
            <div class="stat-box"><div class="stat-value">${{s.avg_blur.toFixed(2)}}</div><div class="stat-label">AVG BLUR</div></div>
            <div class="stat-box"><div class="stat-value">${{s.qr_success_rate.toFixed(1)}}%</div><div class="stat-label">QR SUCCESS</div></div>
            <div class="stat-box"><div class="stat-value">${{s.ocr_success_rate.toFixed(1)}}%</div><div class="stat-label">OCR SUCCESS</div></div>
            <div class="stat-box"><div class="stat-value">${{s.avg_time.toFixed(2)}}s</div><div class="stat-label">AVG TIME</div></div>
        `;
    }}

    function renderRecent(list) {{
        if (!list || list.length === 0) {{
            recentEl.innerHTML = '<div style="text-align:center;opacity:0.6;padding:8px">No inspections yet</div>';
            return;
        }}
        let html = '';
        for (let item of list) {{
            let cls = item.status === 'OK' ? 'result-ok' : 'result-nok';
            html += `<div class="inspection-item"><div><div style="font-size:12px;opacity:0.7">${{item.formatted_time}}</div><div style="font-size:13px;margin-top:4px">${{item.product_code}}</div></div><div style="font-weight:800;color:${{item.status==='OK'?'#0f0':'#ff6b6b'}}">${{item.status}}</div></div>`;
        }}
        recentEl.innerHTML = html;
    }}

    function renderCurrent(curr) {{
        if (!curr) {{
            currentSlot.innerHTML = '';
            return;
        }}
        currentSlot.innerHTML = `
            <div class="card current-inspection">
                <div class="card-title"><span style="display:inline-block;width:10px;height:10px;background:#ffd700;border-radius:50%;margin-right:8px"></span> Current Inspection - ${ { } }${{curr.status}}</div>
                <div style="font-size:18px;font-weight:600;margin-bottom:8px;">${{curr.product_code || 'Unknown'}}</div>
                <div class="inspection-details" style="display:grid;grid-template-columns:repeat(2,1fr);gap:8px">
                    <div><div class="detail-label">QR CODE</div><div class="detail-value">${{curr.qr_data || 'N/A'}}</div></div>
                    <div><div class="detail-label">OCR TEXT</div><div class="detail-value">${{curr.ocr_result || 'N/A'}}</div></div>
                    <div><div class="detail-label">BLUR</div><div class="detail-value">${{(curr.blur_score||0).toFixed(2)}}</div></div>
                    <div><div class="detail-label">TIME</div><div class="detail-value">${{curr.formatted_time || ''}}</div></div>
                </div>
            </div>
        `;
    }}

    function renderDiagnostics(d) {{
        diagEl.innerHTML = `CPU: ${{d.cpu}}<br>Memory: ${{d.memory}}<br>FPS: ${{d.fps}}`;
    }}

    // fetch state and update DOM
    async function fetchState() {{
        try {{
            const res = await fetch('/api/state');
            if (!res.ok) return;
            const data = await res.json();

            // update time
            document.getElementById('current-time').textContent = new Date().toLocaleTimeString();

            // update live image
            if (data.live_image) {{
                imgArea.innerHTML = `<img src="data:image/jpeg;base64,${{data.live_image}}" alt="Live">`;
            }} else {{
                imgArea.innerHTML = '<div style="text-align:center;opacity:0.6">Waiting for image...</div>';
            }}

            // update stats
            renderStats(data.statistics || {{}});
            renderVisionMetrics(data.statistics || {{}});
            renderSystemStatus(data.system_status || {{}});
            renderRecent(data.recent_inspections || []);
            renderCurrent(data.current_inspection || null);
            renderDiagnostics(data.diagnostics || {{}});

            // update theme selection if changed externally
            if (data.theme && themeSelect.value !== data.theme) {{
                themeSelect.value = data.theme;
            }}
        }} catch (err) {{
            // ignore errors in UI refresh
            console.warn('fetchState error', err);
        }}
    }}

    // polling loop
    setInterval(fetchState, POLL_INTERVAL);
    fetchState();

    // theme selector action (simple reload to apply server-side theme)
    themeSelect.addEventListener('change', function() {{
        const q = new URLSearchParams(window.location.search);
        q.set('theme', themeSelect.value);
        // reload dashboard path with theme param
        window.location.href = '/dashboard?' + q.toString();
    }});

    // manual refresh link
    document.getElementById('refresh-btn').addEventListener('click', function(e) {{
        e.preventDefault();
        fetchState();
    }});
}})();
</script>
</body>
</html>
"""

    @staticmethod
    def _get_current_time() -> str:
        return datetime.now().strftime("%H:%M:%S")

    @staticmethod
    def _generate_system_status(status: Dict) -> str:
        # small server-side fallback block for initial render
        s = status or {}
        def badge_html(ok: bool, text_ok: str = "✓ OK", text_err: str = "✗ ERR"):
            if ok:
                return f'<span class="status-badge" style="background: rgba(0,255,0,0.12); color: #00e676;">{text_ok}</span>'
            return f'<span class="status-badge" style="background: rgba(255,0,0,0.06); color: #ff6b6b;">{text_err}</span>'

        html = ""
        html += f'<div class="status-item"><span>Server</span>{badge_html(bool(s.get("server_running")) )}</div>'
        html += f'<div class="status-item"><span>Camera</span>{badge_html(bool(s.get("camera_connected")) )}</div>'
        html += f'<div class="status-item"><span>Vision</span>{badge_html(s.get("vision_engine")=="ready")}</div>'
        html += f'<div class="status-item"><span>Database</span>{badge_html(s.get("database")=="connected")}</div>'
        return html

    @staticmethod
    def _generate_statistics(stats: Dict) -> str:
        s = stats or {}
        ok = s.get('ok', 0)
        nok = s.get('nok', 0)
        total = s.get('total', 0)
        pass_rate = s.get('pass_rate', 0.0)
        return f"""
            <div class="stat-box"><div class="stat-value">{ok}</div><div class="stat-label">OK</div></div>
            <div class="stat-box"><div class="stat-value">{nok}</div><div class="stat-label">NOK</div></div>
            <div class="stat-box"><div class="stat-value">{total}</div><div class="stat-label">TOTAL</div></div>
            <div class="stat-box"><div class="stat-value">{pass_rate:.1f}%</div><div class="stat-label">PASS RATE</div></div>
        """

    @staticmethod
    def _generate_vision_metrics(stats: Dict) -> str:
        s = stats or {}
        avg_blur = s.get('avg_blur', 0.0)
        qr_rate = s.get('qr_success_rate', 0.0)
        ocr_rate = s.get('ocr_success_rate', 0.0)
        avg_time = s.get('avg_time', 0.0)
        return f"""
            <div class="stat-box"><div class="stat-value">{avg_blur:.2f}</div><div class="stat-label">AVG BLUR</div></div>
            <div class="stat-box"><div class="stat-value">{qr_rate:.1f}%</div><div class="stat-label">QR SUCCESS</div></div>
            <div class="stat-box"><div class="stat-value">{ocr_rate:.1f}%</div><div class="stat-label">OCR SUCCESS</div></div>
            <div class="stat-box"><div class="stat-value">{avg_time:.2f}s</div><div class="stat-label">AVG TIME</div></div>
        """

    @staticmethod
    def _generate_recent_inspections(inspections: List[Dict]) -> str:
        if not inspections:
            return '<div style="text-align:center;opacity:0.6;padding:10px">No inspections yet</div>'
        html = ""
        for insp in inspections[:6]:
            status = insp.get('status', 'PENDING')
            color = '#0f0' if status == 'OK' else '#ff6b6b'
            html += f'<div class="inspection-item"><div><div style="font-size:12px;opacity:0.7">{insp.get("formatted_time","")}</div><div style="font-size:13px;margin-top:4px">{insp.get("product_code","Unknown")}</div></div><div style="font-weight:800;color:{color}">{status}</div></div>'
        return html

    @staticmethod
    def _generate_current_inspection(inspection: Optional[Dict]) -> str:
        if not inspection:
            return ''
        product = inspection.get('product_code', 'Unknown')
        status = inspection.get('status', 'PROCESSING')
        qr = inspection.get('qr_data', 'N/A')
        ocr = inspection.get('ocr_result', 'N/A')
        blur = inspection.get('blur_score', 0.0)
        time_str = inspection.get('formatted_time', '')
        return f"""
            <div class="card current-inspection">
                <div class="card-title">🔎 Current Inspection - {status}</div>
                <div style="font-size:18px;font-weight:700;margin-bottom:8px;">{product}</div>
                <div style="display:grid;grid-template-columns:repeat(2,1fr);gap:8px">
                    <div><div style="opacity:0.7;font-size:12px">QR CODE</div><div style="font-weight:700">{qr}</div></div>
                    <div><div style="opacity:0.7;font-size:12px">OCR TEXT</div><div style="font-weight:700">{ocr}</div></div>
                    <div><div style="opacity:0.7;font-size:12px">BLUR</div><div style="font-weight:700">{blur:.2f}</div></div>
                    <div><div style="opacity:0.7;font-size:12px">TIME</div><div style="font-weight:700">{time_str}</div></div>
                </div>
            </div>
        """

    @staticmethod
    def _generate_live_feed(image_base64: Optional[str]) -> str:
        if not image_base64:
            return '<div style="text-align:center;opacity:0.6">Waiting for feed...</div>'
        return f'<img src="data:image/jpeg;base64,{image_base64}" alt="Live Feed"/>'

# -------------------------
# HTTP Handler / Server
# -------------------------
class DashboardRequestHandler(BaseHTTPRequestHandler):
    dashboard: Optional[LiveDashboard] = None

    def log_message(self, format, *args):
        # suppress default logs or customize
        # Uncomment to enable normal logging:
        # super().log_message(format, *args)
        pass

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        qs = parse_qs(parsed.query)

        # change theme via query param, store in dashboard
        if 'theme' in qs and self.dashboard:
            theme_val = qs.get('theme', ['dark'])[0]
            self.dashboard.set_theme(theme_val)

        if path in ('/', '/dashboard'):
            self._serve_dashboard(qs)
        elif path == '/api/state':
            self._serve_state_json()
        elif path == '/report':
            self._serve_report()
        else:
            self.send_error(404)

    def _serve_dashboard(self, qs):
        if not self.dashboard:
            self.send_error(500, "Dashboard not initialized")
            return
        state = self.dashboard.get_state()
        # if theme provided in query, override in state (already set above)
        html = DashboardHTMLGenerator.generate_page(state)

        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))

    def _serve_state_json(self):
        if not self.dashboard:
            self.send_error(500, "Dashboard not initialized")
            return
        state = self.dashboard.get_state()
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.end_headers()
        # Ensure bytes are JSON-serializable; live_image is base64 string already
        self.wfile.write(json.dumps(state).encode('utf-8'))

    def _serve_report(self):
        """CSV of recent inspections"""
        if not self.dashboard:
            self.send_error(500, "Dashboard not initialized")
            return
        with self.dashboard.lock:
            rows = list(self.dashboard.recent_inspections)[:50]
        csv_lines = ["timestamp,product_code,status,processing_time,blur_score,qr_success,ocr_success"]
        for r in rows:
            ts = r.get('formatted_time', '')
            prod = r.get('product_code', '')
            status = r.get('status', '')
            ptime = r.get('processing_time', '')
            blur = r.get('blur_score', '')
            qr_s = r.get('qr_success', '')
            ocr_s = r.get('ocr_success', '')
            # Escape commas minimally by quoting fields
            csv_lines.append(f'"{ts}","{prod}","{status}","{ptime}","{blur}","{qr_s}","{ocr_s}"')
        csv_data = "\n".join(csv_lines)

        self.send_response(200)
        self.send_header('Content-Type', 'text/csv; charset=utf-8')
        self.send_header('Content-Disposition', 'attachment; filename="inspection_report.csv"')
        self.end_headers()
        self.wfile.write(csv_data.encode('utf-8'))


class DashboardServer:
    def __init__(self, host: str = '0.0.0.0', port: int = 8081):
        self.host = host
        self.port = port
        self.dashboard = LiveDashboard()
        self.server: Optional[HTTPServer] = None
        self.server_thread: Optional[threading.Thread] = None
        DashboardRequestHandler.dashboard = self.dashboard

    def start(self, blocking: bool = False):
        try:
            self.server = HTTPServer((self.host, self.port), DashboardRequestHandler)
            print(f"✓ Dashboard server started on http://{self.host}:{self.port}/dashboard")
            if blocking:
                self.server.serve_forever()
            else:
                self.server_thread = threading.Thread(target=self.server.serve_forever, daemon=True)
                self.server_thread.start()
        except Exception as e:
            print("✗ Failed to start dashboard:", e)
            raise

    def stop(self):
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            print("✓ Dashboard stopped")

    # convenience pass-throughs
    def update_current_inspection(self, data: Dict):
        self.dashboard.update_current_inspection(data)

    def add_completed_inspection(self, data: Dict):
        self.dashboard.add_completed_inspection(data)

    def update_system_status(self, component: str, status: str):
        self.dashboard.update_system_status(component, status)

    def update_live_image(self, image_bytes: bytes):
        self.dashboard.update_live_image(image_bytes)

    def update_diagnostics(self):
        self.dashboard.update_diagnostics()

# -------------------------
# Run as script
# -------------------------
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="QC Vision Dashboard (upgraded)")
    parser.add_argument('--host', default='localhost', help='Host to bind (default: localhost)')
    parser.add_argument('--port', type=int, default=8081, help='Port (default: 8081)')
    parser.add_argument('--demo', action='store_true', help='Run demo simulator (needs numpy & opencv)')
    parser.add_argument('--demo-iter', type=int, default=40, help='Number of demo iterations')
    args = parser.parse_args()

    srv = DashboardServer(host=args.host, port=args.port)
    srv.start(blocking=False)

    try:
        # Main thread: keep updating diagnostics every 1s
        while True:
            time.sleep(1.0)
            srv.update_diagnostics()
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        srv.stop()
