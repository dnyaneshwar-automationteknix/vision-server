"""
QC Vision System - Enhanced Configuration Manager
Added: Camera source selection, auto-detection settings, image storage
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional


class ConfigManager:
    """
    Enhanced configuration manager with camera selection and auto-detection
    """
    
    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        
        self.configs = {
            'pi': None,
            'server': None,
            'vision': None,
            'system': None,
            'camera': None  # NEW: Camera-specific config
        }
        
        self._load_all_configs()
    
    def _get_config_path(self, config_type: str) -> Path:
        """Get path for specific config file"""
        return self.config_dir / f"{config_type}_config.json"
    
    def _load_all_configs(self):
        """Load all configuration files"""
        for config_type in self.configs.keys():
            self.configs[config_type] = self._load_config(config_type)
    
    def _load_config(self, config_type: str) -> Dict:
        """Load specific configuration file"""
        config_path = self._get_config_path(config_type)
        
        if config_path.exists():
            with open(config_path, 'r') as f:
                return json.load(f)
        else:
            default_config = self._get_default_config(config_type)
            self._save_config(config_type, default_config)
            return default_config
    
    def _save_config(self, config_type: str, config: Dict):
        """Save configuration to file"""
        config_path = self._get_config_path(config_type)
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=4)
    
    def _get_default_config(self, config_type: str) -> Dict:
        """Get default configuration based on type"""
        
        if config_type == 'camera':
            # NEW: Camera configuration
            return {
                "source": "webcam",  # Options: "webcam", "pc_camera", "pi_camera", "mock"
                "device_index": 0,  # For webcam/PC camera (0, 1, 2...)
                "resolution": {
                    "width": 1280,
                    "height": 720
                },
                "framerate": 30,
                "rotation": 0,
                "flip_horizontal": False,
                "flip_vertical": False,
                "brightness": 128,
                "contrast": 128,
                "saturation": 128,
                "auto_focus": True,
                "auto_white_balance": True,
                "available_sources": [
                    {"id": "webcam", "name": "Webcam", "description": "External USB webcam"},
                    {"id": "pc_camera", "name": "PC Camera", "description": "Built-in laptop camera"},
                    {"id": "pi_camera", "name": "Pi Camera", "description": "Raspberry Pi camera module"},
                    {"id": "mock", "name": "Mock Camera", "description": "Test images"}
                ],
                "save_images": True,
                "save_thumbnails": True,
                "save_annotated": True
            }
        
        elif config_type == 'pi':
            return {
                "enabled": False,
                "camera": {
                    "resolution": [1920, 1080],
                    "framerate": 30,
                    "rotation": 0,
                    "brightness": 50,
                    "contrast": 50
                },
                "capture": {
                    "format": "jpg",
                    "quality": 90,
                    "auto_white_balance": True
                },
                "network": {
                    "server_url": "http://localhost:8080",
                    "timeout": 30,
                    "retry_attempts": 3
                },
                "local_storage": {
                    "enabled": True,
                    "cache_dir": "pi_cache",
                    "max_cache_size_mb": 500
                },
                "mock_mode": {
                    "enabled": True,
                    "sample_images_dir": "test_data/sample_images"
                }
            }
        
        elif config_type == 'server':
            return {
                "enabled": True,
                "api": {
                    "host": "0.0.0.0",
                    "port": 8080,
                    "max_connections": 10
                },
                "web": {
                    "enabled": True,
                    "host": "0.0.0.0",
                    "port": 8081,
                    "refresh_rate_ms": 2000
                },
                "database": {
                    "path": "qc_server.db",
                    "backup_enabled": True,
                    "backup_interval_hours": 24,
                    "backup_dir": "backups"
                },
                "storage": {
                    "image_dir": "data/inspections/images",
                    "thumbnail_dir": "data/inspections/thumbnails",
                    "annotated_dir": "data/inspections/annotated",
                    "max_storage_gb": 10,
                    "auto_cleanup": True,
                    "retention_days": 90
                },
                "processing": {
                    "max_workers": 4,
                    "timeout_seconds": 30
                }
            }
        
        elif config_type == 'vision':
            return {
                "auto_detection": {
                    "enabled": True,
                    "detect_qr": True,
                    "detect_ocr": True,
                    "detect_colors": True,
                    "detect_quality": True
                },
                "qr_detection": {
                    "enabled": True,
                    "min_size": 50,
                    "max_detections": 5,
                    "auto_annotate": True
                },
                "ocr": {
                    "enabled": True,
                    "language": "eng",
                    "psm": 6,
                    "min_confidence": 60,
                    "auto_annotate": True
                },
                "color_detection": {
                    "enabled": True,
                    "color_space": "RGB",
                    "tolerance": 30,
                    "min_area_pixels": 100,
                    "auto_annotate": True,
                    "roi_tools": {
                        "rectangle": True,
                        "circle": True,
                        "polygon": True,
                        "freehand": True,
                        "line": True
                    }
                },
                "image_quality": {
                    "blur_threshold": 100,
                    "brightness_min": 50,
                    "brightness_max": 200,
                    "auto_reject_blur": True,
                    "auto_reject_brightness": False
                },
                "preprocessing": {
                    "resize_max_width": 1920,
                    "resize_max_height": 1080,
                    "apply_clahe": False,
                    "denoise": False
                }
            }
        
        elif config_type == 'system':
            return {
                "mode": "server_only",
                "debug": True,
                "log_level": "INFO",
                "log_file": "logs/qc_system.log",
                "timezone": "UTC",
                "language": "en"
            }
        
        return {}
    
    # ==================== CAMERA CONFIGURATION ====================
    
    def get_camera_config(self) -> Dict:
        """Get camera configuration"""
        return self.configs['camera']
    
    def get_camera_source(self) -> str:
        """Get current camera source"""
        return self.get('camera', 'source', 'webcam')
    
    def set_camera_source(self, source: str):
        """
        Set camera source
        Args:
            source: 'webcam', 'pc_camera', 'pi_camera', or 'mock'
        """
        valid_sources = ['webcam', 'pc_camera', 'pi_camera', 'mock']
        if source not in valid_sources:
            raise ValueError(f"Invalid camera source. Must be one of: {valid_sources}")
        
        self.set('camera', 'source', source)
        print(f"✓ Camera source set to: {source}")
    
    def get_camera_device_index(self) -> int:
        """Get camera device index (for webcam/PC camera)"""
        return self.get('camera', 'device_index', 0)
    
    def set_camera_device_index(self, index: int):
        """Set camera device index"""
        self.set('camera', 'device_index', index)
    
    def get_camera_resolution(self) -> tuple:
        """Get camera resolution (width, height)"""
        res = self.get('camera', 'resolution', {'width': 1280, 'height': 720})
        return (res['width'], res['height'])
    
    def is_image_saving_enabled(self) -> bool:
        """Check if image saving is enabled"""
        return self.get('camera', 'save_images', True)
    
    def is_auto_detection_enabled(self) -> bool:
        """Check if auto-detection is enabled"""
        return self.get('vision', 'auto_detection.enabled', True)
    
    # ==================== GETTERS ====================
    
    def get(self, config_type: str, key_path: str = None, default: Any = None) -> Any:
        """
        Get configuration value
        Args:
            config_type: 'pi', 'server', 'vision', 'system', or 'camera'
            key_path: Dot-separated path like 'camera.resolution'
            default: Default value if key not found
        """
        config = self.configs.get(config_type)
        if not config:
            return default
        
        if key_path is None:
            return config
        
        keys = key_path.split('.')
        value = config
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def get_pi_config(self) -> Dict:
        """Get complete Pi configuration"""
        return self.configs['pi']
    
    def get_server_config(self) -> Dict:
        """Get complete Server configuration"""
        return self.configs['server']
    
    def get_vision_config(self) -> Dict:
        """Get complete Vision configuration"""
        return self.configs['vision']
    
    def get_system_config(self) -> Dict:
        """Get complete System configuration"""
        return self.configs['system']
    
    # ==================== SETTERS ====================
    
    def set(self, config_type: str, key_path: str, value: Any):
        """
        Set configuration value
        Args:
            config_type: 'pi', 'server', 'vision', 'system', or 'camera'
            key_path: Dot-separated path like 'camera.resolution'
            value: Value to set
        """
        config = self.configs.get(config_type)
        if not config:
            config = {}
            self.configs[config_type] = config
        
        keys = key_path.split('.')
        current = config
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        current[keys[-1]] = value
        self._save_config(config_type, config)
    
    # ==================== MODE MANAGEMENT ====================
    
    def get_mode(self) -> str:
        """Get current system mode"""
        return self.get('system', 'mode', 'server_only')
    
    def set_mode(self, mode: str):
        """
        Set system mode
        Args:
            mode: 'pi_only', 'server_only', 'both'
        """
        valid_modes = ['pi_only', 'server_only', 'both']
        if mode not in valid_modes:
            raise ValueError(f"Invalid mode. Must be one of: {valid_modes}")
        
        self.set('system', 'mode', mode)
    
    def is_pi_enabled(self) -> bool:
        """Check if Pi component is enabled"""
        mode = self.get_mode()
        return mode in ['pi_only', 'both'] and self.get('pi', 'enabled', False)
    
    def is_server_enabled(self) -> bool:
        """Check if Server component is enabled"""
        mode = self.get_mode()
        return mode in ['server_only', 'both']
    
    def is_mock_mode(self) -> bool:
        """Check if using mock camera"""
        return self.get_camera_source() == 'mock'
    
    # ==================== VALIDATION ====================
    
    def validate(self) -> Dict[str, Any]:
        """Validate all configurations"""
        issues = []
        warnings = []
        
        # Check camera configuration
        camera_source = self.get_camera_source()
        if camera_source not in ['webcam', 'pc_camera', 'pi_camera', 'mock']:
            issues.append(f"Invalid camera source: {camera_source}")
        
        if camera_source == 'pi_camera' and not self.is_pi_enabled():
            warnings.append("Pi camera selected but Pi component not enabled")
        
        # Check storage paths
        if self.is_server_enabled():
            image_dir = self.get('server', 'storage.image_dir')
            if not Path(image_dir).exists():
                warnings.append(f"Image directory doesn't exist: {image_dir}")
        
        # Check vision dependencies
        if self.get('vision', 'qr_detection.enabled'):
            warnings.append("QR detection requires: pip install opencv-python pyzbar")
        
        if self.get('vision', 'ocr.enabled'):
            warnings.append("OCR requires: pip install pytesseract + Tesseract installation")
        
        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'warnings': warnings
        }
    
    # ==================== UTILITY ====================
    
    def reload(self):
        """Reload all configurations from files"""
        self._load_all_configs()
    
    def reset(self, config_type: str = None):
        """Reset configuration to defaults"""
        if config_type:
            default = self._get_default_config(config_type)
            self._save_config(config_type, default)
            self.configs[config_type] = default
        else:
            for cfg_type in self.configs.keys():
                self.reset(cfg_type)
    
    def export_config(self, export_path: str):
        """Export all configurations to single file"""
        with open(export_path, 'w') as f:
            json.dump(self.configs, f, indent=4)
    
    def ensure_paths(self):
        """Ensure all necessary directories exist"""
        # Server storage
        server_cfg = self.get_server_config() or {}
        storage = server_cfg.get('storage', {})
        
        for dir_key in ['image_dir', 'thumbnail_dir', 'annotated_dir']:
            dir_path = storage.get(dir_key)
            if dir_path:
                Path(dir_path).mkdir(parents=True, exist_ok=True)
        
        # Pi local cache
        pi_cfg = self.get_pi_config() or {}
        cache_dir = pi_cfg.get('local_storage', {}).get('cache_dir')
        if cache_dir:
            Path(cache_dir).mkdir(parents=True, exist_ok=True)
        
        # Database backup
        backup_dir = server_cfg.get('database', {}).get('backup_dir')
        if backup_dir:
            Path(backup_dir).mkdir(parents=True, exist_ok=True)
        
        # Logs
        system_cfg = self.get_system_config() or {}
        log_file = system_cfg.get('log_file')
        if log_file:
            Path(log_file).parent.mkdir(parents=True, exist_ok=True)
    
    def print_summary(self):
        """Print configuration summary"""
        print("=" * 60)
        print("QC Vision System - Configuration Summary")
        print("=" * 60)
        
        # System Mode
        mode = self.get_mode()
        print(f"\n🔧 System Mode: {mode.upper()}")
        
        # Camera Configuration
        camera_cfg = self.get_camera_config()
        print("\n📹 Camera Configuration:")
        print(f"   Source: {camera_cfg.get('source')}")
        print(f"   Device Index: {camera_cfg.get('device_index')}")
        res = camera_cfg.get('resolution', {})
        print(f"   Resolution: {res.get('width')}x{res.get('height')}")
        print(f"   Save Images: {camera_cfg.get('save_images')}")
        print(f"   Save Thumbnails: {camera_cfg.get('save_thumbnails')}")
        print(f"   Save Annotated: {camera_cfg.get('save_annotated')}")
        
        # Vision Configuration
        vision_cfg = self.get_vision_config()
        print("\n🔎 Vision Processing:")
        auto_det = vision_cfg.get('auto_detection', {})
        print(f"   Auto-detection: {auto_det.get('enabled')}")
        print(f"   QR Detection: {auto_det.get('detect_qr')}")
        print(f"   OCR Detection: {auto_det.get('detect_ocr')}")
        print(f"   Color Detection: {auto_det.get('detect_colors')}")
        print(f"   Quality Check: {auto_det.get('detect_quality')}")
        
        # Storage
        server_cfg = self.get_server_config()
        storage = server_cfg.get('storage', {})
        print("\n💾 Storage:")
        print(f"   Images: {storage.get('image_dir')}")
        print(f"   Thumbnails: {storage.get('thumbnail_dir')}")
        print(f"   Annotated: {storage.get('annotated_dir')}")
        print(f"   Max Storage: {storage.get('max_storage_gb')}GB")
        
        # Validation
        val = self.validate()
        print("\n✅ Validation:")
        print(f"   Valid: {val['valid']}")
        if val['issues']:
            print("   Issues:")
            for i in val['issues']:
                print(f"    - {i}")
        if val['warnings']:
            print("   Warnings:")
            for w in val['warnings']:
                print(f"    - {w}")
        
        print("=" * 60)


if __name__ == "__main__":
    cfg = ConfigManager()
    cfg.ensure_paths()
    cfg.print_summary()
    
    print("\n\n📋 Available Commands:")
    print("  cfg.set_camera_source('webcam')  # Set to webcam")
    print("  cfg.set_camera_source('pc_camera')  # Set to PC camera")
    print("  cfg.set_camera_source('pi_camera')  # Set to Pi camera")
    print("  cfg.set_camera_device_index(0)  # Set device index")
    print("  cfg.get_camera_source()  # Get current source")