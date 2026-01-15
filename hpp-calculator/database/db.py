import sqlite3
import os
from contextlib import contextmanager

DATABASE_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'hpp_calculator.db')


def ensure_data_dir():
    """Ensure the data directory exists."""
    data_dir = os.path.dirname(DATABASE_PATH)
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)


@contextmanager
def get_connection():
    """Get database connection as context manager."""
    ensure_data_dir()
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def init_db():
    """Initialize database tables."""
    ensure_data_dir()
    with get_connection() as conn:
        cursor = conn.cursor()

        # Calculations table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS calculations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                total_batch_cost REAL NOT NULL,
                output_units INTEGER NOT NULL,
                target_margin_percent REAL NOT NULL,
                hpp_per_unit REAL NOT NULL,
                suggested_selling_price REAL NOT NULL,
                actual_selling_price REAL,
                actual_margin_percent REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Ingredients table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ingredients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                calculation_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                quantity REAL NOT NULL,
                unit TEXT NOT NULL,
                price_per_unit REAL NOT NULL,
                line_cost REAL NOT NULL,
                contribution_percent REAL NOT NULL,
                FOREIGN KEY (calculation_id) REFERENCES calculations (id) ON DELETE CASCADE
            )
        ''')

        # Templates table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                ingredients_json TEXT NOT NULL,
                output_units INTEGER DEFAULT 1,
                target_margin_percent REAL DEFAULT 40,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Settings table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT UNIQUE NOT NULL,
                value TEXT NOT NULL
            )
        ''')

        # Insert default settings
        default_settings = [
            ('currency_symbol', 'Rp'),
            ('default_margin', '40'),
            ('decimal_places', '0'),
            ('theme', 'light')
        ]

        for key, value in default_settings:
            cursor.execute('''
                INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)
            ''', (key, value))

        conn.commit()

    return True


def get_setting(key: str, default: str = None) -> str:
    """Get a setting value by key."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT value FROM settings WHERE key = ?', (key,))
        row = cursor.fetchone()
        return row['value'] if row else default


def set_setting(key: str, value: str):
    """Set a setting value."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)
        ''', (key, value))
        conn.commit()


# ==========================================
# Product Template Functions (Save/Load)
# ==========================================

def save_product_template(name: str, mode: str, data_json: str, output_units: int = 1, target_margin: float = 40) -> int:
    """
    Save a product template for reuse.
    
    Args:
        name: Template name (e.g., "Nasi Goreng Spesial")
        mode: Calculator mode ("produksi", "distributor", "service")
        data_json: JSON string of the product data (ingredients/products/services)
        output_units: Number of output units
        target_margin: Target margin percentage
        
    Returns:
        ID of the saved template
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # Update templates table to include mode if not exists
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS product_templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                mode TEXT NOT NULL DEFAULT 'produksi',
                data_json TEXT NOT NULL,
                output_units INTEGER DEFAULT 1,
                target_margin_percent REAL DEFAULT 40,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            INSERT INTO product_templates (name, mode, data_json, output_units, target_margin_percent)
            VALUES (?, ?, ?, ?, ?)
        ''', (name, mode, data_json, output_units, target_margin))
        
        conn.commit()
        return cursor.lastrowid


