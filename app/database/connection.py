import os
import pymysql
from pymysql.cursors import DictCursor
import time
from urllib.parse import urlparse

import os
import pymysql
from pymysql.cursors import DictCursor
import sqlite3
import time
from urllib.parse import urlparse
import re

# In-instance SQLite path for zero-setup cloud hosting
SQLITE_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'expense_tracker.db')

class SQLiteDictCursor:
    """Wrapper around sqlite3 cursor to provide MySQL-compatible syntax & dictionary returns"""
    def __init__(self, cursor):
        self.cursor = cursor
        self.lastrowid = None

    def execute(self, query, params=None):
        # Convert MySQL syntax to SQLite syntax
        q = query
        # Replace MySQL %s placeholders with SQLite ? placeholders
        # Watch out for literal %%Y, %%m in DATE_FORMAT
        q = q.replace("%%Y", "%Y").replace("%%m", "%m").replace("%%b", "%b").replace("%%d", "%d")
        
        # MySQL functions to SQLite functions
        # DATE_FORMAT(col, '%Y-%m-%d') -> strftime('%Y-%m-%d', col)
        q = re.sub(r"DATE_FORMAT\(([^,]+),\s*'([^']+)'\)", r"strftime('\2', \1)", q, flags=re.IGNORECASE)
        # MONTH(col) -> CAST(strftime('%m', col) AS INTEGER)
        q = re.sub(r"MONTH\(([^)]+)\)", r"CAST(strftime('%m', \1) AS INTEGER)", q, flags=re.IGNORECASE)
        # YEAR(col) -> CAST(strftime('%Y', col) AS INTEGER)
        q = re.sub(r"YEAR\(([^)]+)\)", r"CAST(strftime('%Y', \1) AS INTEGER)", q, flags=re.IGNORECASE)
        # DATE_SUB(CURRENT_DATE(), INTERVAL 6 MONTH) -> date('now', '-6 months')
        q = re.sub(r"DATE_SUB\(CURRENT_DATE\(\),\s*INTERVAL\s*6\s*MONTH\)", r"date('now', '-6 months')", q, flags=re.IGNORECASE)
        # ON DUPLICATE KEY UPDATE -> handled or standard upsert
        if "ON DUPLICATE KEY UPDATE" in q.upper():
            # For settings or budgets: INSERT OR REPLACE INTO ...
            q = re.sub(r"INSERT\s+INTO", "INSERT OR REPLACE INTO", q, flags=re.IGNORECASE)
            q = re.sub(r"ON\s+DUPLICATE\s+KEY\s+UPDATE.*$", "", q, flags=re.IGNORECASE)

        # Replace MySQL %s with ?
        q = q.replace("%s", "?")

        # Execute
        if params is not None:
            if isinstance(params, (list, tuple)):
                res = self.cursor.execute(q, tuple(params))
            else:
                res = self.cursor.execute(q, (params,))
        else:
            res = self.cursor.execute(q)

        self.lastrowid = self.cursor.lastrowid
        return res

    def fetchone(self):
        row = self.cursor.fetchone()
        if row is None:
            return None
        return dict(row)

    def fetchall(self):
        rows = self.cursor.fetchall()
        return [dict(r) for r in rows]

    def close(self):
        self.cursor.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

class SQLiteConnectionWrapper:
    """Wrapper that matches PyMySQL connection interface"""
    def __init__(self, conn):
        self.conn = conn

    def cursor(self):
        c = self.conn.cursor()
        return SQLiteDictCursor(c)

    def close(self):
        try:
            self.conn.commit()
            self.conn.close()
        except Exception:
            pass

def is_mysql_configured():
    """Checks whether real MySQL credentials or DATABASE_URL are provided"""
    db_url = os.getenv('DATABASE_URL') or os.getenv('MYSQL_URL') or ''
    # If it is the default template placeholder, ignore it
    if "user:pass@host" in db_url:
        return False
    if db_url and (db_url.startswith("mysql://") or db_url.startswith("mysql2://")):
        return True
    
    host = os.getenv('DB_HOST')
    if host and host not in ('localhost', '127.0.0.1') and os.getenv('DB_PASSWORD'):
        return True
    return False

def get_db_connection(config=None):
    """
    Returns MySQL connection if configured.
    Otherwise automatically falls back to self-contained in-instance storage!
    """
    if is_mysql_configured():
        try:
            host, port, user, password, database, ssl_config = get_connection_params(config)
            kwargs = {
                'host': host,
                'port': port,
                'user': user,
                'password': password,
                'database': database,
                'cursorclass': DictCursor,
                'autocommit': True,
                'charset': 'utf8mb4'
            }
            if ssl_config:
                kwargs.update(ssl_config)
            return pymysql.connect(**kwargs)
        except Exception as e:
            print(f"[Database] Could not connect to MySQL ({e}). Using in-instance storage fallback.")

    # Self-contained SQLite fallback in the instance
    conn = sqlite3.connect(SQLITE_DB_PATH, timeout=20)
    conn.row_factory = sqlite3.Row
    conn.isolation_level = None # autocommit
    return SQLiteConnectionWrapper(conn)

