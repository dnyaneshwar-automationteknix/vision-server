"""
Automated Setup Script for QC Vision System
Checks dependencies, creates initial data, and verifies installation
"""

import subprocess
import sys
from pathlib import Path
import platform


class SetupManager:
    """Manages system setup and dependency checking"""
    
    def __init__(self):
        self.os_type = platform.system()
        self.python_version = sys.version_info
        self.issues = []
        self.warnings = []
        
    def print_header(self):
        """Print setup header"""
        print("=" * 70)
        print("🚀 QC Vision System - Automated Setup")
        print("=" * 70)
        print(f"\nPlatform: {self.os_type}")
        print(f"Python: {self.python_version.major}.{self.python_version.minor}.{self.python_version.micro}\n")
    
    def check_python_version(self):
        """Check if Python version is compatible"""
        print("🐍 Checking Python version...")
        
        if self.python_version.major < 3 or (self.python_version.major == 3 and self.python_version.minor < 8):
            self.issues.append("Python 3.8 or higher required")
            print("  ✗ Python version too old")
            return False
        else:
            print(f"  ✓ Python {self.python_version.major}.{self.python_version.minor}.{self.python_version.micro}")
            return True
    
    def check_pip(self):
        """Check if pip is available"""
        print("\n📦 Checking pip...")
        
        try:
            import pip
            print(f"  ✓ pip is available")
            return True
        except ImportError:
            self.issues.append("pip not found")
            print("  ✗ pip not installed")
            return False
    
    def install_package(self, package_name, import_name=None):
        """Install a Python package"""
        if import_name is None:
            import_name = package_name
        
        try:
            __import__(import_name)
            print(f"  ✓ {package_name} already installed")
            return True
        except ImportError:
            print(f"  📥 Installing {package_name}...")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
                print(f"  ✓ {package_name} installed successfully")
                return True
            except subprocess.CalledProcessError:
                self.warnings.append(f"Failed to install {package_name}")
                print(f"  ⚠️ Failed to install {package_name}")
                return False
    
    def install_dependencies(self):
        """Install all required dependencies"""
        print("\n📚 Installing dependencies...")
        
        # Required packages
        required = [
            ("opencv-python", "cv2"),
            ("numpy", "numpy"),
        ]
        
        # Optional packages
        optional = [
            ("pyzbar", "pyzbar"),
            ("pytesseract", "pytesseract"),
            ("openpyxl", "openpyxl"),
            ("reportlab", "reportlab"),
        ]
        
        print("\n  Required packages:")
        for package, import_name in required:
            if not self.install_package(package, import_name):
                self.issues.append(f"Required package {package} failed to install")
        
        print("\n  Optional packages (for full features):")
        for package, import_name in optional:
            self.install_package(package, import_name)
    
    def create_directories(self):
        """Create necessary directories"""
        print("\n📁 Creating directories...")
        
        directories = [
            "config",
            "inspections/images",
            "inspections/thumbnails",
            "reports",
            "backups",
            "logs",
            "test_data/sample_images"
        ]
        
        for dir_path in directories:
            path = Path(dir_path)
            path.mkdir(parents=True, exist_ok=True)
            print(f"  ✓ {dir_path}")
    
    def setup_database(self):
        """Initialize database with demo data"""
        print("\n💾 Setting up database...")
        
        try:
            from database import QCDatabase
            
            db = QCDatabase("production_qc.db")
            
            # Check if already setup
            existing_products = db.list_products()
            if existing_products:
                print(f"  ℹ️  Database already has {len(existing_products)} products")
                db.close()
                return
            
            # Add demo products
            products = [
                {
                    'code': 'WIDGET-001',
                    'name': 'Red Widget',
                    'qr': 'QR-WIDGET-.*',
                    'ocr': 'LOT2024'
                },
                {
                    'code': 'WIDGET-002',
                    'name': 'Green Widget',
                    'qr': 'QR-WIDGET-.*',
                    'ocr': 'LOT2024'
                },
                {
                    'code': 'WIDGET-003',
                    'name': 'Blue Widget',
                    'qr': 'QR-WIDGET-.*',
                    'ocr': 'LOT2024'
                }
            ]
            
            for p in products:
                db.add_product(
                    product_code=p['code'],
                    product_name=p['name'],
                    qr_pattern=p['qr'],
                    ocr_expected=p['ocr']
                )
                print(f"  ✓ Added product: {p['code']}")
            
            # Add demo users
            import hashlib
            password_hash = hashlib.sha256('admin'.encode()).hexdigest()
            
            db.add_user('admin', password_hash, 'ADMIN')
            db.add_user('operator', password_hash, 'OPERATOR')
            
            print(f"  ✓ Added demo users")
            
            db.close()
            print(f"  ✓ Database initialized")
        
        except Exception as e:
            self.warnings.append(f"Database setup failed: {str(e)}")
            print(f"  ⚠️ Database setup failed: {e}")
    
    def verify_modules(self):
        """Verify all Python modules are present"""
        print("\n🔍 Verifying modules...")
        
        modules = [
            "database.py",
            "config_manager.py",
            "management/vision_engine.py",
            "management/communication.py",
            "web_dashboard.py",
            "enhanced_dashboard.py",
            "report_generator.py",
            "pi_camera_module.py",
            "complete_system.py"
        ]
        
        all_present = True
        for module in modules:
            if Path(module).exists():
                print(f"  ✓ {module}")
            else:
                print(f"  ✗ {module} (missing)")
                self.issues.append(f"Module {module} not found")
                all_present = False
        
        return all_present
    
    def test_import(self):
        """Test importing all modules"""
        print("\n🧪 Testing imports...")
        
        modules = [
            ("database", "QCDatabase"),
            ("config_manager", "ConfigManager"),
            ("management/vision_engine", "VisionEngine"),
            ("management/communication", "QCServer"),
            ("report_generator", "ReportGenerator"),
            ("pi_camera_module", "CameraManager")
        ]
        
        all_ok = True
        for module_name, class_name in modules:
            try:
                module = __import__(module_name)
                getattr(module, class_name)
                print(f"  ✓ {module_name}.{class_name}")
            except Exception as e:
                print(f"  ✗ {module_name}.{class_name}: {e}")
                self.warnings.append(f"Import failed: {module_name}")
                all_ok = False
        
        return all_ok
    
    def print_summary(self):
        """Print setup summary"""
        print("\n" + "=" * 70)
        print("📋 Setup Summary")
        print("=" * 70)
        
        if not self.issues:
            print("\n✅ Setup completed successfully!")
            print("\nNo critical issues found.")
        else:
            print("\n❌ Setup completed with issues:")
            for issue in self.issues:
                print(f"  • {issue}")
        
        if self.warnings:
            print("\n⚠️ Warnings:")
            for warning in self.warnings:
                print(f"  • {warning}")
        
        print("\n" + "=" * 70)
        print("🚀 Next Steps")
        print("=" * 70)
        
        if not self.issues:
            print("\n1. Run the system:")
            print("   python complete_system.py")
            print("\n2. Open browser:")
            print("   http://localhost:8081/dashboard")
            print("\n3. Default login:")
            print("   Username: admin")
            print("   Password: admin")
        else:
            print("\n⚠️ Please fix the issues above before running the system.")
        
        print("\n" + "=" * 70)
    
    def run_setup(self):
        """Run complete setup process"""
        self.print_header()
        
        # Check Python
        if not self.check_python_version():
            print("\n❌ Python version check failed. Please upgrade Python.")
            return False
        
        # Check pip
        if not self.check_pip():
            print("\n❌ pip is required. Please install pip.")
            return False
        
        # Install dependencies
        self.install_dependencies()
        
        # Create directories
        self.create_directories()
        
        # Verify modules
        if not self.verify_modules():
            print("\n⚠️ Some modules are missing. Please ensure all files are present.")
        
        # Test imports
        self.test_import()
        
        # Setup database
        self.setup_database()
        
        # Print summary
        self.print_summary()
        
        return len(self.issues) == 0


def main():
    """Main entry point"""
    setup = SetupManager()
    success = setup.run_setup()
    
    if success:
        print("\n🎉 Setup complete! You're ready to go!")
        return 0
    else:
        print("\n⚠️ Setup completed with issues. Please review above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())