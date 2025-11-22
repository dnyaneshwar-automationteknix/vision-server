"""
Enhanced Dashboard - Complete State Management
Tracks: Inspections, Statistics, System Status, Alerts
"""

import threading
import time
from typing import Dict, List
from datetime import datetime


class EnhancedDashboardComplete:
    """
    Enhanced dashboard with comprehensive state tracking
    """
    
    def __init__(self):
        self.current_inspection = None
        self.recent_inspections = []
        self.max_recent = 100
        
        self.statistics = {
            'total': 0,
            'ok': 0,
            'nok': 0,
            'pending': 0,
            'pass_rate': 0.0,
            'avg_blur': 0.0,
            'total_blur_samples': 0,
            'avg_time': 0.0,
            'total_time_samples': 0,
            'qr_success_count': 0,
            'ocr_success_count': 0,
            'color_detection_count': 0
        }
        
        self.system_status = {
            'server_running': False,
            'camera_connected': False,
            'vision_engine': 'initializing',
            'color_detection': 'initializing',
            'database': 'disconnected',
            'last_update': time.time()
        }
        
        self.current_user = 'admin'
        self.alerts = []
        self.lock = threading.Lock()
    
    def add_alert(self, message: str, alert_type: str = 'info'):
        """
        Add system alert
        
        Args:
            message: Alert message
            alert_type: 'info', 'warning', 'error', 'success'
        """
        with self.lock:
            self.alerts.insert(0, {
                'message': message,
                'type': alert_type,
                'timestamp': datetime.now().strftime("%H:%M:%S")
            })
            if len(self.alerts) > 20:
                self.alerts = self.alerts[:20]
    
    def update_system_status(self, component: str, status: str):
        """
        Update system component status
        
        Args:
            component: Component name
            status: Status value
        """
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
        """
        Add completed inspection and update statistics
        
        Args:
            inspection: Inspection data dictionary
        """
        with self.lock:
            # Add to recent inspections
            entry = {
                **inspection,
                'timestamp': time.time(),
                'formatted_time': inspection.get('formatted_time') or 
                                 datetime.now().strftime("%H:%M:%S")
            }
            self.recent_inspections.insert(0, entry)
            
            if len(self.recent_inspections) > self.max_recent:
                self.recent_inspections = self.recent_inspections[:self.max_recent]
            
            # Update statistics
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
            
            # Vision metrics
            blur = inspection.get('blur_score')
            if blur is not None:
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
            
            # Detection success counters
            if inspection.get('qr_success'):
                self.statistics['qr_success_count'] += 1
            
            if inspection.get('ocr_success'):
                self.statistics['ocr_success_count'] += 1
            
            if inspection.get('color_detection'):
                self.statistics['color_detection_count'] += 1
            
            self.system_status['last_update'] = time.time()
    
    def get_state_summary(self) -> Dict:
        """Get complete dashboard state"""
        with self.lock:
            return {
                'statistics': self.statistics.copy(),
                'system_status': self.system_status.copy(),
                'recent_inspections': self.recent_inspections[:10],
                'current_inspection': self.current_inspection,
                'alerts': self.alerts[:10],
                'current_user': self.current_user
            }
    
    def reset_statistics(self):
        """Reset all statistics"""
        with self.lock:
            self.statistics = {
                'total': 0,
                'ok': 0,
                'nok': 0,
                'pending': 0,
                'pass_rate': 0.0,
                'avg_blur': 0.0,
                'total_blur_samples': 0,
                'avg_time': 0.0,
                'total_time_samples': 0,
                'qr_success_count': 0,
                'ocr_success_count': 0,
                'color_detection_count': 0
            }
            self.add_alert("Statistics reset", "info")
    
    def clear_inspections(self):
        """Clear recent inspections"""
        with self.lock:
            self.recent_inspections = []
            self.add_alert("Inspection history cleared", "info")


if __name__ == "__main__":
    print("Enhanced Dashboard Complete - Initialized")
    dashboard = EnhancedDashboardComplete()
    print("✓ Ready for state management")