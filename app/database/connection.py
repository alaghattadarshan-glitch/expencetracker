import os
import pymysql
from pymysql.cursors import DictCursor
import time

def get_db_connection(config=None):
    """
    Returns a live connection to MySQL with retry logic.
    Yields DictCursor by default for convenient dictionary result sets.
    """
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

    return pymysql.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        database=database,
        cursorclass=DictCursor,
        autocommit=True,
        charset='utf8mb4'
    )

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

    # First connect without selecting database to ensure database exists
    host = os.getenv('DB_HOST', 'localhost')
    port = int(os.getenv('DB_PORT', 3306))
    user = os.getenv('DB_USER', 'expense_user')
    password = os.getenv('DB_PASSWORD', 'expense_password')
    database = os.getenv('DB_NAME', 'expense_tracker')

    # Allow up to 10 retries if MySQL container is initializing
    last_err = None
    for attempt in range(10):
        try:
            conn = pymysql.connect(
                host=host,
                port=port,
                user=user,
                password=password,
                cursorclass=DictCursor,
                autocommit=True
            )
            with conn.cursor() as cursor:
                cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{database}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
                cursor.execute(f"USE `{database}`;")
                
                with open(schema_path, 'r', encoding='utf-8') as f:
                    sql_content = f.read()

                # Execute statement by statement
                statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
                for stmt in statements:
                    cursor.execute(stmt)
            conn.close()
            print("[Database] Schema initialized successfully.")
            return
        except Exception as e:
            last_err = e
            time.sleep(1)

    print(f"[Database] Warning: Could not initialize database immediately: {last_err}")