def safe_int_port(port_val, default=3306):
    """Safely converts port value to int, handling empty strings or invalid values."""
    if port_val is None:
        return default
    try:
        val_str = str(port_val).strip()
        return int(val_str) if val_str.isdigit() else default
    except (ValueError, TypeError):
        return default

def parse_db_url():
    """
    Parses DATABASE_URL (or MYSQL_URL) if provided by cloud providers like Render.
    """
    db_url = os.getenv('DATABASE_URL') or os.getenv('MYSQL_URL')
    if not db_url or "user:pass@host" in db_url:
        return None

    db_url = db_url.strip()
    if not (db_url.startswith("mysql://") or db_url.startswith("mysql2://")):
        return None

    cleaned_url = re.sub(r':port(?=[/?#]|$)', ':3306', db_url, flags=re.IGNORECASE)

    try:
        parsed = urlparse(cleaned_url)
        netloc = parsed.netloc
        host = parsed.hostname or 'localhost'
        port = 3306

        if '@' in netloc:
            host_port_part = netloc.split('@', 1)[1]
        else:
            host_port_part = netloc

        if ':' in host_port_part:
            raw_p = host_port_part.split(':', 1)[1]
            raw_p = re.split(r'[/\\?#]', raw_p)[0]
            port = safe_int_port(raw_p, 3306)

        return {
            'host': host,
            'port': port,
            'user': parsed.username or 'root',
            'password': parsed.password or '',
            'database': parsed.path.lstrip('/') if parsed.path else 'expense_tracker'
        }
    except Exception:
        return None

def get_connection_params(config=None):
    parsed = parse_db_url()
    if parsed:
        host = parsed['host']
        port = safe_int_port(parsed['port'], 3306)
        user = parsed['user']
        password = parsed['password']
        database = parsed['database']
    else:
        host = os.getenv('DB_HOST', 'localhost')
        raw_port = os.getenv('DB_PORT') or 3306
        port = safe_int_port(raw_port, 3306)
        user = os.getenv('DB_USER', 'expense_user')
        password = os.getenv('DB_PASSWORD', 'expense_password')
        database = os.getenv('DB_NAME', 'expense_tracker')

    if config:
        host = config.get('DB_HOST', host)
        port = safe_int_port(config.get('DB_PORT', port), 3306)
        user = config.get('DB_USER', user)
        password = config.get('DB_PASSWORD', password)
        database = config.get('DB_NAME', database)

    ssl_config = None
    use_ssl = os.getenv('DB_SSL', 'false').lower() in ('true', '1', 'yes') or 'tidbcloud' in str(host).lower() or 'aiven' in str(host).lower()
    if use_ssl:
        ssl_config = {'ssl': {}}

    return host, port, user, password, database, ssl_config

def init_db(schema_path=None):
    """
    Initializes database tables automatically on startup.
    Supports both MySQL and in-instance storage fallback.
    """
    if is_mysql_configured():
        try:
            host, port, user, password, database, ssl_config = get_connection_params()
            kwargs = {
                'host': host,
                'port': port,
                'user': user,
                'password': password,
                'cursorclass': DictCursor,
                'autocommit': True,
                'charset': 'utf8mb4'
            }
            if ssl_config:
                kwargs.update(ssl_config)
            conn = pymysql.connect(**kwargs)
            with conn.cursor() as cursor:
                base_dir = os.path.dirname(os.path.abspath(__file__))
                schema_path = os.path.join(base_dir, 'schema.sql')
                with open(schema_path, 'r', encoding='utf-8') as f:
                    sql_content = f.read()
                for stmt in [s.strip() for s in sql_content.split(';') if s.strip()]:
                    cursor.execute(stmt)
            conn.close()
            print("[Database] MySQL Schema initialized.")
            return
        except Exception as e:
            print(f"[Database] MySQL auto-init deferred: {e}")

    # Initialize in-instance SQLite tables
    conn = sqlite3.connect(SQLITE_DB_PATH)
    with conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                id INTEGER PRIMARY KEY,
                display_name TEXT NOT NULL DEFAULT 'My Account',
                currency TEXT NOT NULL DEFAULT '₹',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                type TEXT NOT NULL,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                transaction_date TEXT NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS budgets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                monthly_limit REAL NOT NULL,
                month INTEGER NOT NULL,
                year INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(category, month, year)
            )
        """)
        conn.execute("""
            INSERT OR IGNORE INTO settings (id, display_name, currency) VALUES (1, 'My Account', '₹')
        """)
    conn.close()
    print("[Database] In-instance storage initialized successfully.")

