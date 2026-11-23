import os
import pymysql
from pymysql.cursors import DictCursor
import time
from urllib.parse import urlparse

def parse_db_url():
    """
    Parses DATABASE_URL (or MYSQL_URL) if provided by cloud providers like Render,
    TiDB Cloud, Aiven, or Railway.
    Format: mysql://user:password@host:port/database?ssl=...
    """
    db_url = os.getenv('DATABASE_URL') or os.getenv('MYSQL_URL')
    if not db_url:
        return None

    # Handle standard url schemes
    if db_url.startswith("mysql://") or db_url.startswith("mysql2://"):
        parsed = urlparse(db_url)
        return {
            'host': parsed.hostname,
            'port': parsed.port or 3306,
            'user': parsed.username,
            'password': parsed.password or '',
            'database': parsed.path.lstrip('/')
        }
    return None

def get_connection_params(config=None):
    parsed = parse_db_url()
    if parsed:
        host = parsed['host']
        port = parsed['port']
        user = parsed['user']
        password = parsed['password']
        database = parsed['database']
    else:
        host = os.getenv('DB_HOST', 'localhost')
        port = int(os.getenv('DB_PORT', 3306))
        user = os.getenv('DB_USER', 'expense_user')
        password = os.getenv('DB_PASSWORD', 'expense_password')
        database = os.getenv('DB_NAME', 'expense_tracker')

    if config:
        host = config.get('DB_HOST', host)
        port = config.get('DB_PORT', port)
        user = config.get('DB_USER', user)
        password = config.get('DB_PASSWORD', password)
        database = config.get('DB_NAME', database)

    # SSL configuration for managed cloud databases (TiDB, Aiven, PlanetScale, Render)
    ssl_config = None
    use_ssl = os.getenv('DB_SSL', 'false').lower() in ('true', '1', 'yes') or 'tidbcloud' in host.lower() or 'aiven' in host.lower()
    if use_ssl:
        ssl_config = {'ssl': {}}

    return host, port, user, password, database, ssl_config

def get_db_connection(config=None):
    """
    Returns a live connection to MySQL with retry logic.
    Supports both discrete environment variables and DATABASE_URL.
    """
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

def init_db(schema_path=None):
    """
    Initializes database schema and default tables using schema.sql
    Handles creation and default seed safely.
    """
    if not schema_path:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        schema_path = os.path.join(base_dir, 'schema.sql')

    if not os.path.exists(schema_path):
        return

    host, port, user, password, database, ssl_config = get_connection_params()

    last_err = None
    for attempt in range(10):
        try:
            # Connect directly to database
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
                cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{database}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
                cursor.execute(f"USE `{database}`;")
                
                with open(schema_path, 'r', encoding='utf-8') as f:
                    sql_content = f.read()

                statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
                for stmt in statements:
                    cursor.execute(stmt)
            conn.close()
            print("[Database] Schema initialized successfully.")
            return
        except Exception as e:
            # If database already specified in connection (e.g., managed cloud where CREATE DATABASE is restricted)
            try:
                conn = get_db_connection()
                with conn.cursor() as cursor:
                    with open(schema_path, 'r', encoding='utf-8') as f:
                        sql_content = f.read()
                    statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
                    for stmt in statements:
                        if stmt.upper().startswith("CREATE DATABASE") or stmt.upper().startswith("USE "):
                            continue
                        cursor.execute(stmt)
                conn.close()
                print("[Database] Schema initialized in existing database successfully.")
                return
            except Exception as e2:
                last_err = e2
            time.sleep(1)

    print(f"[Database] Warning: Could not initialize database immediately: {last_err}")
