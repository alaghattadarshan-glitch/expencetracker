from flask import Blueprint, request, jsonify
from app.database.connection import get_db_connection
from datetime import datetime, timedelta

settings_bp = Blueprint('settings', __name__, url_prefix='/api/settings')

@settings_bp.route('', methods=['GET'])
def get_settings():
    """Retrieve user settings and preferences"""
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, display_name, currency FROM settings WHERE id = 1")
            settings = cursor.fetchone()
            if not settings:
                settings = {'id': 1, 'display_name': 'User', 'currency': '₹'}
        conn.close()
        return jsonify(settings), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@settings_bp.route('', methods=['PUT'])
def update_settings():
    """Update user settings"""
    try:
        data = request.get_json() or {}
        display_name = data.get('display_name', 'User').strip()
        currency = data.get('currency', '₹').strip()

        if not display_name:
            return jsonify({'error': 'Display name cannot be empty'}), 400

        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO settings (id, display_name, currency)
                VALUES (1, %s, %s)
                ON DUPLICATE KEY UPDATE display_name = VALUES(display_name), currency = VALUES(currency)
            """, (display_name, currency))
        conn.close()

        return jsonify({'message': 'Settings updated successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@settings_bp.route('/clear-data', methods=['POST'])
def clear_all_data():
    """
    Clears all user transactions and budgets for a completely fresh start.
    """
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("TRUNCATE TABLE transactions")
            cursor.execute("TRUNCATE TABLE budgets")
        conn.close()
        return jsonify({'message': 'All financial data has been cleared.'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

