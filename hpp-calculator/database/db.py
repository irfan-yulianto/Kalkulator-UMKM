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
