"""
QC Vision System - Configuration Manager
Separate configs for Pi and Server
Allows selecting which component to run
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional


class ConfigManager:
    """
    Manages configuration for both Pi and Server
    Each component can be enabled/disabled independently
    """
    
    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        
        self.configs = {
            'pi': None,
            'server': None,
            'vision': None,
            'system': None
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
            # Create default config
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
        
        if config_type == 'pi':
            return {
                "enabled": False,  # Can work without Pi
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
                    "enabled": True,  # Start with mock
                    "sample_images_dir": "test_data/sample_images"
                }
            }
        
        elif config_type == 'server':
            return {
                "enabled": True,  # Server always enabled
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
                    "image_dir": "inspections/images",
                    "thumbnail_dir": "inspections/thumbnails",
                    "max_storage_gb": 10
                },
                "processing": {
                    "max_workers": 4,
                    "timeout_seconds": 30
                }
            }
        
        elif config_type == 'vision':
            return {
                "qr_detection": {
                    "enabled": True,
                    "min_size": 50,
                    "max_detections": 5
                },
                "ocr": {
                    "enabled": True,
                    "language": "eng",
                    "psm": 6,  # Tesseract page segmentation mode
                    "min_confidence": 60
                },
                "color_detection": {
                    "enabled": True,
                    "color_space": "HSV",  # HSV or RGB
                    "tolerance": 30,
                    "min_area_pixels": 100
                },
                "image_quality": {
                    "blur_threshold": 100,  # Laplacian variance
                    "brightness_min": 50,
                    "brightness_max": 200,
                    "auto_reject_blur": True,
                    "auto_reject_brightness": False
                },
                "preprocessing": {
                    "resize_max_width": 1920,
                    "resize_max_height": 1080,
                    "apply_clahe": False,  # Contrast Limited Adaptive Histogram Equalization
                    "denoise": False
                }
            }
        
        elif config_type == 'system':
            return {
                "mode": "server_only",  # Options: "pi_only", "server_only", "both"
                "debug": True,
                "log_level": "INFO",  # DEBUG, INFO, WARNING, ERROR
                "log_file": "logs/qc_system.log",
                "timezone": "UTC",
                "language": "en"
            }
        
        return {}
    
    # ==================== GETTERS ====================
    
    def get(self, config_type: str, key_path: str = None, default: Any = None) -> Any:
        """
        Get configuration value
        Args:
            config_type: 'pi', 'server', 'vision', or 'system'
            key_path: Dot-separated path like 'camera.resolution'
            default: Default value if key not found
        """
        config = self.configs.get(config_type)
        if not config:
            return default
        
        if key_path is None:
            return config
        
        # Navigate nested dict
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
            config_type: 'pi', 'server', 'vision', or 'system'
            key_path: Dot-separated path like 'camera.resolution'
            value: Value to set
        """
        config = self.configs.get(config_type)
        if not config:
            config = {}
            self.configs[config_type] = config
        
        # Navigate and set nested dict
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
        """Check if using mock camera (no real Pi hardware)"""
        return self.get('pi', 'mock_mode.enabled', True)
    
    # ==================== VALIDATION ====================
    
    def validate(self) -> Dict[str, Any]:
        """
        Validate all configurations
        Returns dict with validation results
        """
        issues = []
        warnings = []
        
        # Check mode consistency
        mode = self.get_mode()
        if mode in ['pi_only', 'both']:
            if not self.get('pi', 'enabled'):
                issues.append("Pi mode selected but Pi is not enabled in config")
        
        # Check network settings
        if self.is_pi_enabled():
            server_url = self.get('pi', 'network.server_url')
            if not server_url or server_url == "http://localhost:8080":
                warnings.append("Pi is using localhost - won't work on separate device")
        
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
        """
        Reset configuration to defaults
        Args:
            config_type: Specific config to reset, or None for all
        """
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
        """Ensure directories referenced in configs exist (image dirs, cache, backups, logs)"""
        # server storage
        server_cfg = self.get_server_config() or {}
        storage = server_cfg.get('storage', {})
        image_dir = storage.get('image_dir')
        thumbnail_dir = storage.get('thumbnail_dir')
        if image_dir:
            Path(image_dir).mkdir(parents=True, exist_ok=True)
        if thumbnail_dir:
            Path(thumbnail_dir).mkdir(parents=True, exist_ok=True)

        # pi local cache
        pi_cfg = self.get_pi_config() or {}
        local_cache = pi_cfg.get('local_storage', {})
        cache_dir = local_cache.get('cache_dir')
        if cache_dir:
            Path(cache_dir).mkdir(parents=True, exist_ok=True)

        # db backup dir
        server_db = server_cfg.get('database', {})
        backup_dir = server_db.get('backup_dir')
        if backup_dir:
            Path(backup_dir).mkdir(parents=True, exist_ok=True)

        # logs
        system_cfg = self.get_system_config() or {}
        log_file = system_cfg.get('log_file')
        if log_file:
            Path(log_file).parent.mkdir(parents=True, exist_ok=True)

    def run_component(self, component: str):
        """
        Lightweight dispatcher to start a component.
        component: 'pi' or 'server'
        NOTE: these are stubs — implement actual run loops in separate modules.
        """
        if component == 'pi':
            if not self.is_pi_enabled():
                raise RuntimeError("Pi component is not enabled in configuration.")
            # stub: replace with actual Pi client runner
            print("Starting Pi client (stub) — implement in pi_client.py")
            # Example: import pi_client; pi_client.run(self.get_pi_config())
        elif component == 'server':
            if not self.is_server_enabled():
                raise RuntimeError("Server component is not enabled in configuration.")
            print("Starting Server (stub) — implement in server_app.py")
            # Example: import server_app; server_app.run(self.get_server_config())
        else:
            raise ValueError("Unknown component. Choose 'pi' or 'server'.")

    def print_summary(self):
        """Print configuration summary"""
        print("=" * 60)
        print("QC Vision System - Configuration Summary")
        print("=" * 60)

        mode = self.get_mode()
        print(f"\n🔧 System Mode: {mode.upper()}")
        sys_cfg = self.get_system_config()
        print(f"   Debug: {sys_cfg.get('debug', False)}")
        print(f"   Log level: {sys_cfg.get('log_level', 'INFO')}")
        print(f"   Log file: {sys_cfg.get('log_file')}")

        # Pi
        pi_cfg = self.get_pi_config()
        print("\n🤖 Pi Component:")
        if pi_cfg:
            print(f"   Enabled: {pi_cfg.get('enabled')}")
            mock = pi_cfg.get('mock_mode', {}).get('enabled', False)
            print(f"   Mock camera: {mock}")
            cam = pi_cfg.get('camera', {})
            print(f"   Camera resolution: {cam.get('resolution')} @ {cam.get('framerate')}fps")
            print(f"   Local cache enabled: {pi_cfg.get('local_storage', {}).get('enabled')}")
        else:
            print("   Not configured")

        # Server
        srv_cfg = self.get_server_config()
        print("\n🖥️ Server Component:")
        if srv_cfg:
            api = srv_cfg.get('api', {})
            web = srv_cfg.get('web', {})
            db = srv_cfg.get('database', {})
            st = srv_cfg.get('storage', {})
            print(f"   API: {api.get('host')}:{api.get('port')}, max_conn={api.get('max_connections')}")
            print(f"   Web UI: enabled={web.get('enabled')}, {web.get('host')}:{web.get('port')}")
            print(f"   Database: {db.get('path')}, backups={'on' if db.get('backup_enabled') else 'off'}")
            print(f"   Image storage: {st.get('image_dir')} (max {st.get('max_storage_gb')}GB)")
        else:
            print("   Not configured")

        # Vision
        vis_cfg = self.get_vision_config()
        print("\n🔎 Vision Processing:")
        if vis_cfg:
            qr = vis_cfg.get('qr_detection', {})
            ocr = vis_cfg.get('ocr', {})
            print(f"   QR detection: enabled={qr.get('enabled')}, min_size={qr.get('min_size')}")
            print(f"   OCR: enabled={ocr.get('enabled')}, lang={ocr.get('language')}, min_conf={ocr.get('min_confidence')}")
        else:
            print("   Not configured")

        # Validation summary
        val = self.validate()
        print("\n Validation:")
        print(f"   Valid: {val['valid']}")
        if val['issues']:
            print("   Issues:")
            for i in val['issues']:
                print(f"    - {i}")
        if val['warnings']:
            print("   Warnings:")
            for w in val['warnings']:
                print(f"    - {w}")

        print("\nTo start components call `run_component('server')` or `run_component('pi')`")
        print("=" * 60)


if __name__ == "__main__":
    cfg_mgr = ConfigManager()
    print("Configuration Manager initialized.")

    cfg_mgr.ensure_paths()
    print("Ensured all necessary directories exist.")
    cfg_mgr.print_summary()
    print("Use cfg_mgr.run_component('server') or cfg_mgr.run_component('pi') to start components.")
