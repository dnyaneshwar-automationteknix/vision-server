import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Any


class QCDatabase:
    """
    Lightweight SQLite database for QC operations
    Can be used by both Pi (local cache) and Server (main DB)
    """
    
    def __init__(self, db_path: str = "qc_data.db"):
        """
        Initialize database connection
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        self._connect()
        self._initialize_tables()
    
    def _connect(self):
        """Establish database connection"""
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        self.cursor = self.conn.cursor()
    
    def _initialize_tables(self):
        """Create all required tables if they don't exist"""
        
        # Products/Models table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                product_id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_code TEXT UNIQUE NOT NULL,
                product_name TEXT NOT NULL,
                qr_pattern TEXT,
                ocr_expected TEXT,
                color_ranges TEXT,  -- JSON: {color_name: [r_min,r_max,g_min,g_max,b_min,b_max]}
                active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Inspections table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS inspections (
                inspection_id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER,
                qr_data TEXT,
                ocr_result TEXT,
                color_detected TEXT,
                image_path TEXT,
                thumbnail_path TEXT,
                status TEXT CHECK(status IN ('OK', 'NOK', 'PENDING', 'REVIEW')),
                blur_score REAL,
                brightness_score REAL,
                defect_type TEXT,  -- JSON array of defects
                operator_id INTEGER,
                station_id TEXT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                processing_time REAL,  -- seconds
                FOREIGN KEY (product_id) REFERENCES products(product_id),
                FOREIGN KEY (operator_id) REFERENCES users(user_id)
            )
        """)
        
        # Defects detail table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS defects (
                defect_id INTEGER PRIMARY KEY AUTOINCREMENT,
                inspection_id INTEGER,
                defect_category TEXT,  -- QR, OCR, COLOR, BLUR, OTHER
                defect_description TEXT,
                severity TEXT CHECK(severity IN ('CRITICAL', 'MAJOR', 'MINOR')),
                coordinates TEXT,  -- JSON: {x, y, width, height}
                FOREIGN KEY (inspection_id) REFERENCES inspections(inspection_id)
            )
        """)
        
        # Users table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT CHECK(role IN ('OPERATOR', 'SUPERVISOR', 'ADMIN')),
                active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                last_login TEXT
            )
        """)
        
        # System logs
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_logs (
                log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                log_level TEXT CHECK(log_level IN ('INFO', 'WARNING', 'ERROR', 'CRITICAL')),
                module TEXT,
                message TEXT,
                details TEXT,  -- JSON for additional data
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Configuration table (key-value store)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS config (
                config_key TEXT PRIMARY KEY,
                config_value TEXT,
                description TEXT,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        self.conn.commit()
        self._create_indexes()
    
    def _create_indexes(self):
        """Create indexes for better query performance"""
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_inspections_timestamp ON inspections(timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_inspections_status ON inspections(status)",
            "CREATE INDEX IF NOT EXISTS idx_inspections_product ON inspections(product_id)",
            "CREATE INDEX IF NOT EXISTS idx_defects_inspection ON defects(inspection_id)",
            "CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON system_logs(timestamp)"
        ]
        for idx in indexes:
            self.cursor.execute(idx)
        self.conn.commit()
    
    # ==================== PRODUCT OPERATIONS ====================
    
    def add_product(self, product_code: str, product_name: str, 
                   qr_pattern: str = None, ocr_expected: str = None,
                   color_ranges: Dict = None) -> int:
        """Add new product/model"""
        color_json = json.dumps(color_ranges) if color_ranges else None
        
        self.cursor.execute("""
            INSERT INTO products (product_code, product_name, qr_pattern, 
                                ocr_expected, color_ranges)
            VALUES (?, ?, ?, ?, ?)
        """, (product_code, product_name, qr_pattern, ocr_expected, color_json))
        
        self.conn.commit()
        return self.cursor.lastrowid
    
    def get_product(self, product_code: str) -> Optional[Dict]:
        """Get product by code"""
        self.cursor.execute("""
            SELECT * FROM products WHERE product_code = ? AND active = 1
        """, (product_code,))
        
        row = self.cursor.fetchone()
        if row:
            product = dict(row)
            if product['color_ranges']:
                product['color_ranges'] = json.loads(product['color_ranges'])
            return product
        return None
    
    def list_products(self, active_only: bool = True) -> List[Dict]:
        """List all products"""
        query = "SELECT * FROM products"
        if active_only:
            query += " WHERE active = 1"
        
        self.cursor.execute(query)
        return [dict(row) for row in self.cursor.fetchall()]
    
    # ==================== INSPECTION OPERATIONS ====================
    
    def add_inspection(self, product_id: int, qr_data: str = None,
                      ocr_result: str = None, color_detected: str = None,
                      image_path: str = None, status: str = "PENDING",
                      blur_score: float = None, brightness_score: float = None,
                      operator_id: int = None, station_id: str = None,
                      processing_time: float = None) -> int:
        """Add new inspection record"""
        
        self.cursor.execute("""
            INSERT INTO inspections (
                product_id, qr_data, ocr_result, color_detected,
                image_path, status, blur_score, brightness_score,
                operator_id, station_id, processing_time, timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (product_id, qr_data, ocr_result, color_detected, image_path,
              status, blur_score, brightness_score, operator_id, station_id,
              processing_time, datetime.now().isoformat()))
        
        self.conn.commit()
        return self.cursor.lastrowid
    
    def update_inspection_status(self, inspection_id: int, status: str,
                                defect_type: List[str] = None):
        """Update inspection status and defects"""
        defect_json = json.dumps(defect_type) if defect_type else None
        
        self.cursor.execute("""
            UPDATE inspections 
            SET status = ?, defect_type = ?
            WHERE inspection_id = ?
        """, (status, defect_json, inspection_id))
        
        self.conn.commit()
    
    def get_inspection(self, inspection_id: int) -> Optional[Dict]:
        """Get single inspection record"""
        self.cursor.execute("""
            SELECT i.*, p.product_name, p.product_code
            FROM inspections i
            LEFT JOIN products p ON i.product_id = p.product_id
            WHERE i.inspection_id = ?
        """, (inspection_id,))
        
        row = self.cursor.fetchone()
        return dict(row) if row else None
    
    def get_inspections(self, limit: int = 100, status: str = None,
                       start_date: str = None, end_date: str = None) -> List[Dict]:
        """Get inspection records with filters"""
        query = """
            SELECT i.*, p.product_name, p.product_code
            FROM inspections i
            LEFT JOIN products p ON i.product_id = p.product_id
            WHERE 1=1
        """
        params = []
        
        if status:
            query += " AND i.status = ?"
            params.append(status)
        
        if start_date:
            query += " AND i.timestamp >= ?"
            params.append(start_date)
        
        if end_date:
            query += " AND i.timestamp <= ?"
            params.append(end_date)
        
        query += " ORDER BY i.timestamp DESC LIMIT ?"
        params.append(limit)
        
        self.cursor.execute(query, params)
        return [dict(row) for row in self.cursor.fetchall()]
    
    # ==================== DEFECT OPERATIONS ====================
    
    def add_defect(self, inspection_id: int, defect_category: str,
                  defect_description: str, severity: str = "MAJOR",
                  coordinates: Dict = None) -> int:
        """Add defect detail"""
        coord_json = json.dumps(coordinates) if coordinates else None
        
        self.cursor.execute("""
            INSERT INTO defects (inspection_id, defect_category, 
                               defect_description, severity, coordinates)
            VALUES (?, ?, ?, ?, ?)
        """, (inspection_id, defect_category, defect_description, 
              severity, coord_json))
        
        self.conn.commit()
        return self.cursor.lastrowid
    
    def get_defects(self, inspection_id: int) -> List[Dict]:
        """Get all defects for an inspection"""
        self.cursor.execute("""
            SELECT * FROM defects WHERE inspection_id = ?
        """, (inspection_id,))
        
        return [dict(row) for row in self.cursor.fetchall()]
    
    # ==================== USER OPERATIONS ====================
    
    def add_user(self, username: str, password_hash: str, 
                role: str = "OPERATOR") -> int:
        """Add new user"""
        self.cursor.execute("""
            INSERT INTO users (username, password_hash, role)
            VALUES (?, ?, ?)
        """, (username, password_hash, role))
        
        self.conn.commit()
        return self.cursor.lastrowid
    
    def get_user(self, username: str) -> Optional[Dict]:
        """Get user by username"""
        self.cursor.execute("""
            SELECT * FROM users WHERE username = ? AND active = 1
        """, (username,))
        
        row = self.cursor.fetchone()
        return dict(row) if row else None
    
    def update_last_login(self, user_id: int):
        """Update user's last login time"""
        self.cursor.execute("""
            UPDATE users SET last_login = ? WHERE user_id = ?
        """, (datetime.now().isoformat(), user_id))
        self.conn.commit()
    
    # ==================== LOGGING ====================
    
    def log(self, level: str, module: str, message: str, details: Dict = None):
        """Add system log entry"""
        details_json = json.dumps(details) if details else None
        
        self.cursor.execute("""
            INSERT INTO system_logs (log_level, module, message, details)
            VALUES (?, ?, ?, ?)
        """, (level, module, message, details_json))
        
        self.conn.commit()
    
    def get_logs(self, limit: int = 100, level: str = None) -> List[Dict]:
        """Retrieve system logs"""
        query = "SELECT * FROM system_logs"
        params = []
        
        if level:
            query += " WHERE log_level = ?"
            params.append(level)
        
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        self.cursor.execute(query, params)
        return [dict(row) for row in self.cursor.fetchall()]
    
    # ==================== STATISTICS ====================
    
    def get_statistics(self, start_date: str = None, end_date: str = None) -> Dict:
        """Get inspection statistics"""
        query = "SELECT status, COUNT(*) as count FROM inspections WHERE 1=1"
        params = []
        
        if start_date:
            query += " AND timestamp >= ?"
            params.append(start_date)
        
        if end_date:
            query += " AND timestamp <= ?"
            params.append(end_date)
        
        query += " GROUP BY status"
        
        self.cursor.execute(query, params)
        stats = {row['status']: row['count'] for row in self.cursor.fetchall()}
        
        # Calculate totals
        total = sum(stats.values())
        ok_count = stats.get('OK', 0)
        nok_count = stats.get('NOK', 0)
        
        return {
            'total_inspections': total,
            'ok_count': ok_count,
            'nok_count': nok_count,
            'pass_rate': (ok_count / total * 100) if total > 0 else 0,
            'by_status': stats
        }
    
    # ==================== UTILITY ====================
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
    
    def backup(self, backup_path: str):
        """Create database backup"""
        import shutil
        shutil.copy2(self.db_path, backup_path)
        self.log('INFO', 'database', f'Backup created: {backup_path}')
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()