def get_product_templates(mode: str = None) -> list:
    """
    Get all product templates, optionally filtered by mode.
    
    Args:
        mode: Filter by mode ("produksi", "distributor", "service") or None for all
        
    Returns:
        List of template dictionaries
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # Check if table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='product_templates'")
        if not cursor.fetchone():
            return []
        
        if mode:
            cursor.execute('''
                SELECT id, name, mode, data_json, output_units, target_margin_percent, created_at
                FROM product_templates WHERE mode = ? ORDER BY updated_at DESC
            ''', (mode,))
        else:
            cursor.execute('''
                SELECT id, name, mode, data_json, output_units, target_margin_percent, created_at
                FROM product_templates ORDER BY updated_at DESC
            ''')
        
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def get_product_template_by_id(template_id: int) -> dict:
    """Get a specific template by ID."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, name, mode, data_json, output_units, target_margin_percent, created_at
            FROM product_templates WHERE id = ?
        ''', (template_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


def delete_product_template(template_id: int) -> bool:
    """Delete a product template by ID."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM product_templates WHERE id = ?', (template_id,))
        conn.commit()
        return cursor.rowcount > 0


def update_product_template(template_id: int, name: str = None, data_json: str = None) -> bool:
    """Update an existing product template."""
    with get_connection() as conn:
        cursor = conn.cursor()
        
        updates = []
        params = []
        
        if name:
            updates.append("name = ?")
            params.append(name)
        if data_json:
            updates.append("data_json = ?")
            params.append(data_json)
        
        if not updates:
            return False
            
        updates.append("updated_at = CURRENT_TIMESTAMP")
        params.append(template_id)
        
        cursor.execute(f'''
            UPDATE product_templates SET {", ".join(updates)} WHERE id = ?
        ''', params)
        
        conn.commit()
        return cursor.rowcount > 0


# ==========================================
# Calculation History Functions
# ==========================================

def save_calculation_history(
    name: str,
    mode: str,
    hpp_per_unit: float,
    suggested_price: float,
    total_cost: float,
    output_units: int,
    margin_percent: float,
    data_json: str
) -> int:
    """
    Save a calculation to history for trend analysis.
    
    Returns:
        ID of the saved calculation
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # Create history table if not exists
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS calculation_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                mode TEXT NOT NULL,
                hpp_per_unit REAL NOT NULL,
                suggested_price REAL NOT NULL,
                total_cost REAL NOT NULL,
                output_units INTEGER NOT NULL,
                margin_percent REAL NOT NULL,
                data_json TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            INSERT INTO calculation_history 
            (name, mode, hpp_per_unit, suggested_price, total_cost, output_units, margin_percent, data_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (name, mode, hpp_per_unit, suggested_price, total_cost, output_units, margin_percent, data_json))
        
        conn.commit()
        return cursor.lastrowid


def get_calculation_history(mode: str = None, limit: int = 50) -> list:
    """
    Get calculation history, optionally filtered by mode.
    
    Args:
        mode: Filter by mode or None for all
        limit: Maximum number of records to return
        
    Returns:
        List of calculation history records
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # Check if table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='calculation_history'")
        if not cursor.fetchone():
            return []
        
        if mode:
            cursor.execute('''
                SELECT id, name, mode, hpp_per_unit, suggested_price, total_cost, 
                       output_units, margin_percent, created_at
                FROM calculation_history 
                WHERE mode = ? 
                ORDER BY created_at DESC 
                LIMIT ?
            ''', (mode, limit))
        else:
            cursor.execute('''
                SELECT id, name, mode, hpp_per_unit, suggested_price, total_cost, 
                       output_units, margin_percent, created_at
                FROM calculation_history 
                ORDER BY created_at DESC 
                LIMIT ?
            ''', (limit,))
        
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def get_hpp_trend(product_name: str, days: int = 30) -> list:
    """
    Get HPP trend for a specific product over time.
    
    Args:
        product_name: Name of the product
        days: Number of days to look back
        
    Returns:
        List of (date, hpp_per_unit) tuples
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='calculation_history'")
        if not cursor.fetchone():
            return []
        
        cursor.execute('''
            SELECT date(created_at) as calc_date, hpp_per_unit
            FROM calculation_history
            WHERE name = ? AND created_at >= datetime('now', ?)
            ORDER BY created_at ASC
        ''', (product_name, f'-{days} days'))
        
        return [(row['calc_date'], row['hpp_per_unit']) for row in cursor.fetchall()]


def get_unique_product_names() -> list:
    """Get list of unique product names from history."""
    with get_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='calculation_history'")
        if not cursor.fetchone():
            return []
        
        cursor.execute('SELECT DISTINCT name FROM calculation_history ORDER BY name')
        return [row['name'] for row in cursor.fetchall()]