# ==================== TEST USAGE ====================

if __name__ == "__main__":
    # Test the database module
    print("Testing QC Database Module...")
    
    # Initialize database
    db = QCDatabase("test_qc.db")
    
    # Add sample product
    product_id = db.add_product(
        product_code="PROD001",
        product_name="Test Widget",
        qr_pattern="QR-.*",
        ocr_expected="LOT2024",
        color_ranges={
            "red": [150, 255, 0, 100, 0, 100],
            "blue": [0, 100, 0, 100, 150, 255]
        }
    )
    print(f"✓ Product added: ID {product_id}")
    
    # Add sample user
    user_id = db.add_user("operator1", "hashed_password", "OPERATOR")
    print(f"✓ User added: ID {user_id}")
    
    # Add sample inspection
    inspection_id = db.add_inspection(
        product_id=product_id,
        qr_data="QR-12345",
        ocr_result="LOT2024",
        color_detected="red",
        status="OK",
        blur_score=0.95,
        brightness_score=0.88,
        operator_id=user_id,
        station_id="STATION-01",
        processing_time=1.23
    )
    print(f"✓ Inspection added: ID {inspection_id}")
    
    # Add defect (for testing)
    defect_id = db.add_defect(
        inspection_id=inspection_id,
        defect_category="COLOR",
        defect_description="Color mismatch in zone A",
        severity="MINOR",
        coordinates={"x": 100, "y": 150, "width": 50, "height": 50}
    )
    print(f"✓ Defect added: ID {defect_id}")
    
    # Get statistics
    stats = db.get_statistics()
    print(f"✓ Statistics: {stats}")
    
    # Log test
    db.log("INFO", "test", "Database test completed successfully")
    
    print("\n✓ All tests passed! Database is ready.")
    
    db.close()